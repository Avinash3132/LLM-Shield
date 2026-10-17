"""Runtime Authorization Interceptor for Path B (Protected Agent).

Every protected outbound tool execution MUST pass through this interceptor.
There is no alternate route that allows the protected agent to invoke
sandbox tools directly. Enforces mandatory interception per Section 6.2.
"""

from typing import Dict, Any, Optional, Callable, List
from ..core.telemetry import (
    GauntletEvent,
    EventType,
    ExecutionPath,
    AuthorizationStatus,
    ToolExecutionStatus,
    Severity,
)
from ..mcp.adapter import SandboxToolAdapter
from .client import ArmorIQClient, AuthorizationDecision, AuthorizationResult

# Phase 6: Role-Based Access Control lookup
ROLE_PERMISSIONS: Dict[str, Dict[str, List[str]]] = {
    "Orchestrator": {
        "allowed_tools": [],
        "forbidden_tools": ["file_vault.read", "file_vault.list", "crm.update_record", "email.send"],
    },
    "Researcher": {
        "allowed_tools": ["file_vault.read", "file_vault.list", "crm.get_record", "crm.list_records"],
        "forbidden_tools": ["crm.update_record", "email.send"],
    },
    "Writer": {
        "allowed_tools": [],
        "forbidden_tools": ["file_vault.read", "file_vault.list", "email.send"],
    },
    "Publisher": {
        "allowed_tools": ["crm.update_record", "crm.get_record", "email.send"],
        "forbidden_tools": ["file_vault.read"],
    },
}

CLASSIFIED_PATH_PREFIXES = ["classified/", "classified\\", "vault://classified", "vault:/classified"]


def _normalize_tool_name(name: str) -> str:
    """Normalize tool names with dots or underscores to underscore format.
    E.g. 'crm.update_record' -> 'crm_update_record'
    'crm_update_record' -> 'crm_update_record'
    'file_vault.read' -> 'file_vault_read'
    """
    return name.lower().replace(".", "_")


def _is_classified_path(arguments: Dict[str, Any]) -> bool:
    """Check if tool arguments reference classified vault paths."""
    path_val = str(arguments.get("path", "")).lower()
    return any(prefix in path_val for prefix in CLASSIFIED_PATH_PREFIXES)


