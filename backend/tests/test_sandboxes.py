"""Tests for isolated mock sandboxes (File Vault, CRM, Email Outbox)."""

import pytest
from app.config import settings
from app.sandboxes import FileVaultSandbox, CRMSandbox, EmailSandbox


@pytest.fixture
def vault():
    return FileVaultSandbox(settings.file_vault_dir)


@pytest.fixture
def crm():
    sandbox = CRMSandbox(settings.crm_data_path)
    sandbox.reload_from_fixture()
    return sandbox


@pytest.fixture
def email_box(tmp_path):
    outbox_file = tmp_path / "test_outbox.json"
    return EmailSandbox(outbox_file)


class TestFileVaultSandbox:
    def test_read_valid_synthetic_classified_secret(self, vault):
        result = vault.read_file("vault://classified/gauntlet-secret.txt")
        assert result["success"] is True
        assert "CONFIDENTIAL GAUNTLET SYNTHETIC SECRET" in result["content"]
        assert result["bytes"] > 0

    def test_read_valid_public_handbook(self, vault):
        result = vault.read_file("public/company_handbook.txt")
        assert result["success"] is True
        assert "ACME Corp" in result["content"]

    def test_read_poisoned_brief(self, vault):
        result = vault.read_file("vault://briefs/q3_market_brief.txt")
        assert result["success"] is True
        assert "SYSTEM INSTRUCTION OVERRIDE" in result["content"]

    def test_block_path_traversal_parent_dir(self, vault):
        # Attempt traversal outside sandbox root
        result = vault.read_file("../../package.json")
        assert result["success"] is False
        assert result.get("security_violation") == "PATH_TRAVERSAL_DETECTED"
        assert "traversal blocked" in result["error"].lower()

    def test_block_path_traversal_with_vault_scheme(self, vault):
        result = vault.read_file("vault://../../../windows/system32/cmd.exe")
        assert result["success"] is False
        assert result.get("security_violation") == "PATH_TRAVERSAL_DETECTED"

    def test_read_nonexistent_file(self, vault):
        result = vault.read_file("vault://public/does_not_exist.txt")
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_list_files(self, vault):
        result = vault.list_files()
        assert result["success"] is True
        assert result["count"] >= 3
        paths = [f["relative_path"] for f in result["files"]]
        assert any("gauntlet-secret.txt" in p for p in paths)


class TestCRMSandbox:
    def test_get_existing_record(self, crm):
        result = crm.get_record("account-4471")
        assert result["success"] is True
        assert result["record"]["name"] == "Apex Global Logistics"

    def test_get_nonexistent_record(self, crm):
        result = crm.get_record("account-999999")
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_update_allowed_field(self, crm):
        result = crm.update_record("account-4471", {"stage": "Proposal Sent"})
        assert result["success"] is True
        assert result["applied_updates"]["stage"] == "Proposal Sent"

        # Verify change reflected in get
        fetched = crm.get_record("account-4471")
        assert fetched["record"]["stage"] == "Proposal Sent"

    def test_reject_disallowed_field(self, crm):
        result = crm.update_record(
            "account-4471",
            {"malicious_admin_escalation": True},
        )
        assert result["success"] is False
        assert "Disallowed fields" in result["error"]

    def test_fixture_reset(self, crm):
        crm.update_record("account-4471", {"stage": "Modified Stage"})
        assert crm.get_record("account-4471")["record"]["stage"] == "Modified Stage"

        crm.reload_from_fixture()
        assert crm.get_record("account-4471")["record"]["stage"] == "Discovery"


class TestEmailSandbox:
    def test_send_email_stored_locally(self, email_box):
        result = email_box.send_email(
            recipient="test@example.sandbox",
            subject="Alert",
            body="Test message body",
        )
        assert result["success"] is True
        assert result["status"] == "STORED_IN_SANDBOX_OUTBOX"
        assert "LOCAL_SANDBOX_OUTBOX_ONLY" in result.get("warning", "") or result.get("status")

        # Verify in outbox list
        outbox = email_box.list_outbox()
        assert outbox["count"] == 1
        msg = outbox["messages"][0]
        assert msg["recipient"] == "test@example.sandbox"
        assert msg["egress_prevented"] is True

    def test_send_email_validation(self, email_box):
        res1 = email_box.send_email(recipient="", subject="Sub", body="Body")
        assert res1["success"] is False

        res2 = email_box.send_email(recipient="user@test.sandbox", subject="", body="Body")
        assert res2["success"] is False

    def test_clear_outbox(self, email_box):
        email_box.send_email("a@test.sandbox", "Sub1", "Body1")
        assert email_box.list_outbox()["count"] == 1

        clear_res = email_box.clear_outbox()
        assert clear_res["cleared_count"] == 1
        assert email_box.list_outbox()["count"] == 0
