/**
 * API client for the LLMShield FastAPI backend.
 *
 * Provides typed fetch wrappers for all REST endpoints
 * and an EventSource factory for SSE streaming.
 */

import type { GauntletEvent, RunStatus } from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api";

// ─────────── REST Helpers ───────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(`API ${response.status}: ${body}`);
  }
  return response.json() as Promise<T>;
}

// ─────────── Health ───────────

export interface HealthStatus {
  status: string;
  app_name: string;
  environment: string;
  gemini: { configured: boolean; model: string };
  armoriq: {
    configured: boolean;
    endpoint: string;
    agent_id: string;
    environment: string;
  };
  sandboxes: {
    file_vault_ready: boolean;
    crm_ready: boolean;
    email_outbox_ready: boolean;
  };
}

export function fetchHealth(): Promise<HealthStatus> {
  return apiFetch("/health");
}

// ─────────── Scenarios ───────────

export interface ScenarioDTO {
  id: string;
  code: string;
  name: string;
  summary: string;
  description: string;
  agentRole: string;
  initialPrompt: string;
  contextFiles: string[];
  targetSecretPath: string | null;
  expectedBehavior: string;
  expectedProtectedOutcome: string;
  tags: string[];
}

export function fetchScenarios(): Promise<ScenarioDTO[]> {
  return apiFetch("/scenarios");
}

// ─────────── Runs ───────────

export interface CreateRunResponse {
  run_id: string;
  scenario_id: string;
  status: string;
  started_at?: string;
}

export function createRun(scenarioId: string): Promise<CreateRunResponse> {
  return apiFetch("/runs", {
    method: "POST",
    body: JSON.stringify({ scenario_id: scenarioId }),
  });
}

export interface RunStatusResponse {
  run_id: string;
  scenario_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  comparison?: Record<string, unknown>;
}

export function fetchRunStatus(runId: string): Promise<RunStatusResponse> {
  return apiFetch(`/runs/${runId}`);
}

export function fetchRunResults(
  runId: string
): Promise<Record<string, unknown>> {
  return apiFetch(`/runs/${runId}/results`);
}

export function cancelRun(
  runId: string
): Promise<{ success: boolean; run_id: string; status: string }> {
  return apiFetch(`/runs/${runId}/cancel`, { method: "POST" });
}

// ─────────── SSE Streaming ───────────

export interface SSEStreamOptions {
  onEvent: (event: GauntletEvent) => void;
  onComplete?: (status: string) => void;
  onError?: (error: Error) => void;
}

/**
 * Opens an EventSource connection to the backend SSE stream for the given run.
 * Returns a cleanup function to close the connection.
 */
export function streamRunEvents(
  runId: string,
  options: SSEStreamOptions
): () => void {
  const url = `${API_BASE}/runs/${runId}/events`;
  const source = new EventSource(url);

  source.onmessage = (message) => {
    try {
      const event: GauntletEvent = JSON.parse(message.data);
      options.onEvent(event);
    } catch (err) {
      console.error("[SSE] Failed to parse event:", err);
    }
  };

  source.addEventListener("run_complete", (message) => {
    try {
      const data = JSON.parse((message as MessageEvent).data);
      options.onComplete?.(data.status ?? "completed");
    } catch {
      options.onComplete?.("completed");
    }
    source.close();
  });

  source.onerror = () => {
    options.onError?.(new Error("SSE connection lost"));
    source.close();
  };

  return () => {
    source.close();
  };
}
