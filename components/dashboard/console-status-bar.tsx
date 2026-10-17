import { Activity, Cpu, Database, ShieldQuestion, ShieldCheck } from "lucide-react";

import { StatusDot, type BadgeTone } from "@/components/ui/badge";
import type { RunStatus } from "@/lib/gauntlet/types";
import type { HealthStatus } from "@/lib/gauntlet/api";

const RUN_STATUS_META: Record<
  RunStatus,
  { label: string; tone: BadgeTone; pulse: boolean }
> = {
  idle: { label: "idle", tone: "neutral", pulse: false },
  running: { label: "running", tone: "info", pulse: true },
  completed: { label: "completed", tone: "success", pulse: false },
  cancelled: { label: "cancelled", tone: "warning", pulse: false },
};

interface ConsoleStatusBarProps {
  runStatus: RunStatus;
  runId: string | null;
  health?: HealthStatus | null;
  isLiveMode?: boolean;
}

function StatusItem({
  icon,
  label,
  value,
  tone,
  pulse,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  tone: BadgeTone;
  pulse?: boolean;
}) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-line bg-surface/70 px-4 py-3">
      <span className="grid h-8 w-8 place-items-center rounded-lg border border-line bg-surface-2 text-muted">
        {icon}
      </span>
      <div className="leading-tight">
        <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-dim">
          {label}
        </p>
        <p className="flex items-center gap-1.5 text-sm font-medium">
          <StatusDot tone={tone} pulse={pulse} />
          {value}
        </p>
      </div>
    </div>
  );
}

export function ConsoleStatusBar({
  runStatus,
  runId,
  health,
  isLiveMode = false,
}: ConsoleStatusBarProps) {
  const runMeta = RUN_STATUS_META[runStatus];

  // Dynamic backend status based on real health check
  const backendLabel = health
    ? "FastAPI :8000"
    : isLiveMode
    ? "Connecting..."
    : "Simulation Mode";
  const backendTone: BadgeTone = health
    ? "success"
    : isLiveMode
    ? "warning"
    : "neutral";

  // Dynamic Gemini model status
  const geminiLabel = health?.gemini
    ? `${health.gemini.model} · ${health.gemini.configured ? "Active" : "Unconfigured"}`
    : "gemini-3.7-flash · Scripted";
  const geminiTone: BadgeTone = health?.gemini.configured
    ? "success"
    : "warning";

  // Dynamic ArmorIQ status (Fail-Secure honest telemetry)
  const armoriqLabel = health?.armoriq.configured
    ? "ArmorIQ · Live Active"
    : "Fail-Secure Interceptor";
  const armoriqTone: BadgeTone = health?.armoriq.configured
    ? "success"
    : "warning";

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <StatusItem
        icon={<Database className="h-4 w-4" />}
        label="Backend"
        value={backendLabel}
        tone={backendTone}
        pulse={isLiveMode && !health}
      />
      <StatusItem
        icon={<Cpu className="h-4 w-4" />}
        label="Gemini model"
        value={geminiLabel}
        tone={geminiTone}
      />
      <StatusItem
        icon={health?.armoriq.configured ? <ShieldCheck className="h-4 w-4" /> : <ShieldQuestion className="h-4 w-4" />}
        label="ArmorIQ"
        value={armoriqLabel}
        tone={armoriqTone}
      />
      <div className="flex items-center justify-between gap-3 rounded-xl border border-line bg-surface/70 px-4 py-3">
        <div className="flex items-center gap-3">
          <span className="grid h-8 w-8 place-items-center rounded-lg border border-line bg-surface-2 text-muted">
            <Activity className="h-4 w-4" />
          </span>
          <div className="leading-tight">
            <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-dim">
              Run status
            </p>
            <p className="flex items-center gap-1.5 text-sm font-medium">
              <StatusDot tone={runMeta.tone} pulse={runMeta.pulse} />
              {runMeta.label}
            </p>
          </div>
        </div>
        <span className="font-mono text-[11px] text-dim">
          {runId ?? "no run id"}
        </span>
      </div>
    </div>
  );
}
