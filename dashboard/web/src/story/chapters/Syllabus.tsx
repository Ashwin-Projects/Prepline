import { useMemo } from "react";
import { motion, useTransform, type MotionValue } from "motion/react";
import { seeded } from "../data";

const COLS = 5;

interface CardPose {
  x: number; // cqw
  y: number; // cqh
  r: number; // deg
}

// One course card: scattered loose pages at the start, filed into a catalogue grid by the end.
function CourseCard({ code, from, to, progress, delay }: {
  code: string;
  from: CardPose;
  to: CardPose;
  progress: MotionValue<number>;
  delay: number;
}) {
  const t = useTransform(progress, [0.05 + delay, 0.55 + delay], [0, 1], { clamp: true });
  const transform = useTransform(t, (v) => {
    const e = 1 - Math.pow(1 - v, 3);
    const x = from.x + (to.x - from.x) * e;
    const y = from.y + (to.y - from.y) * e;
    const r = from.r + (to.r - from.r) * e;
    return `translate(${x}cqw, ${y}cqh) rotate(${r}deg)`;
  });
  const kind = code.at(-1);
  return (
    <motion.div
      style={{ transform }}
      className={`absolute top-0 left-0 flex h-[10cqh] w-[17cqw] items-center justify-center rounded-[3px] border font-mono text-[max(2.1cqw,8.5px)] tracking-tight ${
        kind === "P" ? "border-primary/30 bg-primary-soft text-primary" : kind === "E" ? "border-line bg-surface-2 text-ink" : "border-line bg-surface text-ink"
      }`}
    >
      {code}
    </motion.div>
  );
}

export function SyllabusScene({ codes, progress }: { codes: string[]; progress: MotionValue<number> }) {
  const poses = useMemo(() => {
    const rand = seeded(20261024);
    return codes.map((_, i) => {
      const from = { x: rand() * 83, y: rand() * 88, r: (rand() - 0.5) * 28 };
      const to = { x: 2 + (i % COLS) * 19.6, y: 4 + Math.floor(i / COLS) * 14.5, r: 0 };
      return { from, to };
    });
  }, [codes]);
  const frame = useTransform(progress, [0.7, 0.9], [0, 1]);
  return (
    <div data-scene className="relative aspect-[4/3] w-full [container-type:size]">
      {codes.map((code, i) => (
        <CourseCard key={code} code={code} {...poses[i]} progress={progress} delay={(i / codes.length) * 0.2} />
      ))}
      <motion.div
        style={{ opacity: frame }}
        className="pointer-events-none absolute -inset-[1.5cqw] rounded-md border border-ink/25"
      />
      <motion.p
        style={{ opacity: frame }}
        className="absolute -bottom-[1.5cqw] left-1/2 -translate-x-1/2 translate-y-1/2 bg-bg px-3 font-display text-[15px] whitespace-nowrap text-ink-2 italic"
      >
        one combined syllabus
      </motion.p>
    </div>
  );
}

export function SyllabusLegend() {
  return (
    <p className="mt-6 flex flex-wrap gap-x-5 gap-y-1 text-[13px] text-ink-3">
      <span className="inline-flex items-center gap-1.5">
        <span className="size-2.5 rounded-[2px] border border-line bg-surface" aria-hidden="true" /> Theory (L)
      </span>
      <span className="inline-flex items-center gap-1.5">
        <span className="size-2.5 rounded-[2px] border border-primary/30 bg-primary-soft" aria-hidden="true" /> Lab (P)
      </span>
      <span className="inline-flex items-center gap-1.5">
        <span className="size-2.5 rounded-[2px] border border-line bg-surface-2" aria-hidden="true" /> Embedded theory + lab (E)
      </span>
    </p>
  );
}
