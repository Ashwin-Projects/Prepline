import type { ReactNode } from "react";
import { AlertTriangle, CheckCircle2, CircleHelp, XCircle } from "lucide-react";
import type { ConfidenceLevel } from "../lib/confidence";

export function Card({ title, subtitle, children, className = "", testId }: {
  title?: ReactNode;
  subtitle?: ReactNode;
  children: ReactNode;
  className?: string;
  testId?: string;
}) {
  return (
    <section className={`rounded-lg border border-line bg-surface p-4 ${className}`} data-testid={testId}>
      {title && (
        <header className="mb-3">
          <h2 className="text-[15px] font-semibold text-ink">{title}</h2>
          {subtitle && <p className="text-[13px] text-ink-3">{subtitle}</p>}
        </header>
      )}
      {children}
    </section>
  );
}

export function PageHeader({ title, lede, actions }: { title: string; lede?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div className="min-w-0">
        <h1 className="text-2xl font-semibold tracking-tight text-ink">{title}</h1>
        {lede && <p className="mt-1 max-w-3xl text-[14px] text-ink-2">{lede}</p>}
      </div>
      {actions}
    </div>
  );
}

const BADGE_STYLES: Record<ConfidenceLevel, string> = {
  High: "bg-good-soft text-good",
  Medium: "bg-warn-soft text-warn",
  Low: "bg-warn-soft text-warn",
  "Insufficient data": "bg-surface-2 text-ink-2",
};

export function ConfidenceBadge({ level }: { level: ConfidenceLevel }) {
  const Icon = level === "High" ? CheckCircle2 : level === "Insufficient data" ? CircleHelp : AlertTriangle;
  return (
    <span
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-0.5 text-[13px] font-medium ${BADGE_STYLES[level]}`}
      data-testid="confidence-badge"
    >
      <Icon size={14} aria-hidden="true" />
      {level === "Insufficient data" ? level : `${level} confidence`}
    </span>
  );
}

export function GateChip({ passed, count, min }: { passed: boolean; count: number | null; min: number }) {
  return (
    <span
      className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2 py-0.5 text-[12px] font-medium ${
        passed ? "bg-good-soft text-good" : "bg-warn-soft text-warn"
      }`}
    >
      {passed ? <CheckCircle2 size={13} aria-hidden="true" /> : <XCircle size={13} aria-hidden="true" />}
      {passed ? "Gate passed" : "Gate not met"} · {count ?? "—"}/{min}
    </span>
  );
}

// Skeleton in the shape of a card grid, so content does not jump when data arrives.
export function Loading({ label = "Loading" }: { label?: string }) {
  return (
    <div role="status" aria-label={`${label}…`} className="grid grid-cols-12 gap-4">
      {["col-span-5", "col-span-7", "col-span-6", "col-span-6"].map((span, i) => (
        <div
          key={i}
          className={`${span} h-40 animate-pulse rounded-lg border border-line bg-surface motion-reduce:animate-none max-[1100px]:col-span-12`}
        />
      ))}
      <span className="sr-only">{label}…</span>
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div role="alert" className="rounded-lg border border-line bg-surface p-4 text-[14px]">
      <p className="font-medium text-bad">Could not load data from the API.</p>
      <p className="mt-1 text-ink-2">
        {message}. Is the backend running on port 8000? Start everything with{" "}
        <code className="font-mono">scripts/start_demo.ps1</code>.
      </p>
    </div>
  );
}

export function InsufficientState({ company, role, count, raw, min }: {
  company: string;
  role: string;
  count: number;
  raw: number;
  min: number;
}) {
  return (
    <div
      className="rounded-lg border border-dashed border-line bg-surface-2 p-4"
      data-testid="insufficient-state"
      role="status"
    >
      <p className="flex items-center gap-2 text-[13px] font-semibold uppercase tracking-wide text-ink-2">
        <CircleHelp size={15} aria-hidden="true" /> Insufficient data
      </p>
      <p className="mt-1.5 text-[14px] text-ink-2">
        {company} {role} has {count} usable interview report{count === 1 ? "" : "s"} ({raw} collected); scoring needs
        at least {min}. No alignment score is shown rather than one built on too few reports.
      </p>
    </div>
  );
}

export function NoResultsState({ company, role }: { company: string; role: string }) {
  return (
    <div className="rounded-lg border border-dashed border-line bg-surface-2 p-4" data-testid="no-results-state" role="status">
      <p className="text-[13px] font-semibold uppercase tracking-wide text-ink-2">No saved results yet</p>
      <p className="mt-1.5 text-[14px] text-ink-2">
        {company} {role} is configured, but the pipeline has not been run for it. Run{" "}
        <code className="font-mono text-[13px]">python evaluation/run_all_targets.py</code>.
      </p>
    </div>
  );
}

export function Stat({ label, value, hint }: { label: string; value: ReactNode; hint?: ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className="text-[12px] font-medium uppercase tracking-wide text-ink-3">{label}</dt>
      <dd className="tabular mt-0.5 text-[15px] font-medium text-ink [overflow-wrap:anywhere]">{value}</dd>
      {hint && <dd className="text-[12px] text-ink-3 [overflow-wrap:anywhere]">{hint}</dd>}
    </div>
  );
}
