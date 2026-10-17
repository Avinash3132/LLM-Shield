import { CheckCircle2, CircleDashed, Radio, ShieldAlert, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Section, SectionHeading } from "@/components/ui/section";

const LAYERS = [
  {
    icon: CircleDashed,
    label: "Model-proposed action",
    body: "The agent asking for a tool call. A proposal proves intent and nothing more.",
    tone: "neutral" as const,
  },
  {
    icon: ShieldAlert,
    label: "Interceptor decision",
    body: "Schema validation, identity resolution, and scope resolution at the boundary.",
    tone: "warning" as const,
  },
  {
    icon: Radio,
    label: "Remote authorization result",
    body: "The actual answer from the authorization layer, including its policy identifier when provided.",
    tone: "brand" as const,
  },
  {
    icon: ShieldCheck,
    label: "Actual tool execution",
    body: "Whether the sandbox tool genuinely ran, and what it touched.",
    tone: "info" as const,
  },
  {
    icon: CheckCircle2,
    label: "Final security outcome",
    body: "Contained, mitigated, or unresolved — derived from observed events, never asserted.",
    tone: "success" as const,
  },
];

const TONE_BORDER = {
  neutral: "border-line",
  warning: "border-warn/30",
  brand: "border-brand/30",
  info: "border-info/30",
  success: "border-safe/30",
} as const;

export function TelemetrySection() {
  return (
    <Section>
      <div className="grid gap-14 lg:grid-cols-[0.9fr_1.1fr]">
        <SectionHeading
          eyebrow="Honest telemetry"
          title={
            <>
              A proposal is never rendered as{" "}
              <span className="text-gradient">an execution.</span>
            </>
          }
          description="The dashboard separates five layers of truth for every tool call. Nothing is inferred upward into a success state, and no simulated result is ever presented as a live authorization decision."
        />

        <div className="flex flex-col gap-3">
          {LAYERS.map((layer, index) => (
            <div
              key={layer.label}
              className={`flex items-start gap-4 rounded-2xl border bg-surface/60 p-5 ${TONE_BORDER[layer.tone]}`}
            >
              <div className="flex flex-col items-center gap-2">
                <span className="grid h-9 w-9 place-items-center rounded-lg border border-line bg-surface-2">
                  <layer.icon className="h-4 w-4 text-foreground" />
                </span>
                {index < LAYERS.length - 1 ? (
                  <span className="h-6 w-px bg-line" />
                ) : null}
              </div>
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[11px] text-dim">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <h3 className="text-sm font-semibold tracking-tight">
                    {layer.label}
                  </h3>
                  <Badge tone={layer.tone} className="ml-auto">
                    layer
                  </Badge>
                </div>
                <p className="text-sm/6 text-muted">{layer.body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Section>
  );
}
