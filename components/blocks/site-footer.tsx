import Link from "next/link";
import { ShieldHalf } from "lucide-react";

const LINK_GROUPS = [
  {
    title: "Platform",
    links: [
      { label: "Threat model", href: "/#threat-model" },
      { label: "Architecture", href: "/#architecture" },
      { label: "Scenarios", href: "/#scenarios" },
      { label: "Authorization outcomes", href: "/#outcomes" },
    ],
  },
  {
    title: "Console",
    links: [
      { label: "Open dashboard", href: "/dashboard" },
      { label: "Sandbox tools", href: "/#architecture" },
      { label: "Role scopes", href: "/#architecture" },
    ],
  },
];

export function SiteFooter() {
  return (
    <footer className="border-t border-line bg-surface">
      <div className="mx-auto w-full max-w-screen-xl px-5 py-14 md:px-8">
        <div className="grid gap-10 md:grid-cols-[1.4fr_1fr_1fr]">
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2.5">
              <span className="grid h-9 w-9 place-items-center rounded-lg border border-brand/40 bg-brand/10 text-brand">
                <ShieldHalf className="h-5 w-5" />
              </span>
              <span className="text-lg font-bold tracking-tighter text-foreground">
                LLM<span className="text-brand">Shield</span>
              </span>
            </div>
            <p className="max-w-sm text-sm/6 text-muted">
              An interactive security testing platform for indirect prompt
              injection and runtime agent authorization. Every attack runs
              against synthetic data inside an isolated sandbox.
            </p>
          </div>

          {LINK_GROUPS.map((group) => (
            <div key={group.title} className="flex flex-col gap-3">
              <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-dim">
                {group.title}
              </span>
              <ul className="flex flex-col gap-2">
                {group.links.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-sm text-muted transition-colors hover:text-foreground"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col gap-3 border-t border-line pt-6 text-xs text-dim md:flex-row md:items-center md:justify-between">
          <p>
            Sandbox only. No production data, no real email transmission, no
            secrets committed.
          </p>
          <p className="font-mono">
            Telemetry schema v1 · events are never fabricated as live results
          </p>
        </div>
      </div>
    </footer>
  );
}
