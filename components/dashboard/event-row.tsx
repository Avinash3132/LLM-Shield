import { Badge, type BadgeTone } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type {
  AuthorizationStatus,
  EventType,
  GauntletEvent,
  Severity,
  ToolExecutionStatus,
} from "@/lib/gauntlet/types";

const EVENT_META: Record<EventType, { label: string; tone: BadgeTone }> = {
  RUN_STARTED: { label: "run started", tone: "neutral" },
  TEST_CASE_LOADED: { label: "test case", tone: "neutral" },
  AGENT_REASONING: { label: "reasoning", tone: "brand" },
  TOOL_CALL_PROPOSED: { label: "tool proposed", tone: "info" },
  AUTHORIZATION_REQUESTED: { label: "auth requested", tone: "info" },
  AUTHORIZATION_RESULT: { label: "auth result", tone: "brand" },
  TOOL_EXECUTION_STARTED: { label: "exec start", tone: "info" },
  TOOL_EXECUTION_COMPLETED: { label: "exec completed", tone: "success" },
  TOOL_EXECUTION_BLOCKED: { label: "exec blocked", tone: "danger" },
  ERROR: { label: "error", tone: "warning" },
  RUN_COMPLETED: { label: "run completed", tone: "neutral" },
};

const SEVERITY_BORDER: Record<Severity, string> = {
  neutral: "border-line",
  info: "border-info/50",
  success: "border-safe/50",
  warning: "border-warn/60",
  danger: "border-danger/70",
};

const AUTH_TONE: Record<AuthorizationStatus, BadgeTone> = {
  NOT_APPLICABLE: "neutral",
  AUTHORIZED: "success",
  POLICY_DENIED: "danger",
  AUTHENTICATION_FAILED: "danger",
  AUTHORIZATION_ERROR: "warning",
  AUTHORIZATION_TIMEOUT: "warning",
  INVALID_REQUEST: "warning",
};

const EXEC_TONE: Record<ToolExecutionStatus, BadgeTone> = {
  NOT_ATTEMPTED: "neutral",
  PROPOSED: "info",
  BLOCKED: "danger",
  EXECUTED: "success",
  FAILED: "danger",
};

function formatTime(iso: string): string {
  const date = new Date(iso);
  const pad = (value: number, length = 2) =>
    String(value).padStart(length, "0");
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(
    date.getSeconds(),
  )}.${pad(date.getMilliseconds(), 3)}`;
}

interface EventRowProps {
  event: GauntletEvent;
}

export function EventRow({ event }: EventRowProps) {
  const meta = EVENT_META[event.eventType];
  const showAuth = event.authorizationStatus !== "NOT_APPLICABLE";
  const showExec = event.toolExecutionStatus !== "NOT_ATTEMPTED";

  return (
    <li
      className={cn(
        "border-l-2 py-2.5 pr-2 pl-3",
        SEVERITY_BORDER[event.severity],
      )}
    >
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
        <time className="font-mono text-[11px] text-dim">
          {formatTime(event.timestamp)}
        </time>
        <Badge tone={meta.tone}>{meta.label}</Badge>
        <span className="font-mono text-[11px] text-muted">
          {event.targetAgent}
        </span>
        {event.toolName ? (
          <span className="font-mono text-[11px] text-brand">
            {event.toolName}
          </span>
        ) : null}
      </div>

      <p className="mt-1.5 text-[13px]/5 text-foreground/90">{event.summary}</p>

      {showAuth || showExec || event.policyId ? (
        <div className="mt-2 flex flex-wrap items-center gap-1.5">
          {showAuth ? (
            <Badge tone={AUTH_TONE[event.authorizationStatus]}>
              {event.authorizationStatus}
            </Badge>
          ) : null}
          {showExec ? (
            <Badge tone={EXEC_TONE[event.toolExecutionStatus]}>
              {event.toolExecutionStatus}
            </Badge>
          ) : null}
          {event.policyId ? (
            <span className="font-mono text-[10px] text-dim">
              {event.policyId}
            </span>
          ) : null}
        </div>
      ) : null}

      {event.redactedDetails ? (
        <p className="mt-2 rounded-md border border-line bg-surface-2/70 px-2 py-1 font-mono text-[11px] text-muted">
          {event.redactedDetails}
        </p>
      ) : null}

      {event.remediationAction ? (
        <p className="mt-1.5 text-[11px]/4 text-dim">
          Remediation: {event.remediationAction}
        </p>
      ) : null}
    </li>
  );
}
