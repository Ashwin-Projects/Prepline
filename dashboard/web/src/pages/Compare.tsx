import type { ComparisonRow } from "../lib/api";
import { useApi } from "../lib/useApi";
import { GapBars } from "../components/GapBars";
import { Card, ErrorState, GateChip, InsufficientState, Loading, NoResultsState, PageHeader } from "../components/ui";

export default function Compare() {
  const { data, error, loading } = useApi<{ min_reports: number; targets: ComparisonRow[] }>("/api/v1/comparison");
  return (
    <>
      <PageHeader
        eyebrow="Dashboard · 02"
        title="Compare"
        lede="All configured company/role targets against the same syllabus. Scores are provisional, and each company is scored on its own set of interview topics, so similar scores are not a ranking. A target below the density gate shows no score."
      />
      {error && <ErrorState message={error} />}
      {loading && !data && <Loading />}
      {data && (
        <div className="grid grid-cols-4 gap-4 max-[1250px]:grid-cols-2 max-[640px]:grid-cols-1" data-testid="compare-grid">
          {data.targets.map((t) => (
            <Card key={t.target_id} testId={`compare-${t.target_id}`} className="flex flex-col">
              <div className="flex items-start justify-between gap-2">
                <h2 className="text-[16px] font-semibold text-ink">
                  {t.company} <span className="font-normal text-ink-2">{t.role}</span>
                </h2>
              </div>
              <p className="tabular mt-2 text-[44px] font-semibold leading-none tracking-tight text-ink">
                {t.status === "SUCCESS" && t.S_comp !== null ? t.S_comp.toFixed(1) : <span className="text-ink-3">n/a</span>}
              </p>
              {t.status === "SUCCESS" && (
                <p className="mt-1 text-[12px] text-ink-3">
                  provisional · {t.scoring_universe_size} interview topics
                </p>
              )}
              {t.results_available && (
                <div className="mt-2 flex flex-wrap items-center gap-2 text-[13px] text-ink-2">
                  <GateChip passed={t.density_gate_passed} count={t.report_count} min={data.min_reports} />
                  <span className="tabular">{t.raw_report_count} collected</span>
                </div>
              )}
              <div className="mt-4 flex-1">
                {!t.results_available ? (
                  <NoResultsState company={t.company} role={t.role} />
                ) : t.status === "SUCCESS" ? (
                  <>
                    <h3 className="mb-2 text-[13px] font-medium text-ink-2">Top priority gaps</h3>
                    <GapBars gaps={t.top_priority_gaps} limit={5} compact />
                    <p className="tabular mt-3 text-[12px] text-ink-3">
                      {t.scoring_universe_size} scored topics · {t.fallback_topics} fallback-depth topics ·{" "}
                      {t.unmapped_distinct_terms} unmapped terms
                    </p>
                  </>
                ) : (
                  <InsufficientState
                    company={t.company}
                    role={t.role}
                    count={t.report_count ?? 0}
                    raw={t.raw_report_count}
                    min={data.min_reports}
                  />
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </>
  );
}
