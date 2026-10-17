import { HeroSection } from "@/components/ui/hero-section-dark";

const PREVIEW_LIGHT =
  "https://coresg-normal.trae.ai/api/ide/v1/text_to_image?prompt=" +
  encodeURIComponent(
    "Light mode cybersecurity operations console, split screen two column layout, AI agent telemetry event log with green red amber status chips, clean minimal product UI screenshot, crisp typography, soft shadows, high fidelity",
  ) +
  "&image_size=landscape_16_9";

const PREVIEW_DARK =
  "https://coresg-normal.trae.ai/api/ide/v1/text_to_image?prompt=" +
  encodeURIComponent(
    "Dark mode cybersecurity operations console, split screen two column layout, AI agent telemetry event log with green red amber status chips, purple and magenta gradient glow, glassmorphism panels, monospace data, ultra detailed product UI screenshot, cinematic",
  ) +
  "&image_size=landscape_16_9";

function HeroSectionDemo() {
  return (
    <HeroSection
      title="Indirect prompt injection, demonstrated live"
      subtitle={{
        regular: "Prove your agent governance ",
        gradient: "under real adversarial pressure.",
      }}
      description="LLMShield fires the same attack at an ungoverned Gemini agent and an ArmorIQ-protected agent, then shows precisely where runtime authorization stops the damage."
      ctaText="Launch the console"
      ctaHref="/dashboard"
      bottomImage={{
        light: PREVIEW_LIGHT,
        dark: PREVIEW_DARK,
      }}
      gridOptions={{
        angle: 65,
        opacity: 0.4,
        cellSize: 50,
        lightLineColor: "#4a4a4a",
        darkLineColor: "#2a2a2a",
      }}
    />
  );
}

export { HeroSectionDemo };
