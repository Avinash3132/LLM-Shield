"use client";

import { Play, Square } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { SCENARIOS } from "@/lib/gauntlet/content";
import type { RunStatus } from "@/lib/gauntlet/types";

interface RunControlsProps {
  scenarioId: string;
  onScenarioChange: (id: string) => void;
  status: RunStatus;
  onRun: () => void;
  onStop: () => void;
  progress: number;
  elapsedMs: number;
  durationMs: number;
}

function formatSeconds(ms: number): string {
  return `${(ms / 1000).toFixed(1)}s`;
}

export function RunControls({
  scenarioId,
  onScenarioChange,
  status,
  onRun,
  onStop,
  progress,
  elapsedMs,
  durationMs,
}: RunControlsProps) {
  const isRunning = status === "running";
  const pct = Math.max(0, Math.min(100, progress));

  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-line bg-surface/70 p-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <label className="flex w-full flex-col gap-2 md:max-w-md">
          <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-dim">
            Attack scenario
          </span>
          <select
            value={scenarioId}
            onChange={(event) => onScenarioChange(event.target.value)}
            disabled={isRunning}
            className="w-full rounded-xl border border-line bg-surface-2 px-3 py-2.5 text-sm text-foreground outline-none transition-colors hover:border-brand/40 disabled:cursor-not-allowed disabled:opacity-60 [&_option]:bg-[#0e1320]"
          >
            {SCENARIOS.map((scenario) => (
              <option key={scenario.id} value={scenario.id}>
                {scenario.code} — {scenario.name}
              </option>
            ))}
          </select>
        </label>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onRun}
            disabled={isRunning}
            className="inline-flex items-center gap-2 rounded-xl bg-foreground px-5 py-2.5 text-sm font-semibold text-background transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Play className="h-4 w-4" />
            {status === "idle" ? "Run test" : "Run again"}
          </button>
          <button
            type="button"
            onClick={onStop}
            disabled={!isRunning}
            className="inline-flex items-center gap-2 rounded-xl border border-line bg-surface-2 px-5 py-2.5 text-sm font-medium text-foreground transition-colors hover:border-danger/50 hover:text-danger disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Square className="h-4 w-4" />
            Stop
          </button>
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <div
          className="h-1.5 w-full overflow-hidden rounded-full bg-surface-2"
          role="progressbar"
          aria-valuenow={Math.round(pct)}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className="h-full rounded-full bg-gradient-to-r from-brand to-brand-2 transition-[width] duration-100 ease-linear"
            style={{ width: `${pct}%` }}
          />
        </div>
        <div className="flex items-center justify-between font-mono text-[11px] text-dim">
          <span>
            {formatSeconds(elapsedMs)} / {formatSeconds(durationMs)}
          </span>
          <span>{Math.round(pct)}%</span>
        </div>
      </div>

      {status === "cancelled" ? (
        <Badge tone="warning" className="w-fit">
          run cancelled — no background tool activity continues
        </Badge>
      ) : null}
    </div>
  );
}
