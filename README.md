# LLMShield — Adversarial Agent Governance Platform

LLMShield is an interactive cybersecurity platform designed to demonstrate and mitigate indirect prompt injection attacks against autonomous AI agents. It executes adversarial test cases through two concurrent, independent paths: an **ungoverned baseline agent** and an **ArmorIQ-governed protected agent**, streaming live security telemetry to a split-screen dashboard.

---

## 1. Architecture Overview

```
                          ┌──────────────────────────┐
                          │   Next.js 16 Dashboard   │
                          │   (Live SSE / REST API)  │
                          └─────────────┬────────────┘
                                        │
                                        ▼
                          ┌──────────────────────────┐
                          │     FastAPI Backend      │
                          │   (Port 8000 / Uvicorn)  │
                          └─────────────┬────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    │ Asynchronous Dual-Execution Engine     │
                    └─────────┬───────────────────┬─────────┘
                              │                   │
               ┌──────────────▼──────┐     ┌──────▼──────────────┐
               │ Path A: Ungoverned  │     │ Path B: Protected   │
               │ Baseline Agent      │     │ Governed Agent      │
               └──────────────┬──────┘     └──────┬──────────────┘
                              │                   │
                              │            ┌──────▼──────────────┐
                              │            │ Runtime Interceptor │
                              │            │ (ArmorIQ & RBAC)    │
                              │            └──────┬──────────────┘
                              │                   │ (Only if Authorized)
                              ▼                   ▼
               ┌─────────────────────────────────────────────────┐
               │            Isolated Mock Sandboxes              │
               │  • File Vault (Classified / Public Briefs)      │
               │  • CRM Sandbox (Scoped Synthetic Accounts)      │
               │  • Email Outbox (Local Append-Only Quarantine)  │
               └─────────────────────────────────────────────────┘
```

---

## 2. Adversarial Scenarios Catalog

| Scenario | Code | Target Agent | Attack Vector | Expected Protected Outcome |
| :--- | :---: | :--- | :--- | :--- |
| **Indirect Prompt Injection** | **A** | Researcher | Poisoned market brief instructs secret exfil | Blocked at file read & email dispatch |
| **Privilege Escalation** | **B** | Researcher | Out-of-scope write to CRM account record | Denied by role-based scope check |
| **Unauthorized Exfiltration** | **C** | Orchestrator | Two-stage read-and-send kill chain | Classified read blocked; outbox remains empty |
| **Benign Authorized Action** | **D** | Researcher | Legitimate read of public market brief | Authorized and executed normally |
| **Authorization Failure** | **E** | Publisher | Outage/timeout simulation | Fails secure; tool blocked without fake denial |

---

## 3. Quickstart Guide

### Prerequisites
- **Node.js**: v18+ (Next.js 16 / React 19)
- **Python**: 3.11+ (Python 3.14 verified)

### Configuration
1. Copy the environment configuration:
   ```bash
   cp .env.example .env
   ```
2. Set API keys in `.env`:
   - `GEMINI_API_KEY`: Google Gemini API key (for autonomous agent reasoning and MCP tool calls).
   - `ARMORIQ_API_KEY`: ArmorIQ platform API key (for live authorization checks).

---

### Running Locally

#### Terminal 1: Backend (FastAPI on Port 8000)
```powershell
cd backend
.\venv\Scripts\activate
python run.py
```
- API Base: `http://localhost:8000/api`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

#### Terminal 2: Frontend (Next.js on Port 3000)
```powershell
npm run dev
```
- Dashboard Console: [http://localhost:3000/dashboard](http://localhost:3000/dashboard)
- Landing Page: [http://localhost:3000](http://localhost:3000)

---

## 4. Automated Test Suite

All 64 backend unit and integration tests can be run with:

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests/ -v
```

### Coverage Highlights
- **`test_sandboxes.py`** (15 tests): Path traversal blocking, virtual URI normalization, CRM mutation limits, and local email containment.
- **`test_mcp_tools.py`** (15 tests): MCP tool schemas, alias resolution, Gemini declarations, and error isolation.
- **`test_scenarios.py`** (9 tests): Scenarios catalog integrity, lookup models, and `ScenarioEvaluator` metrics.
- **`test_agent.py`** (9 tests): Prompt builder, Gemini provider tool declarations, bounded loop, and synthetic secret redaction.
- **`test_armoriq.py`** (6 tests): Fail-secure unconfigured behavior, simulated timeouts, RBAC permissions matrix, and runtime interceptor.
- **`test_execution.py`** (5 tests): Parallel dual-run execution, REST run lifecycle, and SSE event streaming.
- **`test_health.py`** (5 tests): Health endpoints and configuration reporting.

---

## 5. Security Principles Enforced

1. **Mandatory Interception**: No protected agent tool call can bypass the `AuthorizationInterceptor`.
2. **Fail-Secure Architecture**: Network timeouts, authentication errors, or service outages automatically block execution.
3. **Honest Telemetry**: Model tool proposals are distinguished from verified executions. No fake success states are ever fabricated.
4. **Local Sandbox Containment**: All file operations, CRM mutations, and emails are strictly confined to local mock fixtures.
