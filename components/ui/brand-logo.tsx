import { cn } from "@/lib/utils";

export function BrandLogo({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 400 400"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("h-full w-full", className)}
    >
      <defs>
        <linearGradient id="shield-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#a855f7" />
          <stop offset="100%" stopColor="#6366f1" />
        </linearGradient>
        <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="5" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>
      
      {/* Outer rounded box */}
      <rect x="50" y="50" width="300" height="300" rx="60" fill="#000" stroke="#a855f7" strokeWidth="8" />
      
      {/* The Shield */}
      <path
        d="M200 80C200 80 120 100 120 160C120 240 200 320 200 320C200 320 280 240 280 160C280 100 200 80 200 80Z"
        fill="url(#shield-grad)"
        fillOpacity="0.2"
        stroke="url(#shield-grad)"
        strokeWidth="12"
      />
      
      {/* Vertical Lightning Bolt Divider */}
      <path
        d="M200 80L190 200H210L200 320"
        stroke="#fff"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
        filter="url(#glow)"
      />
      
      {/* Brain/Circuit Patterns (Simplified representation) */}
      <circle cx="165" cy="180" r="25" stroke="#a855f7" strokeWidth="4" opacity="0.6" />
      <circle cx="235" cy="180" r="25" stroke="#a855f7" strokeWidth="4" opacity="0.6" />
      <path d="M165 180L145 210" stroke="#a855f7" strokeWidth="3" opacity="0.6" />
      <path d="M235 180L255 210" stroke="#a855f7" strokeWidth="3" opacity="0.6" />
      
      {/* The Orbiting Ring */}
      <ellipse
        cx="200"
        cy="200"
        rx="150"
        ry="40"
        stroke="#a855f7"
        strokeWidth="10"
        transform="rotate(-15 200 200)"
        strokeLinecap="round"
        opacity="0.8"
      />
    </svg>
  );
}
