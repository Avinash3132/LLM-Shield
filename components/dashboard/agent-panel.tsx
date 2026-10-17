"use client";

import { useEffect, useRef } from "react";
import { Bot, ShieldCheck, Terminal } from "lucide-react";

import { EventRow } from "@/components/dashboard/event-row";
import { Badge, StatusDot } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { GauntletEvent, RunStatus } from "@/lib/gauntlet/types";

interface AgentPanelProps {
  variant: "ungoverned" | "protected";
  agentLabel: string;
  roleLabel: string;
  events: GauntletEvent[];
  status: RunStatus;
}

const VARIANT = {
  ungoverned: {
    Icon: Bot,
    accent: "text-danger",
    ring: "border-danger/25",
    glow: "bg-danger/10",
    runningTone: "danger" as const,
  },
  protected: {
    Icon: ShieldCheck,
    accent: "text-safe",
    ring: "border-safe/30",
    glow: "bg-safe/10",
    runningTone: "success" as const,
  },
};

export function AgentPanel({
  variant,
  agentLabel,
  roleLabel,
  events,
  status,
}: AgentPanelProps) {
  const config = VARIANT[variant];
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const node = scrollRef.current;
    if (node) {
      node.scrollTop = node.scrollHeight;
    }
  }, [events.length]);

  return (
    <section
      className={cn(
        "flex min-h-[26rem] flex-col overflow-hidden rounded-2xl border bg-surface/70",
        config.ring,
      )}
      aria-label={agentLabel}
    >
      <header className="flex items-center justify-between gap-3 border-b border-line bg-surface-2/70 px-4 py-3">
        <div className="flex items-center gap-3">
          <span
            className={cn(
              "grid h-8 w-8 place-items-center rounded-lg border border-line",
              config.glow,
              config.accent,
            )}
          >
            <config.Icon className="h-4 w-4" />
          </span>
          <div className="leading-tight">
            <p className="text-sm font-semibold tracking-tight">
              {agentLabel}
            </p>
            <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-dim">
              {roleLabel}
            </p>
          </div>
        </div>
        <Badge tone={status === "running" ? config.runningTone : "neutral"}>
          <StatusDot
            tone={status === "running" ? config.runningTone : "neutral"}
            pulse={status === "running"}
          />
          {events.length} events
        </Badge>
      </header>

      <div
        ref={scrollRef}
        className="thin-scroll flex-1 overflow-y-auto px-2 py-2"
      >
        {events.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-2 py-16 text-center">
            <Terminal className="h-5 w-5 text-dim" />
            <p className="text-sm text-muted">
              {status === "running"
                ? "Streaming events…"
                : "No events yet. Start a run to stream this path."}
            </p>
          </div>
        ) : (
          <ul className="flex flex-col divide-y divide-line/60">
            {events.map((event) => (
              <EventRow key={event.eventId} event={event} />
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
