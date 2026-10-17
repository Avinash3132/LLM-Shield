"""Dual-Execution Coordinator and Run Manager.

For every test run:
1. Generates a unique run ID
2. Loads a versioned test case
3. Creates independent execution contexts for both paths
4. Provides equivalent test inputs
5. Runs the two paths concurrently
6. Records events independently
7. Streams events as they occur
8. Aggregates final outcomes
9. Calculates a comparison summary
"""

import asyncio
import uuid
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from ..core.telemetry import GauntletEvent, ExecutionPath
from ..config import settings
from ..sandboxes import FileVaultSandbox, CRMSandbox, EmailSandbox
from ..mcp.adapter import SandboxToolAdapter
from ..armoriq.client import ArmorIQClient
from ..armoriq.interceptor import AuthorizationInterceptor
from ..agent.gemini_provider import GeminiProvider, ModelTurnResult, ToolCallRequest
from ..agent.runner import AgentRunner, RunResult
from ..agent.protected_runner import ProtectedAgentRunner
from ..scenarios.catalog import get_scenario_by_id
from ..scenarios.evaluator import ScenarioEvaluator
from ..scenarios.models import ScenarioOutcome, ComparisonSummary


class DualRunResult(BaseModel):
    run_id: str
    scenario_id: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    baseline: Optional[RunResult] = None
    protected: Optional[RunResult] = None
    comparison: Optional[ComparisonSummary] = None
    all_events: List[GauntletEvent] = Field(default_factory=list)


# In-memory run storage (sufficient for Phase 1-10 scope)
_active_runs: Dict[str, DualRunResult] = {}
_run_events: Dict[str, List[GauntletEvent]] = {}
_cancelled_runs: set = set()


def generate_run_id() -> str:
    return f"run_{uuid.uuid4().hex[:10]}"


async def execute_dual_run(
    scenario_id: str,
    on_event: Optional[Callable[[GauntletEvent], None]] = None,
    mock_baseline_handler: Optional[Any] = None,
    mock_protected_handler: Optional[Any] = None,
    mock_armoriq_handler: Optional[Any] = None,
    simulate_armoriq_timeout: bool = False,
) -> DualRunResult:
    """Execute both ungoverned and protected paths concurrently."""
    scenario = get_scenario_by_id(scenario_id)
    if not scenario:
        raise ValueError(f"Scenario '{scenario_id}' not found.")

    run_id = generate_run_id()
    _run_events[run_id] = []
    _cancelled_runs.discard(run_id)

    def collect_event(event: GauntletEvent) -> None:
        _run_events.setdefault(run_id, []).append(event)
        if on_event:
            try:
                on_event(event)
            except Exception:
                pass

    dual_result = DualRunResult(
        run_id=run_id,
        scenario_id=scenario_id,
        status="running",
        started_at=datetime.now(timezone.utc).isoformat(),
    )
    _active_runs[run_id] = dual_result

    # Create ISOLATED sandbox instances for each path (no shared mutable state)
    baseline_vault = FileVaultSandbox(settings.file_vault_dir)
    baseline_crm = CRMSandbox(settings.crm_data_path)
    baseline_crm.reload_from_fixture()
    baseline_email = EmailSandbox(settings.email_outbox_path)
    baseline_adapter = SandboxToolAdapter(
        vault=baseline_vault, crm=baseline_crm, email=baseline_email
    )

    protected_vault = FileVaultSandbox(settings.file_vault_dir)
    protected_crm = CRMSandbox(settings.crm_data_path)
    protected_crm.reload_from_fixture()
    protected_email = EmailSandbox(settings.email_outbox_path)
    protected_adapter = SandboxToolAdapter(
        vault=protected_vault, crm=protected_crm, email=protected_email
    )

    # Providers
    baseline_provider = GeminiProvider(mock_handler=mock_baseline_handler)
    protected_provider = GeminiProvider(mock_handler=mock_protected_handler)

    # ArmorIQ client for interceptor
    use_timeout = simulate_armoriq_timeout or scenario.code == "E"
    armoriq_client = ArmorIQClient(simulate_timeout=use_timeout, mock_auth_handler=mock_armoriq_handler)
    interceptor = AuthorizationInterceptor(
        tool_adapter=protected_adapter, armoriq_client=armoriq_client
    )

    # Runners
    baseline_runner = AgentRunner(
        tool_adapter=baseline_adapter,
        provider=baseline_provider,
        target_agent=scenario.agent_role,
        max_turns=5,
    )
    protected_runner = ProtectedAgentRunner(
        interceptor=interceptor,
        provider=protected_provider,
        target_agent=scenario.agent_role,
        max_turns=5,
    )

    task_prompt = scenario.initial_prompt

    # Run both paths concurrently
    async def run_baseline():
        if run_id in _cancelled_runs:
            return None
        return await baseline_runner.execute_run(
            run_id=run_id,
            scenario_id=scenario_id,
            scenario_name=scenario.name,
            task_prompt=task_prompt,
            execution_path=ExecutionPath.UNGOVERNED,
            on_event=collect_event,
        )

    async def run_protected():
        if run_id in _cancelled_runs:
            return None
        return await protected_runner.execute_run(
            run_id=run_id,
            scenario_id=scenario_id,
            scenario_name=scenario.name,
            task_prompt=task_prompt,
            on_event=collect_event,
        )

    try:
        baseline_result, protected_result = await asyncio.gather(
            run_baseline(), run_protected(), return_exceptions=True
        )

        if isinstance(baseline_result, Exception):
            baseline_result = RunResult(
                run_id=run_id, scenario_id=scenario_id,
                execution_path=ExecutionPath.UNGOVERNED, status="failed",
                summary=f"Baseline failed: {str(baseline_result)}"
            )
        if isinstance(protected_result, Exception):
            protected_result = RunResult(
                run_id=run_id, scenario_id=scenario_id,
                execution_path=ExecutionPath.PROTECTED, status="failed",
                summary=f"Protected failed: {str(protected_result)}"
            )

    except asyncio.CancelledError:
        dual_result.status = "cancelled"
        dual_result.completed_at = datetime.now(timezone.utc).isoformat()
        _active_runs[run_id] = dual_result
        return dual_result

    # Evaluate outcomes
    baseline_outcome = ScenarioEvaluator.evaluate_path_outcome(
        run_id, scenario, ExecutionPath.UNGOVERNED,
        baseline_result.events if baseline_result else [],
        baseline_result.status if baseline_result else "failed",
    )
    protected_outcome = ScenarioEvaluator.evaluate_path_outcome(
        run_id, scenario, ExecutionPath.PROTECTED,
        protected_result.events if protected_result else [],
        protected_result.status if protected_result else "failed",
    )
    comparison = ScenarioEvaluator.compare_outcomes(
        run_id, scenario, baseline_outcome, protected_outcome
    )

    dual_result.baseline = baseline_result
    dual_result.protected = protected_result
    dual_result.comparison = comparison
    dual_result.all_events = _run_events.get(run_id, [])
    dual_result.status = "completed" if run_id not in _cancelled_runs else "cancelled"
    dual_result.completed_at = datetime.now(timezone.utc).isoformat()
    _active_runs[run_id] = dual_result

    return dual_result


def get_run(run_id: str) -> Optional[DualRunResult]:
    return _active_runs.get(run_id)


def get_run_events(run_id: str) -> List[GauntletEvent]:
    return _run_events.get(run_id, [])


def cancel_run(run_id: str) -> bool:
    if run_id in _active_runs:
        _cancelled_runs.add(run_id)
        if _active_runs[run_id].status == "running":
            _active_runs[run_id].status = "cancelled"
        return True
    return False
