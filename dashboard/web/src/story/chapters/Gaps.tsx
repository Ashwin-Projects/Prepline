import { motion, useTransform, type MotionValue } from "motion/react";
import type { Gap } from "../../lib/api";
import { GapBars } from "../../components/GapBars";

// The top priority gaps, rising into place; GapBars is the same component the Overview uses.
export function GapsScene({ gaps, progress }: { gaps: Gap[]; progress: MotionValue<number> }) {
  const opacity = useTransform(progress, [0.05, 0.35], [0, 1], { clamp: true });
  const transform = useTransform(progress, [0.05, 0.4], [24, 0], { clamp: true });
  const transformText = useTransform(transform, (y) => `translateY(${y}px)`);
  return (
    <motion.div style={{ opacity, transform: transformText }} className="rounded-[10px] border border-line bg-surface p-6 max-[600px]:p-4" data-testid="story-gaps">
      <p className="mb-4 font-display text-[19px] font-medium text-ink">Top {Math.min(5, gaps.length)} priority gaps</p>
      <GapBars gaps={gaps} limit={5} />
      <p className="mt-4 text-[12px] text-ink-3">PriorityGap = I(t) × (1 − Coverage(t)); bar length relative to the largest gap.</p>
    </motion.div>
  );
}
