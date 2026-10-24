import { useMemo } from "react";
import { motion, useTransform, type MotionValue } from "motion/react";
import type { Topic } from "../../lib/api";
import { domainShort } from "../../lib/format";
import { seeded } from "../data";

// Positions: a centre in container percent (cx, cy) plus an offset in cqmin (ox, oy), so rings stay circular.
interface Pose {
  cx: number;
  cy: number;
  ox: number;
  oy: number;
}

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

// Scattered → clustered by domain → split into an inner ring of high-level concepts and an outer ring of skills.
function TopicDot({ a, b, c, high, progress }: { a: Pose; b: Pose; c: Pose; high: boolean; progress: MotionValue<number> }) {
  const transform = useTransform(progress, (p) => {
    const t1 = ease(Math.min(Math.max((p - 0.05) / 0.35, 0), 1));
    const t2 = ease(Math.min(Math.max((p - 0.55) / 0.35, 0), 1));
    const pick = (k: keyof Pose) => lerp(lerp(a[k], b[k], t1), c[k], t2);
    return `translate(calc(${pick("cx")}cqw + ${pick("ox")}cqmin - 50%), calc(${pick("cy")}cqh + ${pick("oy")}cqmin - 50%))`;
  });
  return (
    <motion.span
      style={{ transform }}
      className={`absolute top-0 left-0 size-[2.2cqmin] rounded-full ${
        high ? "bg-primary" : "border-[0.35cqmin] border-ink-3 bg-bg"
      }`}
    />
  );
}

const CLUSTERS = [
  { cx: 27, cy: 30 },
  { cx: 73, cy: 28 },
  { cx: 18, cy: 74 },
  { cx: 50, cy: 70 },
  { cx: 82, cy: 74 },
];

export function TaxonomyScene({ topics, domains, progress }: {
  topics: Topic[];
  domains: { domain: string; count: number }[];
  progress: MotionValue<number>;
}) {
  const dots = useMemo(() => {
    const rand = seeded(83);
    const order = new Map(domains.map((d, i) => [d.domain, i]));
    const sorted = [...topics].sort(
      (x, y) => (order.get(x.domain) ?? 9) - (order.get(y.domain) ?? 9) || x.topic_id.localeCompare(y.topic_id),
    );
    const highs = sorted.filter((t) => t.type === "high_level_concept");
    const grans = sorted.filter((t) => t.type !== "high_level_concept");
    const seenInDomain = new Map<string, number>();
    return sorted.map((t) => {
      const k = seenInDomain.get(t.domain) ?? 0;
      seenInDomain.set(t.domain, k + 1);
      const cluster = CLUSTERS[order.get(t.domain) ?? 0] ?? CLUSTERS[0];
      const angle = k * 2.39996; // golden angle: an even sunflower spiral per domain
      const radius = 2.6 * Math.sqrt(k + 0.5);
      const high = t.type === "high_level_concept";
      const ringList = high ? highs : grans;
      const ringIndex = ringList.indexOf(t);
      const ringAngle = (ringIndex / ringList.length) * Math.PI * 2 - Math.PI / 2;
      const ringRadius = high ? 20 : 38;
      return {
        id: t.topic_id,
        high,
        a: { cx: 6 + rand() * 88, cy: 6 + rand() * 88, ox: 0, oy: 0 },
        b: { cx: cluster.cx, cy: cluster.cy, ox: Math.cos(angle) * radius, oy: Math.sin(angle) * radius },
        c: { cx: 50, cy: 50, ox: Math.cos(ringAngle) * ringRadius, oy: Math.sin(ringAngle) * ringRadius },
      };
    });
  }, [topics, domains]);

  const clusterLabels = useTransform(progress, [0.3, 0.42, 0.55, 0.65], [0, 1, 1, 0]);
  const ringLabels = useTransform(progress, [0.82, 0.95], [0, 1]);
  return (
    <div className="relative aspect-[4/3] w-full [container-type:size]">
      {dots.map((d) => (
        <TopicDot key={d.id} {...d} progress={progress} />
      ))}
      {domains.slice(0, CLUSTERS.length).map((d, i) => (
        <motion.p
          key={d.domain}
          style={{ opacity: clusterLabels, left: `${CLUSTERS[i].cx}%`, top: `calc(${CLUSTERS[i].cy}% + 15cqmin)` }}
          className="absolute -translate-x-1/2 text-center text-[13px] whitespace-nowrap text-ink-2"
        >
          {domainShort(d.domain)} <span className="tabular text-ink-3">{d.count}</span>
        </motion.p>
      ))}
      <motion.p style={{ opacity: ringLabels }} className="absolute top-1/2 left-1/2 -translate-1/2 text-center font-display text-[clamp(10px,3.2cqmin,15px)] leading-tight text-ink-2 italic">
        concepts inside,
        <br />
        skills around
      </motion.p>
    </div>
  );
}
