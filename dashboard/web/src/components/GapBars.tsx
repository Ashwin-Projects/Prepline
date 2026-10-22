import type { Gap } from "../lib/api";
import { num, pct } from "../lib/format";

// Ranked priority gaps as an HTML bar list: bar length = PriorityGap(t) relative to the largest gap shown.
export function GapBars({ gaps, limit = 10, compact = false }: { gaps: Gap[]; limit?: number; compact?: boolean }) {
  const shown = gaps.slice(0, limit);
  if (shown.length === 0) return <p className="text-[14px] text-ink-3">No priority gaps (no topic has importance above zero).</p>;
  const max = Math.max(...shown.map((g) => g.priority_gap), 1e-9);
  return (
    <ol className="space-y-2" data-testid="gap-list">
      {shown.map((g, i) => (
        <li key={g.topic_id} className="grid grid-cols-[1.5rem_minmax(0,1fr)_auto] items-center gap-x-2">
          <span className="tabular text-right text-[13px] text-ink-3">{g.rank}</span>
          <div className="min-w-0">
            <div className="flex items-baseline justify-between gap-2">
              <span
                className={`${compact ? "line-clamp-2 text-[13px] leading-snug" : "truncate text-[14px]"} text-ink`}
                title={`${g.topic_name} (${g.topic_id})`}
              >
                {g.topic_name}
              </span>
              {!compact && (
                <span className="tabular shrink-0 text-[12px] text-ink-3">
                  I {num(g.importance, 2)} · cov {pct(g.coverage)}
                </span>
              )}
            </div>
            <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-track" aria-hidden="true">
              <div
                className="bar-grow h-full rounded-full bg-series"
                style={{ width: `${(g.priority_gap / max) * 100}%`, ["--i" as string]: i }}
              />
            </div>
          </div>
          <span className="tabular w-12 text-right text-[13px] font-medium text-ink">{num(g.priority_gap)}</span>
        </li>
      ))}
    </ol>
  );
}
