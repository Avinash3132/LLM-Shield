"""Comprehensive unit tests for MCP tools, schemas, registry, and sandbox tool adapter."""

import pytest
from app.config import settings
from app.sandboxes import FileVaultSandbox, CRMSandbox, EmailSandbox
from app.mcp import SandboxToolAdapter, ToolRegistry


@pytest.fixture
def adapter(tmp_path):
    vault = FileVaultSandbox(settings.file_vault_dir)
    crm = CRMSandbox(settings.crm_data_path)
    crm.reload_from_fixture()
    test_outbox = tmp_path / "mcp_test_outbox.json"
    email = EmailSandbox(test_outbox)
    return SandboxToolAdapter(vault=vault, crm=crm, email=email)


class TestMCPRegistry:
    def test_registered_tools_present(self, adapter):
        tools = adapter.registry.list_tools()
        names = [t.name for t in tools]
        assert "file_vault.read" in names
        assert "file_vault.list" in names
        assert "crm.get_record" in names
        assert "crm.list_records" in names
        assert "crm.update_record" in names
        assert "email.send" in names

    def test_alias_lookup(self, adapter):
        # Primary lookup
        t1 = adapter.registry.get("file_vault.read")
        assert t1 is not None

        # Underscore alias
        t2 = adapter.registry.get("file_vault_read")
        assert t2 is not None
        assert t1.name == t2.name

        # Case insensitive
        t3 = adapter.registry.get("EMAIL.SEND")
        assert t3 is not None
        assert t3.name == "email.send"

    def test_mcp_catalog_format(self, adapter):
        catalog = adapter.registry.to_mcp_catalog()
        assert len(catalog) == 6
        for tool in catalog:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert tool["inputSchema"].get("type") == "object"
            assert "properties" in tool["inputSchema"]

    def test_gemini_declarations_format(self, adapter):
        declarations = adapter.registry.to_gemini_declarations()
        assert len(declarations) == 6
        for decl in declarations:
            assert "name" in decl
            assert "_" in decl["name"] or decl["name"].isalnum()
            assert "description" in decl
            assert "parameters" in decl
            assert decl["parameters"]["type"] == "OBJECT"


class TestSandboxToolAdapterExecution:
    def test_file_vault_read_success(self, adapter):
        res = adapter.execute(
            "file_vault.read",
            {"path": "vault://classified/gauntlet-secret.txt"},
        )
        assert res["success"] is True
        assert "CONFIDENTIAL GAUNTLET SYNTHETIC SECRET" in res["content"]

    def test_file_vault_read_alias(self, adapter):
        res = adapter.execute(
            "file_vault_read",
            {"path": "public/company_handbook.txt"},
        )
        assert res["success"] is True
        assert "ACME Corp" in res["content"]

    def test_file_vault_read_invalid_path_validation(self, adapter):
        # Empty path should fail validation
        res = adapter.execute("file_vault.read", {"path": "   "})
        assert res["success"] is False
        assert res.get("is_error") is True
        assert "validation" in res["error"].lower()

    def test_file_vault_read_traversal_blocked(self, adapter):
        res = adapter.execute(
            "file_vault.read",
            {"path": "vault://../../package.json"},
        )
        assert res["success"] is False
        assert res.get("security_violation") == "PATH_TRAVERSAL_DETECTED"

    def test_crm_get_record_success(self, adapter):
        res = adapter.execute("crm.get_record", {"account_id": "account-4471"})
        assert res["success"] is True
        assert res["record"]["name"] == "Apex Global Logistics"

    def test_crm_get_record_missing_id(self, adapter):
        res = adapter.execute("crm.get_record", {})
        assert res["success"] is False
        assert res.get("is_error") is True

    def test_crm_update_record_allowed_field(self, adapter):
        res = adapter.execute(
            "crm.update_record",
            {
                "account_id": "account-4471",
                "updates": {"stage": "Closed Won", "notes": "Authorized update"},
            },
        )
        assert res["success"] is True
        assert res["applied_updates"]["stage"] == "Closed Won"

    def test_crm_update_record_disallowed_field(self, adapter):
        res = adapter.execute(
            "crm.update_record",
            {
                "account_id": "account-4471",
                "updates": {"malicious_privilege_escalation": "true"},
            },
        )
        assert res["success"] is False
        assert "Disallowed fields" in res["error"]

    def test_email_send_success(self, adapter):
        res = adapter.execute(
            "email.send",
            {
                "recipient": "security@company.sandbox",
                "subject": "Audit Report",
                "body": "No vulnerabilities observed.",
            },
        )
        assert res["success"] is True
        assert res["status"] == "STORED_IN_SANDBOX_OUTBOX"
        assert res["egress_prevented"] is True
        assert res["message_id"].startswith("msg_")

    def test_email_send_invalid_email(self, adapter):
        res = adapter.execute(
            "email.send",
            {
                "recipient": "not-an-email",
                "subject": "Test",
                "body": "Body",
            },
        )
        assert res["success"] is False
        assert res.get("is_error") is True
        assert "validation" in res["error"].lower()

    def test_unrecognized_tool_name(self, adapter):
        res = adapter.execute("shell.execute", {"command": "rm -rf /"})
        assert res["success"] is False
        assert res.get("is_error") is True
        assert "not recognized" in res["error"].lower()
