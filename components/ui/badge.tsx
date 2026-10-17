import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export type BadgeTone =
  | "neutral"
  | "info"
  | "success"
  | "warning"
  | "danger"
  | "brand";

const TONE_CLASSES: Record<BadgeTone, string> = {
  neutral: "border-line bg-surface-2 text-muted",
  info: "border-info/30 bg-info/10 text-info",
  success: "border-safe/30 bg-safe/10 text-safe",
  warning: "border-warn/30 bg-warn/10 text-warn",
  danger: "border-danger/30 bg-danger/10 text-danger",
  brand: "border-brand/30 bg-brand/10 text-brand",
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
}

export function Badge({ tone = "neutral", className, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 font-mono text-[11px] font-medium uppercase tracking-wider",
        TONE_CLASSES[tone],
        className,
      )}
      {...props}
    />
  );
}

interface StatusDotProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
  pulse?: boolean;
}

const DOT_CLASSES: Record<BadgeTone, string> = {
  neutral: "bg-dim",
  info: "bg-info",
  success: "bg-safe",
  warning: "bg-warn",
  danger: "bg-danger",
  brand: "bg-brand",
};

export function StatusDot({
  tone = "neutral",
  pulse = false,
  className,
  ...props
}: StatusDotProps) {
  return (
    <span
      className={cn(
        "inline-block h-2 w-2 shrink-0 rounded-full",
        DOT_CLASSES[tone],
        pulse && "animate-pulse",
        className,
      )}
      {...props}
    />
  );
}
