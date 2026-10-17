"use client";

import { useCallback, useEffect, useMemo, useState, useRef } from "react";
import { Radio, Sparkles, RefreshCw } from "lucide-react";

import { AgentPanel } from "@/components/dashboard/agent-panel";
import { ConsoleStatusBar } from "@/components/dashboard/console-status-bar";
import { RunControls } from "@/components/dashboard/run-controls";
import { SummaryPanel } from "@/components/dashboard/summary-panel";
import { Badge } from "@/components/ui/badge";
import { getScenario } from "@/lib/gauntlet/content";
import {
  buildRunScript,
  summarizeRun,
  type RunScript,
} from "@/lib/gauntlet/simulation";
import type { GauntletEvent, RunStatus } from "@/lib/gauntlet/types";
import {
  fetchHealth,
  createRun,
  cancelRun as apiCancelRun,
  streamRunEvents,
  type HealthStatus,
} from "@/lib/gauntlet/api";

const TICK_MS = 70;

function createRunId(): string {
  const random =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID().replace(/-/g, "")
      : Math.random().toString(16).slice(2);
  return `run_${random.slice(0, 10)}`;
}

type ExecutionMode = "live" | "simulation";

export function GauntletConsole() {
  const [scenarioId, setScenarioId] = useState("scenario-a");
  const [mode, setMode] = useState<ExecutionMode>("simulation");
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [phase, setPhase] = useState<RunStatus>("idle");

  // Simulation mode states
  const [script, setScript] = useState<RunScript | null>(null);
  const [elapsed, setElapsed] = useState(0);

  // Live backend states
  const [liveRunId, setLiveRunId] = useState<string | null>(null);
  const [liveEvents, setLiveEvents] = useState<GauntletEvent[]>([]);
  const sseCleanupRef = useRef<(() => void) | null>(null);

  const scenario = getScenario(scenarioId);

  // Poll backend health on mount and periodically
  const checkBackendHealth = useCallback(async () => {
    try {
      const h = await fetchHealth();
      setHealth(h);
      // Auto-switch to live if backend becomes available and we were idle in simulation
      setMode((prev) => (prev === "simulation" && phase === "idle" ? "live" : prev));
    } catch {
      setHealth(null);
      setMode("simulation");
    }
  }, [phase]);

  useEffect(() => {
    checkBackendHealth();
    const interval = setInterval(checkBackendHealth, 10000);
    return () => clearInterval(interval);
  }, [checkBackendHealth]);

  // Clean up any open SSE stream on unmount
  useEffect(() => {
    return () => {
      if (sseCleanupRef.current) {
        sseCleanupRef.current();
        sseCleanupRef.current = null;
      }
    };
  }, []);

  // Simulation clock
  const isSimFinished = script !== null && elapsed >= script.durationMs;
  useEffect(() => {
    if (mode !== "simulation" || phase !== "running" || isSimFinished) {
      return;
    }
    const timer = window.setInterval(() => {
      setElapsed((prev) => prev + TICK_MS);
    }, TICK_MS);
    return () => window.clearInterval(timer);
  }, [mode, phase, isSimFinished]);

  // Computed status
  const currentStatus: RunStatus = useMemo(() => {
    if (mode === "simulation") {
      return phase === "running" && isSimFinished ? "completed" : phase;
    }
    return phase;
  }, [mode, phase, isSimFinished]);

  // Handle Starting a Run
  const startRun = useCallback(async () => {
    if (currentStatus === "running") {
      return;
    }

    if (mode === "live" && health) {
      // LIVE BACKEND SSE EXECUTION
      setLiveEvents([]);
      setPhase("running");

      try {
        const resp = await createRun(scenarioId);
        const runId = resp.run_id;
        setLiveRunId(runId);

        // Open SSE stream
        if (sseCleanupRef.current) {
          sseCleanupRef.current();
        }

        const cleanup = streamRunEvents(runId, {
          onEvent: (event) => {
            setLiveEvents((prev) => [...prev, event]);
          },
          onComplete: (_status) => {
            setPhase("completed");
            if (sseCleanupRef.current) {
              sseCleanupRef.current();
              sseCleanupRef.current = null;
            }
          },
          onError: (err) => {
            console.warn("[GauntletConsole] SSE stream notice:", err.message);
            // Don't mark failed immediately if we already received events
            setPhase("completed");
          },
        });

        sseCleanupRef.current = cleanup;
      } catch (err) {
        console.error("Failed to start live run:", err);
        // Fall back gracefully to simulation
        setMode("simulation");
        const simScript = buildRunScript(scenarioId, createRunId());
        setScript(simScript);
        setElapsed(0);
        setPhase("running");
      }
    } else {
      // LOCAL SIMULATION PREVIEW
      const simScript = buildRunScript(scenarioId, createRunId());
      setScript(simScript);
      setElapsed(0);
      setPhase("running");
    }
  }, [currentStatus, mode, health, scenarioId]);

  // Handle Stopping / Cancelling a Run
  const stopRun = useCallback(async () => {
    if (mode === "live" && liveRunId) {
      try {
        await apiCancelRun(liveRunId);
      } catch (err) {
        console.warn("Cancel notice:", err);
      }
      if (sseCleanupRef.current) {
        sseCleanupRef.current();
        sseCleanupRef.current = null;
      }
    }
    setPhase("cancelled");
  }, [mode, liveRunId]);

  // Aggregate events for display
  const events = useMemo<GauntletEvent[]>(() => {
    if (mode === "live") {
      return liveEvents;
    }
    if (!script) {
      return [];
    }
    return script.schedule
      .filter((item) => item.at <= elapsed)
      .map((item) => item.event);
  }, [mode, liveEvents, script, elapsed]);

  const baselineEvents = useMemo(
    () => events.filter((event) => event.executionPath === "ungoverned"),
    [events],
  );

  const protectedEvents = useMemo(
    () => events.filter((event) => event.executionPath === "protected"),
    [events],
  );

  const summary = useMemo(() => {
    if (events.length === 0) return null;
    return summarizeRun(baselineEvents, protectedEvents);
  }, [events.length, baselineEvents, protectedEvents]);

  // Progress computation
  const progress = useMemo(() => {
    if (mode === "simulation") {
      return script ? Math.min(100, (elapsed / script.durationMs) * 100) : 0;
    }
    if (currentStatus === "completed") return 100;
    if (currentStatus === "running") {
      // Estimate live progress by event count (avg ~10 events per scenario)
      return Math.min(95, events.length * 9);
    }
    return 0;
  }, [mode, script, elapsed, currentStatus, events.length]);

  const activeRunId = mode === "live" ? liveRunId : script?.runId ?? null;

  return (
    <div className="flex flex-col gap-5">
      {/* Dynamic Mode Header Banner */}
      <div className="flex flex-col gap-3 rounded-2xl border border-line bg-surface/70 p-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <Badge
            tone={mode === "live" ? "brand" : "warning"}
            className="w-fit shrink-0"
          >
            {mode === "live" ? (
              <span className="flex items-center gap-1.5">
                <Radio className="h-3.5 w-3.5 text-safe animate-pulse" />
                Live Engine Connected
              </span>
            ) : (
              <span className="flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5" />
                Simulation Preview
              </span>
            )}
          </Badge>
          <p className="text-xs/5 text-muted sm:text-sm/6">
            {mode === "live"
              ? "Dual-path asynchronous execution streamed live from the FastAPI backend over SSE."
              : "Scripted timeline preview active. Run `cd backend; python -m uvicorn app.main:app` to engage live execution."}
          </p>
        </div>

        {/* Engine Toggle */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={() => setMode((prev) => (prev === "live" ? "simulation" : "live"))}
            disabled={currentStatus === "running"}
            className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-surface-2 px-3 py-1.5 text-xs font-mono text-dim transition-colors hover:border-brand/40 hover:text-foreground disabled:opacity-40"
          >
            <RefreshCw className="h-3 w-3" />
            Switch to {mode === "live" ? "Simulation" : "Live Backend"}
          </button>
        </div>
      </div>

      <ConsoleStatusBar
        runStatus={currentStatus}
        runId={activeRunId}
        health={health}
        isLiveMode={mode === "live"}
      />

      <RunControls
        scenarioId={scenarioId}
        onScenarioChange={setScenarioId}
        status={currentStatus}
        onRun={startRun}
        onStop={stopRun}
        progress={progress}
        elapsedMs={mode === "simulation" ? Math.min(elapsed, script?.durationMs ?? 0) : 0}
        durationMs={mode === "simulation" ? script?.durationMs ?? 0 : 0}
      />

      {scenario ? (
        <div className="rounded-2xl border border-line bg-surface/70 p-5">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="brand">Scenario {scenario.code}</Badge>
            <span className="text-sm font-semibold tracking-tight">
              {scenario.name}
            </span>
            <Badge tone="neutral" className="normal-case">
              {scenario.agentRole}
            </Badge>
          </div>
          <p className="mt-3 max-w-3xl text-sm/6 text-muted">
            {scenario.description}
          </p>
          <p className="mt-2 max-w-3xl text-xs/5 text-dim">
            <span className="text-safe">Expected under governance: </span>
            {scenario.expectedProtectedOutcome}
          </p>
        </div>
      ) : null}

      <div className="grid gap-5 xl:grid-cols-2">
        <AgentPanel
          variant="ungoverned"
          agentLabel="Ungoverned agent"
          roleLabel="path A · gemini → sandbox"
          events={baselineEvents}
          status={currentStatus}
        />
        <AgentPanel
          variant="protected"
          agentLabel="ArmorIQ-protected agent"
          roleLabel="path B · interceptor enforced"
          events={protectedEvents}
          status={currentStatus}
        />
      </div>

      <SummaryPanel summary={summary} status={currentStatus} />
    </div>
  );
}
