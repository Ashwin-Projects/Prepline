import { useRef, type ReactNode } from "react";
import type { MotionValue } from "motion/react";
import { useChapterProgress } from "./useChapterProgress";

// One story chapter: a tall section whose sticky stage stays in view while the scene scrubs with scroll.
// Reduced motion: normal document flow, scene drawn in its final state.
export function Chapter({ index, id, title, lede, facts, note, visualIsContent = false, loading = false, children }: {
  index: number;
  id: string;
  title: string;
  lede: ReactNode;
  facts?: ReactNode;
  note?: ReactNode;
  // True when the scene is real content (e.g. the gap list) rather than an illustration of facts stated in text.
  visualIsContent?: boolean;
  // Results not loaded yet: show a placeholder of the scene's size so the stage does not jump when data arrives.
  loading?: boolean;
  children: (progress: MotionValue<number>, reduced: boolean) => ReactNode;
}) {
  const ref = useRef<HTMLElement>(null);
  const sceneRef = useRef<HTMLDivElement>(null);
  const { progress, reduced } = useChapterProgress(ref, sceneRef);
  return (
    <section
      ref={ref}
      id={id}
      data-testid={`chapter-${id}`}
      aria-labelledby={`${id}-title`}
      className={`relative ${reduced ? "" : "h-[240vh] unpinned:h-auto"}`}
    >
      <div
        data-testid="chapter-stage"
        className={`${reduced ? "py-24" : "sticky top-0 h-svh pt-16 unpinned:static unpinned:h-auto unpinned:py-20"} mx-auto grid w-full max-w-[1280px] grid-cols-[minmax(0,5fr)_minmax(0,7fr)] items-center gap-14 px-8 max-[900px]:grid-cols-1 max-[900px]:gap-8 max-[900px]:px-4`}
      >
        <div className="min-w-0">
          <p className="tabular font-display text-[17px] text-primary italic">§ {String(index).padStart(2, "0")}</p>
          <h2
            id={`${id}-title`}
            className="mt-2 font-display text-[clamp(32px,4.2vw,58px)] leading-[1.02] font-medium tracking-[-0.025em] text-balance text-ink"
          >
            {title}
          </h2>
          <div className="mt-5 max-w-[48ch] text-[16px] leading-relaxed text-ink-2">{lede}</div>
          {facts && <dl className="mt-8 grid max-w-[34rem] grid-cols-[repeat(auto-fill,minmax(9.5rem,1fr))] gap-x-8 gap-y-5">{facts}</dl>}
          {note && <div className="mt-6 max-w-[48ch]">{note}</div>}
        </div>
        <div ref={sceneRef} className="relative min-w-0" aria-hidden={visualIsContent ? undefined : true}>
          {loading ? (
            <div
              data-testid="scene-skeleton"
              className="aspect-[4/3] w-full animate-pulse rounded-[10px] bg-surface-2 motion-reduce:animate-none"
            />
          ) : (
            children(progress, reduced)
          )}
        </div>
      </div>
    </section>
  );
}

// A large tabular figure with its label; the value carries the test id so tests can compare it with the API.
export function Fact({ label, value, testId }: { label: string; value: ReactNode; testId?: string }) {
  return (
    <div className="flex min-w-0 flex-col-reverse">
      <dt className="mt-1.5 max-w-[20ch] text-[13px] leading-snug text-ink-3">{label}</dt>
      <dd className="tabular text-[34px] leading-none font-medium tracking-[-0.02em] text-ink" data-testid={testId}>
        {value}
      </dd>
    </div>
  );
}
