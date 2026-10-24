import { useMemo } from "react";
import { motion, useTransform, type MotionValue } from "motion/react";
import type { Topic } from "../../lib/api";

// S_comp as a picture: one strip, a column per scored topic. Column width = I(t) / ΣI, fill height = Coverage(t),
// so the filled share of the strip is exactly Σ I·Coverage / Σ I = S_comp / 100.
function Column({ topic, share, index, count, progress }: {
  topic: Topic;
  share: number;
  index: number;
  count: number;
  progress: MotionValue<number>;
}) {
  const start = 0.05 + (index / count) * 0.25;
  const appear = useTransform(progress, [start, start + 0.1], [0, 1], { clamp: true });
  const fill = useTransform(progress, [0.4, 0.75], [0, topic.coverage], { clamp: true });
  const fillTransform = useTransform(fill, (f) => `scaleY(${f})`);
  // The white copy of the label is clipped to the filled part, so the label reads dark on the track, white on the fill.
  const fillClip = useTransform(fill, (f) => `inset(${((1 - f) * 100).toFixed(2)}% 0 0 0)`);
  return (
    <motion.div style={{ opacity: appear, flexGrow: share }} className="relative h-full min-w-0 basis-0 overflow-hidden bg-track">
      <motion.div style={{ transform: fillTransform }} className="absolute inset-0 origin-bottom bg-series" />
      {share > 0.07 && (
        <>
          <ColumnLabel name={topic.topic_name} layer="base" className="text-ink" />
          <motion.div style={{ clipPath: fillClip }} className="absolute inset-0" data-label-layer="fill">
            <ColumnLabel name={topic.topic_name} className="text-white" />
          </motion.div>
        </>
      )}
    </motion.div>
  );
}

function ColumnLabel({ name, layer, className }: { name: string; layer?: "base"; className: string }) {
  return (
    <span
      data-label-layer={layer}
      className={`absolute bottom-2 left-1/2 max-h-[85%] -translate-x-1/2 rotate-180 truncate text-[11px] leading-none font-medium [writing-mode:vertical-rl] ${className}`}
    >
      {name}
    </span>
  );
}

export function ScoringScene({ topics, sComp, progress }: { topics: Topic[]; sComp: number; progress: MotionValue<number> }) {
  const universe = useMemo(
    () => topics.filter((t) => (t.importance ?? 0) > 0).sort((a, b) => (b.importance ?? 0) - (a.importance ?? 0)),
    [topics],
  );
  const total = universe.reduce((s, t) => s + (t.importance ?? 0), 0) || 1;
  const level = useTransform(progress, [0.75, 0.9], [0, 1], { clamp: true });
  return (
    <div className="w-full">
      <div className="relative">
        <div className="flex aspect-[16/10] w-full gap-[2px]">
          {universe.map((t, i) => (
            <Column key={t.topic_id} topic={t} share={(t.importance ?? 0) / total} index={i} count={universe.length} progress={progress} />
          ))}
        </div>
        <motion.div
          style={{ opacity: level, bottom: `${sComp}%` }}
          className="pointer-events-none absolute inset-x-0 border-t-2 border-dashed border-ink"
        />
        <motion.p
          style={{ opacity: level, bottom: `${sComp}%` }}
          className="absolute right-0 mb-1.5 bg-bg/90 px-1.5 text-[13px] font-medium text-ink"
        >
          {sComp.toFixed(1)}
        </motion.p>
      </div>
      <p className="mt-4 text-[13px] text-ink-3">
        Column width: how often interviews ask (importance) · fill: syllabus coverage · dashed line: the filled share,
        which is the score.
      </p>
    </div>
  );
}
