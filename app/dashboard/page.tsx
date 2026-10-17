import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { SiteFooter } from "@/components/blocks/site-footer";
import { SiteHeader } from "@/components/blocks/site-header";
import { GauntletConsole } from "@/components/dashboard/gauntlet-console";

export const metadata: Metadata = {
  title: "Console",
  description:
    "Run an adversarial scenario through the ungoverned and ArmorIQ-protected execution paths side by side.",
};

export default function DashboardPage() {
  return (
    <>
      <SiteHeader />
      <main className="flex-1">
        <div className="mx-auto w-full max-w-screen-xl px-5 py-10 md:px-8">
          <div className="mb-8 flex flex-col gap-3">
            <Link
              href="/"
              className="inline-flex w-fit items-center gap-1.5 text-sm text-muted transition-colors hover:text-foreground"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Back to overview
            </Link>
            <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
              Dual-execution console
            </h1>
            <p className="max-w-3xl text-sm/6 text-muted">
              Run one adversarial scenario through both execution paths at once
              and read the resulting event streams side by side.
            </p>
          </div>

          <GauntletConsole />
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
