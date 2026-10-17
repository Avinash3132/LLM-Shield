import { ArchitectureSection } from "@/components/blocks/architecture-section";
import { CtaSection } from "@/components/blocks/cta-section";
import { HeroSectionDemo } from "@/components/blocks/hero-section-demo";
import { MetricsStrip } from "@/components/blocks/metrics-strip";
import { OutcomesSection } from "@/components/blocks/outcomes-section";
import { ScenariosSection } from "@/components/blocks/scenarios-section";
import { SiteFooter } from "@/components/blocks/site-footer";
import { SiteHeader } from "@/components/blocks/site-header";
import { TelemetrySection } from "@/components/blocks/telemetry-section";
import { ThreatModelSection } from "@/components/blocks/threat-model-section";

export default function Home() {
  return (
    <>
      <SiteHeader />
      <main className="flex-1">
        <HeroSectionDemo />
        <div className="relative z-10 -mt-16 md:-mt-24">
          <MetricsStrip />
        </div>
        <ThreatModelSection />
        <ArchitectureSection />
        <ScenariosSection />
        <OutcomesSection />
        <TelemetrySection />
        <CtaSection />
      </main>
      <SiteFooter />
    </>
  );
}
