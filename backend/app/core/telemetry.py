"""Pydantic Telemetry Schema for Prompt-Injection Gauntlet (LLMShield).

Strict versioned telemetry models as mandated by Section 10 of prompt.txt.
Distinguishes proposed tool actions from verified executions.
Supports automatic camelCase serialization for SSE frontend streaming.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ExecutionPath(str, Enum):
    UNGOVERNED = "ungoverned"
    PROTECTED = "protected"


class AuthorizationStatus(str, Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    AUTHORIZED = "AUTHORIZED"
    POLICY_DENIED = "POLICY_DENIED"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    AUTHORIZATION_TIMEOUT = "AUTHORIZATION_TIMEOUT"
    INVALID_REQUEST = "INVALID_REQUEST"


class ToolExecutionStatus(str, Enum):
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    PROPOSED = "PROPOSED"
    BLOCKED = "BLOCKED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class EventType(str, Enum):
    RUN_STARTED = "RUN_STARTED"
    TEST_CASE_LOADED = "TEST_CASE_LOADED"
    AGENT_REASONING = "AGENT_REASONING"
    TOOL_CALL_PROPOSED = "TOOL_CALL_PROPOSED"
    AUTHORIZATION_REQUESTED = "AUTHORIZATION_REQUESTED"
    AUTHORIZATION_RESULT = "AUTHORIZATION_RESULT"
    TOOL_EXECUTION_STARTED = "TOOL_EXECUTION_STARTED"
    TOOL_EXECUTION_COMPLETED = "TOOL_EXECUTION_COMPLETED"
    TOOL_EXECUTION_BLOCKED = "TOOL_EXECUTION_BLOCKED"
    ERROR = "ERROR"
    RUN_COMPLETED = "RUN_COMPLETED"


class Severity(str, Enum):
    NEUTRAL = "neutral"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"


class GauntletEvent(BaseModel):
    """Structured security telemetry event model."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        use_enum_values=True,
    )

    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    run_id: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    execution_path: ExecutionPath
    target_agent: str
    event_type: EventType
    tool_name: Optional[str] = None
    requested_action: Optional[str] = None
    authorization_status: AuthorizationStatus = AuthorizationStatus.NOT_APPLICABLE
    policy_id: Optional[str] = None
    tool_execution_status: ToolExecutionStatus = ToolExecutionStatus.NOT_ATTEMPTED
    remediation_action: Optional[str] = None
    error_type: Optional[str] = None
    summary: str
    redacted_details: Optional[str] = None
    severity: Severity = Severity.INFO
