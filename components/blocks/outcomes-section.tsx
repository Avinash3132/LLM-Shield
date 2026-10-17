import { Fingerprint, GaugeCircle, ShieldX, TimerOff } from "lucide-react";

import { Badge, type BadgeTone } from "@/components/ui/badge";
import { Section, SectionHeading } from "@/components/ui/section";
import { AUTH_OUTCOMES } from "@/lib/gauntlet/content";

const TONE_MAP: Record<string, BadgeTone> = {
  safe: "success",
  danger: "danger",
  warn: "warning",
  muted: "neutral",
};

const STATS = [
  {
    icon: ShieldX,
    title: "Denial ≠ outage",
    body: "A policy denial and a network timeout are recorded as different outcomes, because they require different operator responses.",
  },
  {
    icon: TimerOff,
    title: "Fail secure by default",
    body: "If authorization times out or the response is malformed, the protected tool is not executed and the result is left unresolved.",
  },
  {
    icon: Fingerprint,
    title: "Identity, scope, operation",
    body: "The interceptor resolves who is asking, for what tool, against which operation, and under which policy.",
  },
  {
    icon: GaugeCircle,
    title: "Verified health only",
    body: "The console reports ArmorIQ as live only after a real integration health check succeeds. Otherwise it stays unverified.",
  },
];

export function OutcomesSection() {
  return (
    <Section id="outcomes" className="scroll-mt-20">
      <SectionHeading
        eyebrow="Authorization outcomes"
        title={
          <>
            Six outcomes, because &quot;blocked&quot;{" "}
            <span className="text-gradient">is not one thing.</span>
          </>
        }
        description="The protected path never collapses distinct results into a single failure state. The interceptor classifies every decision and the UI renders it verbatim."
      />

      <div className="mt-14 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {AUTH_OUTCOMES.map((outcome) => (
          <div
            key={outcome.status}
            className="flex flex-col gap-3 rounded-2xl border border-line bg-surface/60 p-5"
          >
            <Badge tone={TONE_MAP[outcome.tone]}>{outcome.status}</Badge>
            <p className="text-sm/6 text-muted">{outcome.meaning}</p>
          </div>
        ))}
      </div>

      <div className="mt-14 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {STATS.map((stat) => (
          <div
            key={stat.title}
            className="flex flex-col gap-3 rounded-2xl border border-line bg-surface-2/50 p-5"
          >
            <stat.icon className="h-5 w-5 text-brand" />
            <h3 className="text-sm font-semibold tracking-tight">
              {stat.title}
            </h3>
            <p className="text-sm/6 text-muted">{stat.body}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}
