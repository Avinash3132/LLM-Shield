import {
  ArrowRight,
  BrainCircuit,
  Database,
  FolderLock,
  Mail,
  ShieldCheck,
  Users,
  Zap,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Eyebrow, Section, SectionHeading } from "@/components/ui/section";
import { ROLE_SCOPES, SANDBOX_TOOLS } from "@/lib/gauntlet/content";

const PATH_A = [
  { label: "Gemini agent", icon: BrainCircuit },
  { label: "Sandbox tool adapter", icon: Zap },
  { label: "Mock MCP services", icon: Database },
];

const PATH_B = [
  { label: "Gemini agent", icon: BrainCircuit },
  { label: "Authorization interceptor", icon: ShieldCheck },
  { label: "ArmorIQ authorization", icon: FolderLock },
  { label: "Sandbox tool adapter", icon: Database },
];

const TOOL_ICONS = {
  "file_vault.read": FolderLock,
  "file_vault.list": FolderLock,
  "crm.read_record": Users,
  "crm.update_record": Users,
  "email.draft": Mail,
  "email.send": Mail,
} as const;

export function ArchitectureSection() {
  return (
    <Section id="architecture" className="scroll-mt-20">
      <SectionHeading
        eyebrow="Architecture"
        title={
          <>
            One test case. Two isolated execution paths.{" "}
            <span className="text-gradient">One hard boundary.</span>
          </>
        }
        description="Every run fans out into two agents with equivalent inputs but separate state. Neither path can observe the other, and the protected path has no route to a tool that skips the interceptor."
      />

      <div className="mt-14 grid gap-6 lg:grid-cols-2">
        <div className="flex flex-col gap-5 rounded-2xl border border-danger/25 bg-surface/60 p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold tracking-tight">
              Path A — Ungoverned
            </h3>
            <Badge tone="danger">no interception</Badge>
          </div>
          <p className="text-sm/6 text-muted">
            The model talks straight to the sandbox. Whatever the agent is
            persuaded to request is what gets executed, and the run log records
            the true outcome.
          </p>
          <ol className="flex flex-col gap-2">
            {PATH_A.map((step, index) => (
              <li key={step.label} className="flex items-center gap-3">
                <span className="grid h-9 w-9 place-items-center rounded-lg border border-line bg-surface-2 text-muted">
                  <step.icon className="h-4 w-4" />
                </span>
                <span className="text-sm">{step.label}</span>
                {index < PATH_A.length - 1 ? (
                  <ArrowRight className="ml-auto h-3.5 w-3.5 text-dim" />
                ) : null}
              </li>
            ))}
          </ol>
        </div>

        <div className="flex flex-col gap-5 rounded-2xl border border-safe/25 bg-surface/60 p-6 glow-ring">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold tracking-tight">
              Path B — ArmorIQ-protected
            </h3>
            <Badge tone="success">fail-secure</Badge>
          </div>
          <p className="text-sm/6 text-muted">
            Every protected tool invocation passes through the interceptor,
            which resolves the agent identity, scope, and requested operation
            before the sandbox adapter is even reachable.
          </p>
          <ol className="flex flex-col gap-2">
            {PATH_B.map((step, index) => (
              <li key={step.label} className="flex items-center gap-3">
                <span className="grid h-9 w-9 place-items-center rounded-lg border border-line bg-surface-2 text-safe">
                  <step.icon className="h-4 w-4" />
                </span>
                <span className="text-sm">
                  {step.label}
                  {index === PATH_B.length - 1 ? (
                    <span className="ml-2 font-mono text-[11px] text-dim">
                      only if authorized
                    </span>
                  ) : null}
                </span>
                {index < PATH_B.length - 1 ? (
                  <ArrowRight className="ml-auto h-3.5 w-3.5 text-dim" />
                ) : null}
              </li>
            ))}
          </ol>
        </div>
      </div>

      <div className="mt-14 grid gap-6 lg:grid-cols-[1.1fr_1fr]">
        <div className="rounded-2xl border border-line bg-surface/60 p-6">
          <Eyebrow>Mock MCP services</Eyebrow>
          <p className="mt-4 text-sm/6 text-muted">
            Three isolated sandbox surfaces with strict schemas, path traversal
            prevention, and fixed destinations. No shell execution, no
            unrestricted filesystem access, no real email.
          </p>
          <ul className="mt-5 grid gap-2 sm:grid-cols-2">
            {SANDBOX_TOOLS.map((tool) => {
              const Icon = TOOL_ICONS[tool.name as keyof typeof TOOL_ICONS];
              return (
                <li
                  key={tool.name}
                  className="flex items-start gap-3 rounded-xl border border-line bg-surface-2/60 p-3"
                >
                  <Icon className="mt-0.5 h-4 w-4 shrink-0 text-brand" />
                  <div>
                    <p className="font-mono text-xs text-foreground">
                      {tool.name}
                    </p>
                    <p className="text-xs/5 text-dim">{tool.description}</p>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>

        <div className="rounded-2xl border border-line bg-surface/60 p-6">
          <Eyebrow>Role scopes</Eyebrow>
          <p className="mt-4 text-sm/6 text-muted">
            Permissions are enforced at the tool execution boundary, never by
            the agent&apos;s system prompt.
          </p>
          <div className="mt-5 flex flex-col divide-y divide-line">
            {ROLE_SCOPES.map((scope) => (
              <div key={scope.role} className="flex flex-col gap-2 py-3">
                <span className="text-sm font-medium">{scope.role}</span>
                <div className="flex flex-wrap gap-1.5">
                  {scope.allowed.map((item) => (
                    <Badge key={item} tone="success" className="normal-case">
                      {item}
                    </Badge>
                  ))}
                  {scope.forbidden.map((item) => (
                    <Badge key={item} tone="danger" className="normal-case">
                      {item}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Section>
  );
}
