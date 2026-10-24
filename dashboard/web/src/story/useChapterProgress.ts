import { useEffect, useMemo, useState, type RefObject } from "react";
import { motionValue, useReducedMotion, useScroll, type MotionValue } from "motion/react";

// Same condition as the `unpinned` CSS variant in index.css.
const UNPINNED = "(max-width: 899.98px), (max-height: 699.98px)";

function useUnpinned() {
  const [unpinned, setUnpinned] = useState(() => window.matchMedia(UNPINNED).matches);
  useEffect(() => {
    const query = window.matchMedia(UNPINNED);
    const onChange = () => setUnpinned(query.matches);
    query.addEventListener("change", onChange);
    return () => query.removeEventListener("change", onChange);
  }, []);
  return unpinned;
}

// Scroll progress 0→1 through one chapter. Wide, tall screens pin the chapter, so progress runs while its sticky
// stage is held (section top at viewport top → section bottom at viewport bottom). Narrow or short screens do not pin
// (text and scene would not fit one screen), so progress tracks the scene itself: it starts as the scene's top
// enters the viewport and completes once the scene is well in view. Under prefers-reduced-motion every chapter
// reports 1, its final state.
export function useChapterProgress(
  sectionRef: RefObject<HTMLElement | null>,
  sceneRef: RefObject<HTMLElement | null>,
): { progress: MotionValue<number>; reduced: boolean } {
  const reduced = useReducedMotion() ?? false;
  const unpinned = useUnpinned();
  const { scrollYProgress } = useScroll(
    unpinned
      ? { target: sceneRef, offset: ["start end", "end 0.6"] }
      : { target: sectionRef, offset: ["start start", "end end"] },
  );
  const done = useMemo(() => motionValue(1), []);
  return { progress: reduced ? done : scrollYProgress, reduced };
}
