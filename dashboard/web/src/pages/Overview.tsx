import { useMemo } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { FileDown } from "lucide-react";
import { reportUrl, type ResultsResponse, type Topic } from "../lib/api";
import { confidenceOf } from "../lib/confidence";
import { date, domainName, domainShort, pct } from "../lib/format";
import { useTarget } from "../lib/target";
import { useApi } from "../lib/useApi";
import { GapBars } from "../components/GapBars";
import { TargetSelect } from "../components/TargetSelect";
import { Card, ConfidenceBadge, ErrorState, GateChip, InsufficientState, Loading, PageHeader, ProvisionalChip, Stat } from "../components/ui";
import { MappingLimitations } from "../components/MappingLimitations";
import { StudyNext } from "../components/StudyNext";

export interface DomainCoverage {
  domain: string;
  name: string;
  short: string;
  coverage: number;
  covered: number;
  total: number;
}

// Mean coverage of every taxonomy topic in a domain, plus how many topics the syllabus covers at all.
export function coverageByDomain(topics: Topic[]): DomainCoverage[] {
  const groups = new Map<string, Topic[]>();
  for (const t of topics) groups.set(t.domain, [...(groups.get(t.domain) ?? []), t]);
  return [...groups.entries()]
    .map(([domain, list]) => ({
      domain,
      name: domainName(domain),
      short: domainShort(domain),
      coverage: list.reduce((s, t) => s + t.coverage, 0) / list.length,
      covered: list.filter((t) => t.presence === 1).length,
      total: list.length,
    }))
    .sort((a, b) => b.coverage - a.coverage);
}

function DomainTooltip({ active, payload }: { active?: boolean; payload?: { payload: DomainCoverage }[] }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="rounded-md border border-line bg-surface px-3 py-2 text-[13px] shadow-sm">
      <p className="font-medium text-ink">{d.name}</p>
      <p className="tabular text-ink-2">
        Mean coverage {pct(d.coverage)} · {d.covered}/{d.total} topics covered
      </p>
    </div>
  );
}

