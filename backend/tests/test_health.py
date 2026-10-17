"""Tests for FastAPI backend health check and scenarios endpoints."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "health_url" in data
    assert data["version"] == "0.1.0"


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "gemini" in data
    assert "armoriq" in data
    assert "sandboxes" in data
    assert data["sandboxes"]["file_vault_ready"] is True
    assert data["sandboxes"]["crm_ready"] is True
    assert data["sandboxes"]["email_outbox_ready"] is True


def test_scenarios_catalog():
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) == 5
    codes = [s["code"] for s in scenarios]
    assert set(codes) == {"A", "B", "C", "D", "E"}


def test_list_tools_endpoint():
    response = client.get("/api/tools")
    assert response.status_code == 200
    data = response.json()
    assert "mcp_tools" in data
    assert "gemini_declarations" in data
    assert data["count"] == 6


def test_execute_tool_endpoint():
    payload = {
        "tool_name": "file_vault.read",
        "arguments": {"path": "vault://public/company_handbook.txt"},
    }
    response = client.post("/api/tools/execute", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert "ACME Corp" in result["content"]

