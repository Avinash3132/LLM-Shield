"""Protected Agent Runner for Path B (ArmorIQ-Governed).

Identical agent reasoning loop to Path A, but every tool call is routed
through the AuthorizationInterceptor. There is no bypass path.
"""

from typing import Dict, Any, List, Optional, Callable

try:
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    types = None

from ..core.telemetry import (
    GauntletEvent,
    EventType,
    ExecutionPath,
    ToolExecutionStatus,
    Severity,
)
from ..mcp.adapter import SandboxToolAdapter
from ..armoriq.interceptor import AuthorizationInterceptor
from .gemini_provider import GeminiProvider, ToolCallRequest
from .prompt_builder import build_agent_system_prompt
from .runner import RunResult


class ProtectedAgentRunner:
    """Executes a bounded agent loop for Path B where every tool call
    passes through the AuthorizationInterceptor."""

    def __init__(
        self,
        interceptor: AuthorizationInterceptor,
        provider: GeminiProvider,
        target_agent: str = "Researcher",
        max_turns: int = 5,
    ):
        self.interceptor = interceptor
        self.provider = provider
        self.target_agent = target_agent
        self.max_turns = max_turns

    async def execute_run(
        self,
        run_id: str,
        scenario_id: str,
        scenario_name: str,
        task_prompt: str,
        on_event: Optional[Callable[[GauntletEvent], None]] = None,
    ) -> RunResult:
        events: List[GauntletEvent] = []
        total_attempts = 0
        executed_count = 0
        blocked_count = 0
        policy_violations = 0

        def emit(event: GauntletEvent) -> None:
            events.append(event)
            if on_event:
                try:
                    on_event(event)
                except Exception:
                    pass

        emit(GauntletEvent(
            run_id=run_id,
            execution_path=ExecutionPath.PROTECTED,
            target_agent=self.target_agent,
            event_type=EventType.RUN_STARTED,
            severity=Severity.NEUTRAL,
            summary="Run started. Every tool call routes through the authorization interceptor.",
        ))

        emit(GauntletEvent(
            run_id=run_id,
            execution_path=ExecutionPath.PROTECTED,
            target_agent="Coordinator",
            event_type=EventType.TEST_CASE_LOADED,
            severity=Severity.INFO,
            summary=f"Scenario '{scenario_name}' loaded with equivalent inputs as the baseline path.",
        ))

        sdk_tools = self.provider.build_sdk_tools(self.interceptor.tool_adapter.registry)
        system_prompt = build_agent_system_prompt(self.target_agent)
        contents: List[Any] = [task_prompt]

        final_summary = "Protected agent completed within turn limit."
        run_status = "completed"

        for turn_idx in range(1, self.max_turns + 1):
            try:
                turn_result = await self.provider.generate_turn(
                    contents=contents,
                    system_instruction=system_prompt,
                    tools=sdk_tools,
                )
            except Exception as e:
                emit(GauntletEvent(
                    run_id=run_id,
                    execution_path=ExecutionPath.PROTECTED,
                    target_agent=self.target_agent,
                    event_type=EventType.ERROR,
                    error_type=type(e).__name__,
                    severity=Severity.DANGER,
                    summary=f"Inference error during turn {turn_idx}: {str(e)}",
                ))
                run_status = "failed"
                final_summary = f"Protected agent failed: {str(e)}"
                break

            if turn_result.text:
                emit(GauntletEvent(
                    run_id=run_id,
                    execution_path=ExecutionPath.PROTECTED,
                    target_agent=self.target_agent,
                    event_type=EventType.AGENT_REASONING,
                    severity=Severity.INFO,
                    summary=turn_result.text[:200] + ("..." if len(turn_result.text) > 200 else ""),
                ))

            # Append model turn to conversation history
            if turn_result.raw_content is not None:
                contents.append(turn_result.raw_content)
            elif turn_result.tool_calls:
                if GENAI_AVAILABLE and types:
                    m_parts = []
                    if turn_result.text:
                        m_parts.append(types.Part.from_text(text=turn_result.text))
                    for c in turn_result.tool_calls:
                        m_parts.append(types.Part.from_function_call(
                            name=c.name.replace(".", "_"),
                            args=c.arguments,
                        ))
                    contents.append(types.Content(role="model", parts=m_parts))
                else:
                    contents.append(turn_result.text or "proposing tools")
            elif turn_result.text:
                contents.append(turn_result.text)

            if not turn_result.tool_calls:
                final_summary = "Protected agent completed without further tool requests."
                break

            for call in turn_result.tool_calls:
                total_attempts += 1

                # Emit TOOL_CALL_PROPOSED
                emit(GauntletEvent(
                    run_id=run_id,
                    execution_path=ExecutionPath.PROTECTED,
                    target_agent=self.target_agent,
                    event_type=EventType.TOOL_CALL_PROPOSED,
                    tool_name=call.name,
                    requested_action=f"{call.name}({', '.join(f'{k}={v}' for k, v in call.arguments.items())})",
                    tool_execution_status=ToolExecutionStatus.PROPOSED,
                    severity=Severity.WARNING,
                    summary=f"Model proposes: {call.name}. Proposal is not execution.",
                ))

                # Route THROUGH interceptor — no bypass
                intercept_result = await self.interceptor.execute_with_authorization(
                    run_id=run_id,
                    agent_role=self.target_agent,
                    tool_name=call.name,
                    arguments=call.arguments,
                    on_event=lambda e: emit(e),
                )

                if intercept_result.get("blocked"):
                    blocked_count += 1
                    policy_violations += 1
                    tool_response_text = f"AUTHORIZATION DENIED: {intercept_result.get('reason', 'Blocked by policy')}"
                else:
                    executed_count += 1
                    tool_response_text = str(intercept_result.get("tool_result", {}))

                # Append response to conversation
                if GENAI_AVAILABLE and types:
                    part = types.Part.from_function_response(
                        name=call.name.replace(".", "_"),
                        response={"result": tool_response_text},
                    )
                    contents.append(types.Content(role="user", parts=[part]))
                else:
                    contents.append(f"Tool {call.name} result: {tool_response_text}")

        final_severity = Severity.SUCCESS if blocked_count > 0 and executed_count == 0 else (
            Severity.DANGER if policy_violations > 0 else Severity.SUCCESS
        )
        emit(GauntletEvent(
            run_id=run_id,
            execution_path=ExecutionPath.PROTECTED,
            target_agent="Coordinator",
            event_type=EventType.RUN_COMPLETED,
            severity=final_severity,
            summary=f"Protected run concluded. Blocked: {blocked_count}, Executed: {executed_count}.",
        ))

        return RunResult(
            run_id=run_id,
            scenario_id=scenario_id,
            execution_path=ExecutionPath.PROTECTED,
            status=run_status,
            events=events,
            total_tool_attempts=total_attempts,
            executed_tools=executed_count,
            blocked_tools=blocked_count,
            policy_violations=policy_violations,
            summary=final_summary,
        )
