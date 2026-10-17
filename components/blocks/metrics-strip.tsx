import { METRICS } from "@/lib/gauntlet/content";

export function MetricsStrip() {
  return (
    <div className="mx-auto w-full max-w-screen-xl px-5 md:px-8">
      <dl className="grid grid-cols-1 divide-y divide-line overflow-hidden rounded-2xl border border-line bg-surface/60 sm:grid-cols-2 sm:divide-y-0 sm:divide-x md:grid-cols-4">
        {METRICS.map((metric) => (
          <div key={metric.label} className="flex flex-col gap-2 p-6">
            <dt className="font-mono text-[11px] uppercase tracking-[0.18em] text-dim">
              {metric.label}
            </dt>
            <dd className="text-4xl font-semibold tracking-tight text-gradient">
              {metric.value}
            </dd>
            <dd className="text-sm/6 text-muted">{metric.detail}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
