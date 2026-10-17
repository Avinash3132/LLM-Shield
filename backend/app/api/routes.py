"""API Routes for LLMShield Gauntlet Backend.

Provides system health, scenario catalogs, sandbox inspection, run management,
and SSE event streaming endpoints.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..config import settings
from ..sandboxes import FileVaultSandbox, CRMSandbox, EmailSandbox
from ..mcp import SandboxToolAdapter
from ..scenarios import SCENARIOS, get_scenario_by_id
from ..execution import execute_dual_run, get_run, get_run_events, cancel_run

router = APIRouter(prefix="/api")

# Instantiate sandbox services and unified tool adapter
vault_sandbox = FileVaultSandbox(settings.file_vault_dir)
crm_sandbox = CRMSandbox(settings.crm_data_path)
email_sandbox = EmailSandbox(settings.email_outbox_path)
tool_adapter = SandboxToolAdapter(
    vault=vault_sandbox,
    crm=crm_sandbox,
    email=email_sandbox,
)


# ============================================================================
# Health & Configuration
# ============================================================================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint reporting backend and integration status."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "environment": settings.app_env,
        "gemini": {
            "configured": settings.is_gemini_configured,
            "model": settings.gemini_model,
        },
        "armoriq": {
            "configured": settings.is_armoriq_configured,
            "endpoint": settings.armoriq_endpoint,
            "agent_id": settings.armoriq_agent_id,
            "environment": settings.armoriq_environment,
        },
        "sandboxes": {
            "file_vault_ready": settings.file_vault_dir.exists(),
            "crm_ready": settings.crm_data_path.exists(),
            "email_outbox_ready": settings.email_outbox_path.exists(),
        },
    }


# ============================================================================
# Scenario Catalog
# ============================================================================

@router.get("/scenarios")
async def get_scenarios() -> List[Dict[str, Any]]:
    """Return catalog of versioned attack scenarios."""
    return [s.model_dump(by_alias=True) for s in SCENARIOS]


@router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str) -> Dict[str, Any]:
    """Retrieve detailed scenario definition by ID."""
    scenario = get_scenario_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")
    return scenario.model_dump(by_alias=True)


# ============================================================================
# Sandbox Inspection & Reset
# ============================================================================

@router.get("/sandboxes/vault")
async def inspect_vault(path: str = "") -> Dict[str, Any]:
    """List or inspect files within the isolated file vault sandbox."""
    return vault_sandbox.list_files(path)


@router.get("/sandboxes/crm")
async def inspect_crm(stage: str = None) -> Dict[str, Any]:
    """Inspect synthetic CRM records."""
    return crm_sandbox.list_records(stage)


@router.get("/sandboxes/email")
async def inspect_email_outbox() -> Dict[str, Any]:
    """Inspect locally contained sandbox email messages."""
    return email_sandbox.list_outbox()


@router.post("/sandboxes/reset")
async def reset_sandboxes() -> Dict[str, Any]:
    """Reset sandbox state back to pristine baseline fixtures."""
    crm_sandbox.reload_from_fixture()
    email_sandbox.clear_outbox()
    return {
        "success": True,
        "message": "Sandboxes reset to baseline fixtures successfully.",
    }


# ============================================================================
# MCP Tools
# ============================================================================

class ToolExecuteRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = {}


@router.get("/tools")
async def list_tools() -> Dict[str, Any]:
    """Return available MCP tools and their parameter schemas."""
    return {
        "mcp_tools": tool_adapter.registry.to_mcp_catalog(),
        "gemini_declarations": tool_adapter.registry.to_gemini_declarations(),
        "count": len(tool_adapter.registry.list_tools()),
    }


@router.post("/tools/execute")
async def execute_tool(req: ToolExecuteRequest) -> Dict[str, Any]:
    """Execute a sandbox tool call through the unified tool adapter."""
    return tool_adapter.execute(req.tool_name, req.arguments)


# ============================================================================
# Run Management & SSE Streaming (Phase 8)
# ============================================================================

class CreateRunRequest(BaseModel):
    scenario_id: str


# Tracks background run tasks to prevent overlapping
_running_task: Optional[asyncio.Task] = None
_current_run_id: Optional[str] = None


@router.post("/runs")
async def create_run(req: CreateRunRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Start a new dual-execution test run."""
    global _running_task, _current_run_id

    scenario = get_scenario_by_id(req.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{req.scenario_id}' not found.")

    # Prevent overlapping runs
    if _running_task and not _running_task.done():
        raise HTTPException(
            status_code=409,
            detail=f"Run '{_current_run_id}' is already in progress. Cancel it first or wait."
        )

    # Execute in background so the POST returns immediately with the run_id
    loop = asyncio.get_event_loop()

    async def _run_wrapper():
        global _running_task, _current_run_id
        try:
            result = await execute_dual_run(scenario_id=req.scenario_id)
            return result
        finally:
            _running_task = None
            _current_run_id = None

    _running_task = asyncio.ensure_future(_run_wrapper())

    # We need to get the run_id. Wait briefly for initialization
    await asyncio.sleep(0.1)

    # Find the latest run for this scenario
    from ..execution.coordinator import _active_runs
    latest_run = None
    for rid, run in _active_runs.items():
        if run.scenario_id == req.scenario_id:
            latest_run = run
            _current_run_id = rid

    if latest_run:
        return {
            "run_id": latest_run.run_id,
            "scenario_id": req.scenario_id,
            "status": latest_run.status,
            "started_at": latest_run.started_at,
        }
    else:
        return {
            "run_id": "pending",
            "scenario_id": req.scenario_id,
            "status": "initializing",
        }


@router.get("/runs/{run_id}")
async def get_run_status(run_id: str) -> Dict[str, Any]:
    """Get current status of a run."""
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    result: Dict[str, Any] = {
        "run_id": run.run_id,
        "scenario_id": run.scenario_id,
        "status": run.status,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
    }

    if run.comparison:
        result["comparison"] = run.comparison.model_dump(by_alias=True)

    return result


@router.get("/runs/{run_id}/results")
async def get_run_results(run_id: str) -> Dict[str, Any]:
    """Get final results and comparison summary for a completed run."""
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    result: Dict[str, Any] = {
        "run_id": run.run_id,
        "scenario_id": run.scenario_id,
        "status": run.status,
    }

    if run.baseline:
        result["baseline"] = run.baseline.model_dump()
    if run.protected:
        result["protected"] = run.protected.model_dump()
    if run.comparison:
        result["comparison"] = run.comparison.model_dump(by_alias=True)

    return result


@router.get("/runs/{run_id}/events")
async def stream_run_events(run_id: str, request: Request):
    """Stream run events through Server-Sent Events (SSE)."""
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    async def event_generator():
        last_index = 0
        max_idle = 60  # seconds max idle before closing
        idle_count = 0

        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break

            events = get_run_events(run_id)
            new_events = events[last_index:]

            if new_events:
                idle_count = 0
                for event in new_events:
                    data = event.model_dump(by_alias=True)
                    yield f"data: {json.dumps(data)}\n\n"
                last_index = len(events)

            # Check if run is complete
            current_run = get_run(run_id)
            if current_run and current_run.status in ("completed", "cancelled", "failed"):
                # Send final status event
                yield f"event: run_complete\ndata: {json.dumps({'status': current_run.status, 'run_id': run_id})}\n\n"
                break

            idle_count += 1
            if idle_count > max_idle * 4:
                break

            await asyncio.sleep(0.25)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/runs/{run_id}/cancel")
async def cancel_run_endpoint(run_id: str) -> Dict[str, Any]:
    """Cancel a running test execution."""
    success = cancel_run(run_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found or already completed.")
    return {"success": True, "run_id": run_id, "status": "cancelled"}