export default function Overview() {
  const { target } = useTarget();
  const { data, error, loading } = useApi<ResultsResponse>(`/api/v1/results/${target}`);
  const domains = useMemo(() => (data ? coverageByDomain(data.topics) : []), [data]);
  const confidence = data && data.result.status === "SUCCESS" ? confidenceOf(data.result, data.min_reports) : null;

  return (
    <>
      <PageHeader
        title="Overview"
        lede="How well the VIT CSE 2024-25 core syllabus covers the topics a company asks about in interviews."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <TargetSelect />
            <a
              href={reportUrl(target)}
              download
              className="press inline-flex items-center gap-1.5 whitespace-nowrap rounded-lg border border-line bg-surface px-3 py-2 text-[13px] font-medium text-ink transition-colors duration-150 hover:bg-surface-2"
            >
              <FileDown size={15} aria-hidden="true" />
              Download report (PDF)
            </a>
          </div>
        }
      />
      {error && <ErrorState message={error} />}
      {loading && !data && <Loading />}
      {data && (
        <div className="grid grid-cols-12 gap-4" data-testid="overview">
          <Card className="col-span-5 max-[1100px]:col-span-12" testId="score-card">
            <h2 className="text-[15px] font-semibold text-ink">
              Composite alignment <span className="font-normal text-ink-2">· {data.target.company} {data.target.role}</span>
            </h2>
            {confidence ? (
              <>
                <div className="mt-2 flex flex-wrap items-end gap-x-4 gap-y-2">
                  <p className="tabular text-[64px] font-semibold leading-none tracking-tight text-ink" data-testid="s-comp">
                    {data.result.S_comp?.toFixed(1)}
                    <span className="ml-1 text-[22px] font-medium text-ink-3">/ 100</span>
                  </p>
                  <ConfidenceBadge level={confidence.level} />
                  <ProvisionalChip />
                </div>
                <p className="mt-3 max-w-[38ch] text-[14px] text-ink-2">
                  Importance-weighted syllabus coverage of the {data.result.scoring_universe_size} topics this company's
                  interviewers ask about. Each company has its own topic set, so similar scores are not a ranking.
                </p>
                {confidence.reasons.length > 0 && (
                  <ul className="mt-2 list-disc space-y-0.5 pl-4 text-[13px] text-ink-3">
                    {confidence.reasons.map((r) => (
                      <li key={r}>{r}</li>
                    ))}
                  </ul>
                )}
              </>
            ) : (
              <div className="mt-3 space-y-3">
                <p className="text-[40px] font-semibold leading-none text-ink-3" data-testid="s-comp">
                  n/a
                </p>
                <InsufficientState
                  company={data.target.company}
                  role={data.target.role}
                  count={data.result.report_count}
                  raw={data.raw_report_count}
                  min={data.min_reports}
                />
              </div>
            )}
          </Card>

          <Card className="col-span-7 max-[1100px]:col-span-12" title="Data" testId="data-card">
            <dl className="grid grid-cols-3 gap-x-4 gap-y-3 max-[640px]:grid-cols-2">
              <Stat
                label="Reports"
                value={`${data.raw_report_count} → ${data.result.report_count}`}
                hint="collected → with a usable question"
              />
              <Stat
                label="Density gate"
                value={
                  <GateChip
                    passed={data.result.report_count >= data.min_reports}
                    count={data.result.report_count}
                    min={data.min_reports}
                  />
                }
              />
              <Stat
                label="Questions"
                value={`${data.result.interview_filter.questions_included} / ${data.result.interview_filter.questions_total}`}
                hint="scored / collected"
              />
              <Stat label="Taxonomy" value={data.result.taxonomy_version ?? "v1.0"} />
              <Stat label="Scoring config" value={data.result.scoring_config_version} />
              <Stat label="Generated" value={date(data.result.generated_at)} />
              <Stat
                label="Syllabus"
                value={`${data.result.syllabus_files.length} course files`}
                hint={data.result.syllabus_id}
              />
              {data.result.scoring_universe_size !== undefined && (
                <Stat label="Scoring universe" value={`${data.result.scoring_universe_size} topics`} hint="I(t) > 0" />
              )}
            </dl>
          </Card>

          <Card
            className="col-span-6 max-[1100px]:col-span-12"
            title="Priority gaps"
            subtitle="Ranked by PriorityGap = importance × (1 − coverage)"
            testId="gaps-card"
          >
            {data.result.status === "SUCCESS" ? (
              <GapBars gaps={data.result.top_priority_gaps ?? []} />
            ) : (
              <p className="text-[14px] text-ink-3">Not computed: below the density gate.</p>
            )}
          </Card>

          <Card
            className="col-span-6 max-[1100px]:col-span-12"
            title="Coverage by domain"
            subtitle="Mean syllabus coverage of all taxonomy topics in each domain (same syllabus for every company)"
            testId="domain-card"
          >
            {domains.length === 0 ? (
              <p className="text-[14px] text-ink-3">No topic table has been exported for this target (evaluation/export_topic_tables.py).</p>
            ) : (
            <div className="h-[230px]" role="img" aria-label="Bar chart of mean coverage by domain">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={domains} layout="vertical" margin={{ top: 4, right: 44, bottom: 4, left: 8 }}>
                  <CartesianGrid horizontal={false} stroke="var(--line)" />
                  <XAxis
                    type="number"
                    domain={[0, 1]}
                    tickFormatter={(v: number) => pct(v)}
                    tick={{ fill: "var(--ink-3)", fontSize: 12 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    type="category"
                    dataKey="short"
                    width={104}
                    tick={{ fill: "var(--ink-2)", fontSize: 13 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip cursor={{ fill: "var(--surface-2)" }} content={<DomainTooltip />} />
                  <Bar
                    dataKey="coverage"
                    fill="var(--series)"
                    radius={[0, 4, 4, 0]}
                    barSize={16}
                    isAnimationActive={false}
                    label={{
                      position: "right",
                      formatter: (v: unknown) => pct(Number(v)),
                      fill: "var(--ink-2)",
                      fontSize: 12,
                    }}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
            )}
            <div className="sr-only">
            <table>
              <caption>Coverage by domain</caption>
              <tbody>
                {domains.map((d) => (
                  <tr key={d.domain}>
                    <th>{d.name}</th>
                    <td>{pct(d.coverage)}</td>
                    <td>
                      {d.covered} of {d.total} topics covered
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          </Card>

          <StudyNext target={target} className="col-span-12" />

          <MappingLimitations className="col-span-12" />
        </div>
      )}
    </>
  );
}
