import { motion, useTransform, type MotionValue } from "motion/react";
import { GateChip } from "../../components/ui";
import type { EvidenceRow } from "../data";

// One tick per collected report. Ticks arrive in order, then reports with no usable question fade back.
function Tick({ index, raw, usable, progress }: { index: number; raw: number; usable: number | null; progress: MotionValue<number> }) {
  const start = 0.05 + (index / Math.max(raw, 1)) * 0.35;
  const arrive = useTransform(progress, [start, start + 0.08], [0, 1], { clamp: true });
  const filtered = usable !== null && index >= usable;
  const dim = useTransform(progress, [0.5, 0.65], [1, filtered ? 0.22 : 1], { clamp: true });
  const opacity = useTransform([arrive, dim], ([a, d]: number[]) => a * d);
  const transform = useTransform(arrive, (a) => `scaleY(${0.35 + 0.65 * a})`);
  return (
    <motion.span
      style={{ opacity, transform }}
      className={`h-full flex-1 origin-bottom rounded-[1px] ${filtered ? "bg-ink-3" : "bg-primary"}`}
    />
  );
}

export function EvidenceScene({ rows, progress }: { rows: EvidenceRow[]; progress: MotionValue<number> }) {
  const scale = Math.max(...rows.map((r) => Math.max(r.raw, r.min)), 1) + 2;
  const min = rows[0]?.min ?? 0;
  const gate = useTransform(progress, [0.65, 0.8], [0, 1], { clamp: true });
  const gateLine = useTransform(gate, (g) => `scaleY(${g})`);
  const chips = useTransform(progress, [0.78, 0.9], [0, 1], { clamp: true });
  return (
    <div className="relative w-full">
      <ol className="space-y-7">
        {rows.map((r) => (
          <li key={r.id} data-testid={`evidence-row-${r.id}`}>
            <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
              <span className="text-[15px] font-medium text-ink">{r.label}</span>
              <span className="tabular text-[13px] text-ink-3">
                {r.raw} collected → {r.usable ?? "—"} usable
              </span>
            </div>
            <div className="relative mt-2 h-9">
              <div className="flex h-full gap-[3px]" style={{ width: `${(r.raw / scale) * 100}%` }}>
                {Array.from({ length: r.raw }, (_, i) => (
                  <Tick key={i} index={i} raw={r.raw} usable={r.usable} progress={progress} />
                ))}
              </div>
              <motion.div
                style={{ left: `${(r.min / scale) * 100}%`, transform: gateLine }}
                className="pointer-events-none absolute -inset-y-1.5 w-0 origin-top border-l-2 border-dashed border-warn"
              />
            </div>
            <motion.div style={{ opacity: chips }} className="mt-2">
              <GateChip passed={r.passed} count={r.usable} min={r.min} />
            </motion.div>
          </li>
        ))}
      </ol>
      <motion.p style={{ opacity: gate }} className="mt-6 flex items-center gap-2 text-[13px] text-ink-3">
        <span className="h-3.5 w-0 border-l-2 border-dashed border-warn" aria-hidden="true" />
        {min}-report density gate: a company is scored only if its usable reports reach this line.
      </motion.p>
    </div>
  );
}
