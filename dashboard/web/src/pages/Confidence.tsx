import type { ComparisonRow, ResultsResponse } from "../lib/api";
import { coverageAtDepth, pct } from "../lib/format";
import { useTarget } from "../lib/target";
import { useApi } from "../lib/useApi";
import { TargetSelect } from "../components/TargetSelect";
import { Card, ErrorState, GateChip, Loading, PageHeader } from "../components/ui";

export default function Confidence() {
  const { target } = useTarget();
  const comparison = useApi<{ min_reports: number; targets: ComparisonRow[] }>("/api/v1/comparison");
  const results = useApi<ResultsResponse>(`/api/v1/results/${target}`);
  const error = comparison.error ?? results.error;
  const gamma = results.data?.result.scoring_config.gamma ?? 0.5;
  const fallbackCoverage = coverageAtDepth(1, gamma);

  return (
    <>
      <PageHeader
        title="Confidence"
        lede="Three indicators say how far to trust a score. They are shown next to every number instead of being folded into it."
        actions={<TargetSelect />}
      />
      {error && <ErrorState message={error} />}
      {(comparison.loading || results.loading) && !(comparison.data && results.data) && <Loading />}
      {comparison.data && results.data && (
        <div className="grid grid-cols-3 gap-4 max-[1150px]:grid-cols-1" data-testid="confidence">
          <Card title="1 · Insufficient data" subtitle={`A target needs ${comparison.data.min_reports} reports with at least one usable question.`} testId="indicator-gate">
            <p className="mb-3 text-[14px] text-ink-2">
              Behavioural rounds, vague mentions and questions given only as a link are filtered out first. Below the
              gate no score is computed at all.
            </p>
            <ul className="space-y-2">
              {comparison.data.targets.map((t) => (
                <li key={t.target_id} className="flex items-center justify-between gap-2 text-[14px]">
                  <span className="truncate text-ink">
                    {t.company} {t.role}
                  </span>
                  <span className="flex shrink-0 items-center gap-2">
                    <span className="tabular text-[12px] text-ink-3">{t.raw_report_count} collected</span>
                    <GateChip passed={t.density_gate_passed} count={t.report_count} min={comparison.data!.min_reports} />
                  </span>
                </li>
              ))}
            </ul>
          </Card>

          <Card title="2 · Fallback depth" subtitle="Topics whose syllabus units carry no depth signal (hours, labs, experiments)." testId="indicator-fallback">
            <p className="text-[14px] text-ink-2">
              Such a topic gets the minimum depth D = 1. With γ = {gamma}, a topic that is present but at depth 1 counts
              as only{" "}
              <strong className="tabular font-semibold text-ink" data-testid="fallback-coverage">
                {pct(fallbackCoverage, 1)}
              </strong>{" "}
              covered, so fallback depth lowers coverage on purpose rather than guessing.
            </p>
            <ul className="mt-3 space-y-1.5 text-[14px]">
              {comparison.data.targets.map((t) => (
                <li key={t.target_id} className="flex justify-between gap-2">
                  <span className="truncate text-ink">
                    {t.company} {t.role}
                  </span>
                  <span className="tabular shrink-0 text-ink-2">
                    {t.fallback_topics === null ? "not scored" : `${t.fallback_topics} of ${t.topics_in_taxonomy} topics`}
                  </span>
                </li>
              ))}
            </ul>
            <p className="mt-2 text-[12px] text-ink-3" data-testid="fallback-note">
              The syllabus is the same for every target, so the count is too.{" "}
              {(() => {
                const present = results.data.result.depth_counts?.present_topics?.fallback ?? 0;
                return present === 0
                  ? "None of the covered topics is at fallback depth; the fallback topics are uncovered ones."
                  : `${present} covered topics are at fallback depth.`;
              })()}
            </p>
          </Card>

          <Card
            title="3 · Unmapped terms"
            subtitle={`Terms that matched no taxonomy node (τ = ${results.data.result.scoring_config.similarity_threshold}) for ${results.data.target.company} ${results.data.target.role}.`}
            testId="indicator-unmapped"
          >
            {results.data.result.unmapped_terms_summary ? (
              <>
                <p className="tabular text-[14px] text-ink-2">
                  {results.data.result.unmapped_terms_summary.distinct_terms} distinct terms (
                  {Object.entries(results.data.result.unmapped_terms_summary.distinct_terms_by_source_type)
                    .map(([k, v]) => `${v} ${k}`)
                    .join(", ")}
                  ). Many interview terms unmapped means the taxonomy misses what that company asks.
                </p>
                <ol className="mt-3 space-y-1 text-[14px]" data-testid="unmapped-list">
                  {(results.data.result.top_unmapped_terms ?? []).map((u) => (
                    <li key={`${u.source_type}-${u.term}`} className="grid grid-cols-[minmax(0,1fr)_auto_auto] items-baseline gap-2">
                      <span className="truncate text-ink" title={u.term}>{u.term}</span>
                      <span className="text-[12px] text-ink-3">{u.source_type}</span>
                      <span className="tabular w-8 text-right text-ink-2">{u.occurrences}</span>
                    </li>
                  ))}
                </ol>
              </>
            ) : (
              <p className="text-[14px] text-ink-3">Not computed: the pipeline stopped at the density gate.</p>
            )}
          </Card>
        </div>
      )}
    </>
  );
}
