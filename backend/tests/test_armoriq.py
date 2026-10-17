"""Unit and Integration Tests for ArmorIQ Integration, RBAC, and Interceptor.

Tests Phase 5 (ArmorIQ Client & Interceptor) and Phase 6 (RBAC & Fail-Secure).
"""

import pytest
from app.armoriq.client import ArmorIQClient, AuthorizationDecision
from app.armoriq.interceptor import AuthorizationInterceptor, ROLE_PERMISSIONS
from app.sandboxes import FileVaultSandbox, CRMSandbox, EmailSandbox
from app.mcp import SandboxToolAdapter
from app.core.telemetry import (
    GauntletEvent,
    ExecutionPath,
    AuthorizationStatus,
    ToolExecutionStatus,
    EventType,
)
from app.config import settings


@pytest.fixture
def sandbox_adapter():
    vault = FileVaultSandbox(settings.file_vault_dir)
    crm = CRMSandbox(settings.crm_data_path)
    crm.reload_from_fixture()
    email = EmailSandbox(settings.email_outbox_path)
    return SandboxToolAdapter(vault=vault, crm=crm, email=email)


@pytest.mark.asyncio
async def test_armoriq_client_fail_secure_unconfigured():
    """Unconfigured client must return AUTHENTICATION_FAILED, not fabricate success."""
    client = ArmorIQClient(api_key="")
    result = await client.check_authorization(
        agent_role="Researcher",
        tool_name="file_vault.read",
        action="read",
    )
    assert result.decision == AuthorizationDecision.AUTHENTICATION_FAILED
    assert "not configured" in result.reason.lower()
    assert result.is_live is False


@pytest.mark.asyncio
async def test_armoriq_client_fail_secure_timeout():
    """Simulated or actual timeout must return AUTHORIZATION_TIMEOUT."""
    client = ArmorIQClient(api_key="valid_key", simulate_timeout=True)
    result = await client.check_authorization(
        agent_role="Publisher",
        tool_name="email.send",
        action="send",
    )
    assert result.decision == AuthorizationDecision.AUTHORIZATION_TIMEOUT
    assert "unreachable" in result.reason.lower()


def test_rbac_matrix_integrity():
    """Verify role permissions conform to Section 7 specs."""
    assert "file_vault.read" in ROLE_PERMISSIONS["Orchestrator"]["forbidden_tools"]
    assert "email.send" in ROLE_PERMISSIONS["Researcher"]["forbidden_tools"]
    assert "crm.update_record" in ROLE_PERMISSIONS["Researcher"]["forbidden_tools"]
    assert "file_vault.read" in ROLE_PERMISSIONS["Publisher"]["forbidden_tools"]


@pytest.mark.asyncio
async def test_interceptor_blocks_forbidden_tool_locally(sandbox_adapter):
    """Researcher attempting CRM update must be stopped at the boundary."""
    client = ArmorIQClient(api_key="")
    interceptor = AuthorizationInterceptor(tool_adapter=sandbox_adapter, armoriq_client=client)

    events = []
    result = await interceptor.execute_with_authorization(
        run_id="test_run_01",
        agent_role="Researcher",
        tool_name="crm.update_record",
        arguments={"account_id": "account-4471", "updates": {"stage": "Closed"}},
        on_event=lambda e: events.append(e),
    )

    assert result["blocked"] is True
    assert result["authorization_status"] == AuthorizationStatus.POLICY_DENIED
    assert any(e.event_type == EventType.AUTHORIZATION_RESULT for e in events)
    assert any(e.event_type == EventType.TOOL_EXECUTION_BLOCKED for e in events)


@pytest.mark.asyncio
async def test_interceptor_blocks_classified_vault_access(sandbox_adapter):
    """Researcher attempting to read classified vault secret must be blocked."""
    client = ArmorIQClient(api_key="")
    interceptor = AuthorizationInterceptor(tool_adapter=sandbox_adapter, armoriq_client=client)

    result = await interceptor.execute_with_authorization(
        run_id="test_run_02",
        agent_role="Researcher",
        tool_name="file_vault.read",
        arguments={"path": "classified/gauntlet-secret.txt"},
    )

    assert result["blocked"] is True
    assert result["authorization_status"] == AuthorizationStatus.POLICY_DENIED
    assert "classified" in result["reason"].lower()


@pytest.mark.asyncio
async def test_interceptor_permits_benign_public_read(sandbox_adapter):
    """Researcher reading public brief is permitted by local RBAC."""
    client = ArmorIQClient(api_key="")  # Unconfigured fallback allows local RBAC check
    interceptor = AuthorizationInterceptor(tool_adapter=sandbox_adapter, armoriq_client=client)

    result = await interceptor.execute_with_authorization(
        run_id="test_run_03",
        agent_role="Researcher",
        tool_name="file_vault.read",
        arguments={"path": "public/briefs/q3-market-brief.txt"},
    )

    assert result["blocked"] is False
    assert result["authorization_status"] == AuthorizationStatus.AUTHORIZED
    assert result["success"] is True
    assert "public" in result["tool_result"]["content"].lower()
