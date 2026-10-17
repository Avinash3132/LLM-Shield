import { AlertTriangle, CheckCircle2, Clock } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { RunSummary } from "@/lib/gauntlet/simulation";
import type { RunStatus } from "@/lib/gauntlet/types";

const ROWS = [
  { key: "attempts", label: "Tool call attempts" },
  { key: "executions", label: "Actual executions" },
  { key: "blocked", label: "Blocked at boundary" },
  { key: "authorized", label: "Authorization granted" },
  { key: "denied", label: "Policy denied" },
  { key: "authFailures", label: "Authorization failures" },
  { key: "violations", label: "Confirmed violations" },
] as const;

interface SummaryPanelProps {
  summary: RunSummary | null;
  status: RunStatus;
}

function Verdict({
  status,
  summary,
}: {
  status: RunStatus;
  summary: RunSummary | null;
}) {
  if (status === "running") {
    return (
      <div className="flex items-center gap-2 text-sm text-info">
        <Clock className="h-4 w-4" />
        Awaiting run completion — counts below are live.
      </div>
    );
  }

  if (status === "cancelled") {
    return (
      <div className="flex items-center gap-2 text-sm text-warn">
        <AlertTriangle className="h-4 w-4" />
        Run cancelled. Partial results only; no mitigation claim is made.
      </div>
    );
  }

  if (status === "idle" || !summary) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted">
        <Clock className="h-4 w-4" />
        Select a scenario and start a run to populate the comparison.
      </div>
    );
  }

  if (summary.baseline.violations === 0) {
    return (
      <div className="flex items-center gap-2 text-sm text-warn">
        <AlertTriangle className="h-4 w-4" />
        The baseline path did not follow the malicious instruction on this run,
        so no mitigation is attributed. Replay to observe variance.
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-sm text-safe">
      <CheckCircle2 className="h-4 w-4" />
      Mitigation demonstrated: the baseline executed the attack while the
      protected path executed none of it.
    </div>
  );
}

export function SummaryPanel({ summary, status }: SummaryPanelProps) {
  return (
    <section className="min-w-0 rounded-2xl border border-line bg-surface/70 p-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold tracking-tight">
            Comparison summary
          </h2>
          <p className="text-sm text-muted">
            Counts separate what was proposed from what actually ran.
          </p>
        </div>
        <Badge tone="neutral">telemetry v1</Badge>
      </header>

      <div className="mt-5 overflow-x-auto">
        <table className="w-full min-w-[28rem] border-collapse text-sm">
          <thead>
            <tr className="border-b border-line text-left font-mono text-[10px] uppercase tracking-[0.16em] text-dim">
              <th className="px-2 py-2 font-normal">Metric</th>
              <th className="px-2 py-2 text-right font-normal">Ungoverned</th>
              <th className="px-2 py-2 text-right font-normal">Protected</th>
            </tr>
          </thead>
          <tbody>
            {ROWS.map((row) => {
              const baselineValue = summary ? summary.baseline[row.key] : 0;
              const protectedValue = summary
                ? summary.protectedPath[row.key]
                : 0;
              const emphasise = row.key === "violations";
              return (
                <tr key={row.key} className="border-b border-line/60">
                  <td className="px-2 py-2.5 text-muted">{row.label}</td>
                  <td
                    className={cn(
                      "px-2 py-2.5 text-right font-mono",
                      emphasise && baselineValue > 0
                        ? "text-danger"
                        : "text-foreground",
                    )}
                  >
                    {baselineValue}
                  </td>
                  <td
                    className={cn(
                      "px-2 py-2.5 text-right font-mono",
                      emphasise && protectedValue > 0
                        ? "text-danger"
                        : "text-foreground",
                    )}
                  >
                    {protectedValue}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-5 border-t border-line pt-4">
        <Verdict status={status} summary={summary} />
      </div>
    </section>
  );
}
