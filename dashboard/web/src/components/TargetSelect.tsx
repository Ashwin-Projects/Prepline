import type { TargetSummary } from "../lib/api";
import { useTarget } from "../lib/target";
import { useApi } from "../lib/useApi";

// Segmented company/role selector; insufficient-data targets stay selectable and are marked.
export function TargetSelect() {
  const { target, setTarget } = useTarget();
  const { data } = useApi<{ targets: TargetSummary[] }>("/api/v1/targets");
  if (!data) return null;
  return (
    <div role="radiogroup" aria-label="Company and role" className="inline-flex max-w-full flex-wrap rounded-lg border border-line bg-surface p-0.5" data-testid="target-select">
      {data.targets.map((t) => {
        const active = t.id === target;
        return (
          <button
            key={t.id}
            role="radio"
            aria-checked={active}
            onClick={() => setTarget(t.id)}
            className={`press max-w-full cursor-pointer rounded-md px-3 py-1.5 text-left text-[13px] leading-snug font-medium transition-colors duration-150 ${
              active ? "bg-primary text-surface" : "text-ink-2 hover:bg-surface-2 hover:text-ink"
            }`}
          >
            {t.company} {t.role}
            {t.status === "INSUFFICIENT_DATA" && <span className="ml-1 opacity-80">· n/a</span>}
          </button>
        );
      })}
    </div>
  );
}
