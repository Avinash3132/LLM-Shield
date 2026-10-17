"""Pydantic Models for Versioned Adversarial Scenarios and Outcomes."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from ..core.telemetry import ExecutionPath


class ScenarioDefinition(BaseModel):
    """Complete definition of a versioned attack or evaluation scenario."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    code: str
    name: str
    summary: str
    description: str
    agent_role: str
    initial_prompt: str
    context_files: List[str] = Field(default_factory=list)
    target_secret_path: Optional[str] = None
    target_account_id: Optional[str] = None
    exfil_recipient: Optional[str] = None
    expected_behavior: str
    expected_protected_outcome: str
    tags: List[str] = Field(default_factory=list)


class ScenarioOutcome(BaseModel):
    """Evaluated security outcome for a single execution path."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    run_id: str
    scenario_id: str
    execution_path: ExecutionPath
    status: str
    total_tool_attempts: int = 0
    authorized_actions: int = 0
    denied_actions: int = 0
    authorization_failures: int = 0
    actual_sandbox_operations: int = 0
    policy_violations: int = 0
    sensitive_data_accessed: bool = False
    exfiltration_occurred: bool = False
    privilege_escalation_attempted: bool = False
    privilege_escalation_executed: bool = False
    mitigated: bool = False
    summary: str = ""


class ComparisonSummary(BaseModel):
    """Side-by-side comparative evaluation of baseline vs protected execution paths."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    run_id: str
    scenario_id: str
    baseline: ScenarioOutcome
    protected: Optional[ScenarioOutcome] = None
    mitigation_demonstrated: bool = False
    verdict: str
