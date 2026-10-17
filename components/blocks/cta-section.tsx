import Link from "next/link";
import { ArrowRight, Terminal } from "lucide-react";

export function CtaSection() {
  return (
    <div className="mx-auto w-full max-w-screen-xl px-5 pb-24 md:px-8">
      <div className="relative overflow-hidden rounded-3xl border border-line bg-surface px-6 py-16 text-center md:px-16">
        <div className="surface-grid pointer-events-none absolute inset-0 opacity-40" />
        <div className="pointer-events-none absolute -top-24 left-1/2 h-64 w-[36rem] -translate-x-1/2 rounded-full bg-brand/20 blur-3xl" />
        <div className="relative flex flex-col items-center gap-6">
          <span className="inline-flex items-center gap-2 rounded-full border border-line bg-surface-2 px-3 py-1 font-mono text-[11px] uppercase tracking-[0.18em] text-muted">
            <Terminal className="h-3 w-3" />
            ready to replay
          </span>
          <h2 className="max-w-2xl text-3xl font-semibold tracking-tight text-balance md:text-5xl">
            Watch governance hold — or{" "}
            <span className="text-gradient">watch it fail loudly.</span>
          </h2>
          <p className="max-w-xl text-base/7 text-muted">
            Pick a scenario, launch both agents, and read the event stream
            yourself. The interesting part is not the answer. It&apos;s the
            boundary. Powered by LLMShield.
          </p>
          <Link
            href="/dashboard"
            className="group inline-flex items-center gap-2 rounded-full bg-foreground px-6 py-3 text-sm font-semibold text-background transition-transform hover:-translate-y-0.5"
          >
            Launch the console
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Link>
        </div>
      </div>
    </div>
  );
}
