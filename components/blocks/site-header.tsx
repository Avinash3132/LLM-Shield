import Link from "next/link";
import { ArrowUpRight, ShieldHalf } from "lucide-react";

import { Badge, StatusDot } from "@/components/ui/badge";

const NAV = [
  { label: "Threat model", href: "/#threat-model" },
  { label: "Architecture", href: "/#architecture" },
  { label: "Scenarios", href: "/#scenarios" },
  { label: "Outcomes", href: "/#outcomes" },
];

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-line/80 bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 w-full max-w-screen-xl items-center justify-between gap-4 px-5 md:px-8">
        <Link href="/" className="group flex items-center gap-2.5">
          <span className="grid h-9 w-9 place-items-center rounded-lg border border-brand/40 bg-brand/10 text-brand transition-colors group-hover:bg-brand/20">
            <ShieldHalf className="h-5 w-5" />
          </span>
          <div className="flex flex-col leading-none">
            <span className="text-lg font-bold tracking-tighter text-foreground">
              LLM<span className="text-brand">Shield</span>
            </span>
            <span className="font-mono text-[9px] uppercase tracking-[0.1em] text-dim max-w-[140px] leading-tight sm:max-w-none">
              TEST • BREAK • MAKE AI SAFER
            </span>
          </div>
        </Link>

        <nav className="hidden items-center gap-7 lg:flex">
          {NAV.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="text-sm text-muted transition-colors hover:text-foreground"
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <Badge tone="brand" className="hidden sm:inline-flex">
            <StatusDot tone="brand" pulse />
            Dual-Execution Active
          </Badge>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 rounded-full border border-brand/40 bg-brand/10 px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-brand/20"
          >
            Launch console
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>
    </header>
  );
}
