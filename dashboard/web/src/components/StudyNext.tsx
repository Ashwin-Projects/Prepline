import { ExternalLink } from "lucide-react";
import type { StudyModule, StudyResponse } from "../lib/api";
import { pct } from "../lib/format";
import { useApi } from "../lib/useApi";
import { Card } from "./ui";

// τ is 0.50; a unit that clears it by less than this is shown as a loose match (see Known mapping limitations).
const WEAK_MATCH = 0.55;
const SHOWN_MODULES = 2;

function ModuleLine({ m }: { m: StudyModule }) {
  const weak = (m.similarity ?? 0) < WEAK_MATCH;
  return (
    <li className="min-w-0">
      <span className="tabular font-medium text-ink">{m.course_code}</span>
      <span className="text-ink-3"> · M{m.module_number}</span>{" "}
      <span className="text-ink-2">{m.module_title}</span>
      {weak && (
        <span
          className="ml-1.5 inline-flex whitespace-nowrap rounded-full bg-warn-soft px-1.5 text-[11px] font-medium text-warn"
          title={`Similarity ${m.similarity?.toFixed(2)}: barely above τ = 0.50, so this module may not really teach the topic`}
        >
          loose match
        </span>
      )}
    </li>
  );
}

// Per top priority gap: the VIT core modules its coverage comes from, and two checked practice pages.
export function StudyNext({ target, className = "" }: { target: string; className?: string }) {
  const { data } = useApi<StudyResponse>(`/api/v1/study/${target}`);
  return (
    <Card
      className={className}
      title="What to study next"
      subtitle="For each priority gap: the core-course modules to revise (strongest syllabus match first) and two practice pages."
      testId="study-next"
    >
      {!data ? (
        <div className="h-24 animate-pulse rounded-md bg-surface-2 motion-reduce:animate-none" aria-hidden="true" />
      ) : data.status !== "SUCCESS" ? (
        <p className="text-[14px] text-ink-3">No priority gaps: this company is below the density gate.</p>
      ) : (
        <>
          <ol className="divide-y divide-line">
            {data.items.map((item) => (
              <li
                key={item.topic_id}
                className="grid grid-cols-[1.5rem_minmax(0,14rem)_minmax(0,1fr)_minmax(0,16rem)] gap-x-4 gap-y-1.5 py-2.5 text-[13px] first:pt-0 last:pb-0 max-[900px]:grid-cols-[1.5rem_minmax(0,1fr)]"
                data-testid="study-item"
              >
                <span className="tabular pt-px text-right text-ink-3">{item.rank}</span>
                <div className="min-w-0">
                  <p className="text-[14px] font-medium leading-snug text-ink">{item.topic_name}</p>
                  {item.coverage !== null && <p className="tabular text-ink-3">coverage {pct(item.coverage)}</p>}
                </div>
                <div className="min-w-0 max-[900px]:col-start-2">
                  {item.modules.length > 0 ? (
                    <ul className="space-y-0.5">
                      {item.modules.slice(0, SHOWN_MODULES).map((m) => (
                        <ModuleLine key={`${m.course_code}-${m.module_number}`} m={m} />
                      ))}
                    </ul>
                  ) : (
                    <p className="font-medium text-warn">{item.note}</p>
                  )}
                </div>
                <ul className="min-w-0 space-y-0.5 max-[900px]:col-start-2">
                  {item.practice.map((link) => (
                    <li key={link.url}>
                      <a
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary underline decoration-primary/40 underline-offset-2 hover:decoration-primary"
                      >
                        {link.title}
                        <ExternalLink size={12} className="ml-1 inline align-[-1px]" aria-hidden="true" />
                        <span className="sr-only">(GeeksforGeeks, opens in a new tab)</span>
                      </a>
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ol>
          <p className="mt-3 text-[12px] text-ink-3">
            Modules come from the same syllabus matching as the scores, so they share its limits; “loose match” marks a
            similarity under {WEAK_MATCH.toFixed(2)}. Links checked {data.links_verified_on} (GeeksforGeeks).
          </p>
        </>
      )}
    </Card>
  );
}