class AuthorizationInterceptor:
    """Mandatory authorization interceptor for Path B (Protected Agent).

    Enforces:
    1. Agent identity verification
    2. Tool and operation identification
    3. Request schema validation (handled upstream by SandboxToolAdapter)
    4. Role-based local policy check
    5. ArmorIQ remote authorization workflow
    6. Execution only after valid authorization
    7. Blocking of denied or invalid requests
    8. Separate recording of authorization and execution outcomes
    """

    def __init__(
        self,
        tool_adapter: SandboxToolAdapter,
        armoriq_client: ArmorIQClient,
    ):
        self.tool_adapter = tool_adapter
        self.armoriq_client = armoriq_client

    def _local_rbac_check(
        self,
        agent_role: str,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Optional[str]:
        """Defense-in-depth local RBAC check. Returns denial reason or None if allowed."""
        normalized_role = agent_role.replace(" agent", "").replace(" Agent", "").strip()
        role_config = ROLE_PERMISSIONS.get(normalized_role)

        if not role_config:
            return f"Unknown role '{normalized_role}' has no defined permissions."

        tool_norm = _normalize_tool_name(tool_name)
        forbidden_norm = [_normalize_tool_name(t) for t in role_config["forbidden_tools"]]

        if tool_norm in forbidden_norm:
            return f"Role '{normalized_role}' is forbidden from using tool '{tool_name}'."

        # Classified path restriction: deny all agents except Publisher from classified vault
        if "file_vault" in tool_norm and _is_classified_path(arguments):
            if normalized_role != "Publisher":
                return f"Role '{normalized_role}' cannot access classified vault paths."

        return None

    async def execute_with_authorization(
        self,
        run_id: str,
        agent_role: str,
        tool_name: str,
        arguments: Dict[str, Any],
        on_event: Optional[Callable[[GauntletEvent], None]] = None,
    ) -> Dict[str, Any]:
        """Execute a tool call through the full authorization pipeline."""
        events: List[GauntletEvent] = []

        def emit(event: GauntletEvent) -> None:
            events.append(event)
            if on_event:
                try:
                    on_event(event)
                except Exception:
                    pass

        requested_action = f"{tool_name}({', '.join(f'{k}={v}' for k, v in arguments.items())})"

        # Step 1: Emit AUTHORIZATION_REQUESTED
        emit(GauntletEvent(
            run_id=run_id,
            execution_path=ExecutionPath.PROTECTED,
            target_agent="Interceptor",
            event_type=EventType.AUTHORIZATION_REQUESTED,
            tool_name=tool_name,
            requested_action=requested_action,
            authorization_status=AuthorizationStatus.NOT_APPLICABLE,
            tool_execution_status=ToolExecutionStatus.PROPOSED,
            severity=Severity.INFO,
            summary=f"Authorization requested for {agent_role} -> {tool_name}.",
        ))

        # Step 2: Local RBAC defense-in-depth check
        local_denial = self._local_rbac_check(agent_role, tool_name, arguments)
        if local_denial:
            policy_id = f"pol_rbac_{agent_role.lower()}_{_normalize_tool_name(tool_name)}"
            emit(GauntletEvent(
                run_id=run_id,
                execution_path=ExecutionPath.PROTECTED,
                target_agent="Interceptor",
                event_type=EventType.AUTHORIZATION_RESULT,
                tool_name=tool_name,
                requested_action=requested_action,
                authorization_status=AuthorizationStatus.POLICY_DENIED,
                policy_id=policy_id,
                tool_execution_status=ToolExecutionStatus.BLOCKED,
                severity=Severity.DANGER,
                summary=f"Policy denied: {local_denial}",
            ))
            emit(GauntletEvent(
                run_id=run_id,
                execution_path=ExecutionPath.PROTECTED,
                target_agent="Interceptor",
                event_type=EventType.TOOL_EXECUTION_BLOCKED,
                tool_name=tool_name,
                requested_action=requested_action,
                authorization_status=AuthorizationStatus.POLICY_DENIED,
                policy_id=policy_id,
                tool_execution_status=ToolExecutionStatus.BLOCKED,
                remediation_action="Return denial to the agent and continue without execution.",
                severity=Severity.DANGER,
                summary=f"Interceptor blocked: {tool_name} was never invoked.",
            ))
            return {
                "success": False,
                "blocked": True,
                "authorization_status": AuthorizationStatus.POLICY_DENIED,
                "policy_id": policy_id,
                "reason": local_denial,
                "events": events,
            }

        # Step 3: Remote ArmorIQ authorization (if configured)
        armoriq_result: Optional[AuthorizationResult] = None
        if self.armoriq_client.is_configured or self.armoriq_client.simulate_timeout:
            armoriq_result = await self.armoriq_client.check_authorization(
                agent_role=agent_role,
                tool_name=tool_name,
                action=requested_action,
                context=arguments,
            )

            auth_status_map = {
                AuthorizationDecision.AUTHORIZED: AuthorizationStatus.AUTHORIZED,
                AuthorizationDecision.POLICY_DENIED: AuthorizationStatus.POLICY_DENIED,
                AuthorizationDecision.AUTHENTICATION_FAILED: AuthorizationStatus.AUTHENTICATION_FAILED,
                AuthorizationDecision.AUTHORIZATION_ERROR: AuthorizationStatus.AUTHORIZATION_ERROR,
                AuthorizationDecision.AUTHORIZATION_TIMEOUT: AuthorizationStatus.AUTHORIZATION_TIMEOUT,
                AuthorizationDecision.INVALID_REQUEST: AuthorizationStatus.INVALID_REQUEST,
            }

            mapped_status = auth_status_map.get(
                armoriq_result.decision, AuthorizationStatus.AUTHORIZATION_ERROR
            )

            if armoriq_result.decision != AuthorizationDecision.AUTHORIZED:
                emit(GauntletEvent(
                    run_id=run_id,
                    execution_path=ExecutionPath.PROTECTED,
                    target_agent="Interceptor",
                    event_type=EventType.AUTHORIZATION_RESULT,
                    tool_name=tool_name,
                    requested_action=requested_action,
                    authorization_status=mapped_status,
                    policy_id=armoriq_result.policy_id,
                    tool_execution_status=ToolExecutionStatus.BLOCKED,
                    severity=Severity.DANGER,
                    summary=f"ArmorIQ decision: {armoriq_result.decision.value}. {armoriq_result.reason}",
                ))
                emit(GauntletEvent(
                    run_id=run_id,
                    execution_path=ExecutionPath.PROTECTED,
                    target_agent="Interceptor",
                    event_type=EventType.TOOL_EXECUTION_BLOCKED,
                    tool_name=tool_name,
                    requested_action=requested_action,
                    authorization_status=mapped_status,
                    tool_execution_status=ToolExecutionStatus.BLOCKED,
                    remediation_action="Drop payload, record audit event.",
                    severity=Severity.DANGER,
                    summary=f"Tool blocked by ArmorIQ. No execution occurred.",
                ))
                return {
                    "success": False,
                    "blocked": True,
                    "authorization_status": mapped_status,
                    "policy_id": armoriq_result.policy_id,
                    "reason": armoriq_result.reason,
                    "is_live": armoriq_result.is_live,
                    "events": events,
                }

            # ArmorIQ explicitly AUTHORIZED
            emit(GauntletEvent(
                run_id=run_id,
                execution_path=ExecutionPath.PROTECTED,
                target_agent="Interceptor",
                event_type=EventType.AUTHORIZATION_RESULT,
                tool_name=tool_name,
                requested_action=requested_action,
                authorization_status=AuthorizationStatus.AUTHORIZED,
                policy_id=armoriq_result.policy_id,
                tool_execution_status=ToolExecutionStatus.PROPOSED,
                severity=Severity.SUCCESS,
                summary=f"ArmorIQ authorized: {tool_name} for {agent_role}.",
            ))

        # Step 4: If ArmorIQ not configured, local RBAC passed → allow
        if not armoriq_result:
            emit(GauntletEvent(
                run_id=run_id,
                execution_path=ExecutionPath.PROTECTED,
                target_agent="Interceptor",
                event_type=EventType.AUTHORIZATION_RESULT,
                tool_name=tool_name,
                requested_action=requested_action,
                authorization_status=AuthorizationStatus.AUTHORIZED,
                tool_execution_status=ToolExecutionStatus.PROPOSED,
                severity=Severity.SUCCESS,
                summary=f"Local RBAC check passed for {agent_role} -> {tool_name}. ArmorIQ not configured.",
            ))

        # Step 5: Execute tool through SandboxToolAdapter
        emit(GauntletEvent(
            run_id=run_id,
            execution_path=ExecutionPath.PROTECTED,
            target_agent="Interceptor",
            event_type=EventType.TOOL_EXECUTION_STARTED,
            tool_name=tool_name,
            requested_action=requested_action,
            tool_execution_status=ToolExecutionStatus.PROPOSED,
            severity=Severity.INFO,
            summary=f"Authorization verified. Executing {tool_name} in sandbox.",
        ))

        tool_result = self.tool_adapter.execute(tool_name, arguments)

        emit(GauntletEvent(
            run_id=run_id,
            execution_path=ExecutionPath.PROTECTED,
            target_agent="Interceptor",
            event_type=EventType.TOOL_EXECUTION_COMPLETED,
            tool_name=tool_name,
            requested_action=requested_action,
            authorization_status=AuthorizationStatus.AUTHORIZED,
            tool_execution_status=ToolExecutionStatus.EXECUTED,
            severity=Severity.SUCCESS if tool_result.get("success") else Severity.WARNING,
            summary=f"Tool '{tool_name}' executed after authorization.",
        ))

        return {
            "success": tool_result.get("success", False),
            "blocked": False,
            "authorization_status": AuthorizationStatus.AUTHORIZED,
            "tool_result": tool_result,
            "events": events,
        }
