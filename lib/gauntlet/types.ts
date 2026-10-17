/**
 * Versioned telemetry schema for the Gauntlet.
 *
 * These types mirror the Pydantic event model the FastAPI backend is specified
 * to emit, so the dashboard can consume live SSE payloads without reshaping.
 * Every field is required and explicit — the UI must be able to tell a *proposed*
 * action apart from an *executed* one at all times.
 */

export type ExecutionPath = "ungoverned" | "protected";

export type RunStatus = "idle" | "running" | "completed" | "cancelled";

export type ScenarioCode = "A" | "B" | "C" | "D" | "E";

export type AuthorizationStatus =
  | "NOT_APPLICABLE"
  | "AUTHORIZED"
  | "POLICY_DENIED"
  | "AUTHENTICATION_FAILED"
  | "AUTHORIZATION_ERROR"
  | "AUTHORIZATION_TIMEOUT"
  | "INVALID_REQUEST";

export type ToolExecutionStatus =
  | "NOT_ATTEMPTED"
  | "PROPOSED"
  | "BLOCKED"
  | "EXECUTED"
  | "FAILED";

export type EventType =
  | "RUN_STARTED"
  | "TEST_CASE_LOADED"
  | "AGENT_REASONING"
  | "TOOL_CALL_PROPOSED"
  | "AUTHORIZATION_REQUESTED"
  | "AUTHORIZATION_RESULT"
  | "TOOL_EXECUTION_STARTED"
  | "TOOL_EXECUTION_COMPLETED"
  | "TOOL_EXECUTION_BLOCKED"
  | "ERROR"
  | "RUN_COMPLETED";

export type Severity = "neutral" | "info" | "success" | "warning" | "danger";

export interface GauntletEvent {
  eventId: string;
  runId: string;
  timestamp: string;
  executionPath: ExecutionPath;
  targetAgent: string;
  eventType: EventType;
  toolName: string | null;
  requestedAction: string | null;
  authorizationStatus: AuthorizationStatus;
  /** Only ever populated when the remote authorization layer actually returned one. */
  policyId: string | null;
  toolExecutionStatus: ToolExecutionStatus;
  remediationAction: string | null;
  errorType: string | null;
  /** Sanitized, human readable description. Never contains secrets or tokens. */
  summary: string;
  redactedDetails: string | null;
  severity: Severity;
}

/** An event template before the runner stamps it with a run id and timestamp. */
export interface EventBlueprint {
  afterMs: number;
  targetAgent: string;
  eventType: EventType;
  toolName?: string;
  requestedAction?: string;
  authorizationStatus?: AuthorizationStatus;
  policyId?: string;
  toolExecutionStatus?: ToolExecutionStatus;
  remediationAction?: string;
  errorType?: string;
  summary: string;
  redactedDetails?: string;
  severity: Severity;
}

export interface Scenario {
  id: string;
  code: ScenarioCode;
  name: string;
  summary: string;
  description: string;
  agentRole: string;
  objective: string;
  expectedProtectedOutcome: string;
  tags: string[];
}

export interface RunOutcome {
  runId: string;
  scenarioId: string;
  status: "idle" | "running" | "completed" | "cancelled";
  startedAt: string | null;
  completedAt: string | null;
  mitigated: boolean | null;
}

export const EXECUTION_PATH_LABEL: Record<ExecutionPath, string> = {
  ungoverned: "Ungoverned agent",
  protected: "ArmorIQ-protected agent",
};
