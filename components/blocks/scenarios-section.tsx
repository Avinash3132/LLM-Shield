import Link from "next/link";
import { ArrowUpRight, Target } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Section, SectionHeading } from "@/components/ui/section";
import { SCENARIOS } from "@/lib/gauntlet/content";

export function ScenariosSection() {
  return (
    <Section id="scenarios" className="scroll-mt-20">
      <SectionHeading
        eyebrow="Adversarial test suite"
        title={
          <>
            Five versioned scenarios that are{" "}
            <span className="text-gradient">replayed, not staged.</span>
          </>
        }
        description="Each scenario ships with the same inputs for both paths, so the comparison is between enforcement layers — not between two different prompts."
      />

      <div className="mt-14 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {SCENARIOS.map((scenario) => (
          <article
            key={scenario.id}
            className="group flex flex-col gap-4 rounded-2xl border border-line bg-surface/60 p-6 transition-colors hover:border-brand/40 hover:bg-surface-2/70"
          >
            <div className="flex items-center justify-between">
              <span className="grid h-9 w-9 place-items-center rounded-lg border border-brand/30 bg-brand/10 font-mono text-sm font-semibold text-brand">
                {scenario.code}
              </span>
              <Badge tone="neutral" className="normal-case">
                {scenario.agentRole}
              </Badge>
            </div>

            <div className="flex flex-col gap-2">
              <h3 className="text-base font-semibold tracking-tight">
                {scenario.name}
              </h3>
              <p className="text-sm/6 text-muted">{scenario.summary}</p>
            </div>

            <div className="flex flex-col gap-2 rounded-xl border border-line bg-surface-2/60 p-3">
              <span className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-dim">
                <Target className="h-3 w-3" />
                attacker objective
              </span>
              <p className="font-mono text-xs/5 text-muted">
                {scenario.objective}
              </p>
            </div>

            <p className="text-xs/5 text-dim">
              <span className="text-safe">Expected under governance: </span>
              {scenario.expectedProtectedOutcome}
            </p>

            <div className="mt-auto flex flex-wrap gap-1.5 pt-2">
              {scenario.tags.map((tag) => (
                <Badge key={tag} tone="brand" className="normal-case">
                  {tag}
                </Badge>
              ))}
            </div>
          </article>
        ))}

        <Link
          href="/dashboard"
          className="group flex flex-col justify-between gap-6 rounded-2xl border border-dashed border-brand/40 bg-gradient-to-br from-brand/10 via-surface/60 to-surface/60 p-6 transition-colors hover:from-brand/20"
        >
          <div className="flex flex-col gap-3">
            <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-brand">
              Run them yourself
            </span>
            <h3 className="text-lg font-semibold tracking-tight">
              Open the console and replay any scenario side by side.
            </h3>
            <p className="text-sm/6 text-muted">
              Select a scenario, start a run, and watch both execution paths
              stream their events in real time.
            </p>
          </div>
          <span className="inline-flex items-center gap-1.5 text-sm font-medium text-brand">
            Launch dashboard
            <ArrowUpRight className="h-4 w-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
          </span>
        </Link>
      </div>
    </Section>
  );
}
