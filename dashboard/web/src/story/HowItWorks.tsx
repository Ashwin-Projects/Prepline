import { useMemo } from "react";
import { ArrowDown, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import type { ComparisonRow, ResultsResponse } from "../lib/api";
import { useTarget } from "../lib/target";
import { useApi } from "../lib/useApi";
import { TargetSelect } from "../components/TargetSelect";
import { ThemeToggle } from "../components/ThemeToggle";
import { ConfidenceBadge, ErrorState, InsufficientState, ProvisionalChip } from "../components/ui";
import { Tex } from "../components/Tex";
import { confidenceOf } from "../lib/confidence";
import { GapsScene } from "./chapters/Gaps";
import { ScoringScene } from "./chapters/Scoring";
import { Chapter, Fact } from "./Chapter";
import { courseCodes, evidenceRows, topicBreakdown, type StoryData } from "./data";
import { EvidenceScene } from "./chapters/Evidence";
import { SyllabusLegend, SyllabusScene } from "./chapters/Syllabus";
import { TaxonomyScene } from "./chapters/Taxonomy";

const STEPS = [
  ["syllabus", "University syllabus and course content"],
  ["taxonomy", "Taxonomy of topics and skills"],
  ["evidence", "Company interview evidence"],
  ["scoring", "Alignment and the composite score"],
  ["gaps", "Priority gaps, confidence and what to study"],
] as const;

// "How PREPLINE works": a scroll-driven explanation built only from the saved results the dashboard shows.
export default function HowItWorks() {
  const { target } = useTarget();
  const results = useApi<ResultsResponse>(`/api/v1/results/${target}`);
  const comparison = useApi<{ min_reports: number; targets: ComparisonRow[] }>("/api/v1/comparison");
  const error = results.error ?? comparison.error;
  const data: StoryData | null =
    results.data && comparison.data ? { results: results.data, comparison: comparison.data.targets } : null;
  const resultsData = results.data;
  const comparisonData = comparison.data;
  const codes = useMemo(() => (resultsData ? courseCodes(resultsData.result.syllabus_files) : []), [resultsData]);
  const breakdown = useMemo(() => (resultsData ? topicBreakdown(resultsData.topics) : null), [resultsData]);
  const evidence = useMemo(() => (comparisonData ? evidenceRows(comparisonData.targets) : []), [comparisonData]);
  const scored = data && data.results.result.status === "SUCCESS" ? data.results.result : null;
  const confidence = scored && data ? confidenceOf(scored, data.results.min_reports) : null;

  return (
    <div className="min-h-screen bg-bg text-ink">
      <header className="top-0 z-20 border-b border-line bg-bg min-[1000px]:sticky">
        <div className="mx-auto flex max-w-[1280px] flex-wrap items-center gap-x-5 gap-y-3 px-8 py-3 max-[900px]:px-4">
          <Link to="/" className="font-display text-[22px] leading-none font-semibold tracking-[-0.015em] text-ink">
            Prepline
          </Link>
          <div className="ml-auto flex items-center gap-1 min-[701px]:order-3">
            <ThemeToggle compact />
            <Link
              to="/"
              className="press inline-flex items-center gap-1.5 rounded-md px-3 py-2 text-[14px] font-medium text-ink-2 transition-colors duration-150 hover:bg-surface-2 hover:text-ink"
            >
              Dashboard <ArrowRight size={15} aria-hidden="true" />
            </Link>
          </div>
          <div className="min-w-0 max-[701px]:w-full min-[701px]:ml-auto min-[701px]:order-2">
            <TargetSelect />
          </div>
        </div>
      </header>

      <main>
        <section className="mx-auto grid min-h-[calc(100svh-61px)] max-w-[1280px] grid-cols-[minmax(0,7fr)_minmax(0,4fr)] items-center gap-16 px-8 py-20 max-[1000px]:grid-cols-1 max-[1000px]:gap-12 max-[900px]:min-h-0 max-[900px]:px-4 max-[900px]:py-16">
          <div className="min-w-0">
            <h1 className="max-w-[18ch] text-[clamp(44px,6.6vw,96px)] leading-[0.98] font-medium tracking-[-0.035em] text-balance">
              Does the syllabus match the interview?
            </h1>
            <p className="mt-7 max-w-[56ch] text-[18px] leading-relaxed text-ink-2 max-[600px]:text-[16px]">
              PREPLINE reads a university's core syllabus and public interview reports, maps both onto one topic taxonomy,
              and measures how much of what interviewers ask the curriculum covers.
            </p>
            <p className="story-cue mt-14 inline-flex items-center gap-2 text-[14px] text-ink-3 max-[1000px]:mt-10">
              <ArrowDown size={16} aria-hidden="true" /> Scroll through the five steps
            </p>
          </div>
          <nav aria-label="Steps" className="min-w-0 border-l border-line pl-8 max-[1000px]:border-l-0 max-[1000px]:border-t max-[1000px]:pt-8 max-[1000px]:pl-0">
            <ol className="space-y-1">
              {STEPS.map(([id, label], i) => (
                <li key={id}>
                  <a
                    href={`#${id}`}
                    className="group flex items-baseline gap-4 rounded-md py-2.5 text-ink-2 transition-colors duration-150 hover:text-ink"
                  >
                    <span className="tabular w-7 shrink-0 font-display text-[17px] text-primary italic">§{String(i + 1).padStart(2, "0")}</span>
                    <span className="text-[16px] underline decoration-transparent underline-offset-4 transition-colors duration-150 group-hover:decoration-line">
                      {label}
                    </span>
                  </a>
                </li>
              ))}
            </ol>
          </nav>
        </section>

        {error ? (
          <div className="mx-auto max-w-[1280px] px-8 pb-16 max-[900px]:px-4">
            <ErrorState message={error} />
          </div>
        ) : (
          <>
            <Chapter
              loading={!data}
              index={1}
              id="syllabus"
              title="The syllabus, read course by course."
              lede={
                <>
                  Every core course syllabus of the VIT B.Tech CSE 2024-25 curriculum is split into modules, keeping the
                  hours and lab work that signal how deeply a topic is taught.
                  <SyllabusLegend />
                </>
              }
              facts={
                <>
                  <Fact label="course syllabus files" value={data?.results.result.syllabus_files.length ?? "—"} testId="story-file-count" />
                  <Fact label="core courses" value={codes.length || "—"} testId="story-course-count" />
                </>
              }
            >
              {(progress) => codes.length > 0 && <SyllabusScene codes={codes} progress={progress} />}
            </Chapter>
            <Chapter
              loading={!data}
              index={2}
              id="taxonomy"
              title="One shared language of topics."
              lede={
                <>
                  A versioned taxonomy gives syllabus units and interview questions the same vocabulary, so the two can be
                  compared topic by topic.
                  {breakdown && (
                    <span className="mt-4 block text-[14px] text-ink-3">
                      {breakdown.byDomain.map((d) => `${d.name} ${d.count}`).join(" · ")}
                    </span>
                  )}
                </>
              }
              facts={
                <>
                  <Fact label={`topics in taxonomy ${data?.results.result.taxonomy_version ?? ""}`.trim()} value={breakdown?.total ?? "—"} testId="story-topic-count" />
                  <Fact label="high-level concepts, matched by syllabus units" value={breakdown?.highLevel ?? "—"} testId="story-high-level" />
                  <Fact label="granular skills, matched by interview questions" value={breakdown?.granular ?? "—"} testId="story-granular" />
                </>
              }
            >
              {(progress) =>
                data && breakdown && <TaxonomyScene topics={data.results.topics} domains={breakdown.byDomain} progress={progress} />
              }
            </Chapter>
            <Chapter
              loading={!data}
              index={3}
              id="evidence"
              title="What interviewers actually ask."
              lede={
                <>
                  Public interview write-ups are filtered down to usable technical questions: behavioural rounds, rows
                  flagged for review, and rows without question text or a report id are dropped. A company is scored only
                  when at least{" "}
                  {data?.results.min_reports ?? "the minimum number of"} reports still have a usable question.
                  <ul className="sr-only">
                    {evidence.map((r) => (
                      <li key={r.id}>
                        {r.label}: {r.raw} reports collected, {r.usable ?? "no"} usable, gate {r.passed ? "passed" : "not met"}
                      </li>
                    ))}
                  </ul>
                </>
              }
              facts={
                data && (
                  <Fact
                    label={`of ${data.results.result.interview_filter.questions_total} ${data.results.target.company} questions usable`}
                    value={data.results.result.interview_filter.questions_included}
                    testId="story-questions-included"
                  />
                )
              }
            >
              {(progress) => evidence.length > 0 && <EvidenceScene rows={evidence} progress={progress} />}
            </Chapter>
            <Chapter
              loading={!data}
              index={4}
              id="scoring"
              title="Coverage, weighted by what is asked."
              lede={
                <>
                  Each topic's syllabus coverage is weighted by how often {data?.results.target.company ?? "the company"}'s
                  interviews raise it. The importance-weighted share of coverage is the composite score.
                  <span className="mt-3 block">
                    <Tex>{String.raw`S_{\text{comp}} = 100 \cdot \frac{\sum_{t} I(t)\,\text{Coverage}(t)}{\sum_{t} I(t)}`}</Tex>
                  </span>
                  {data && (
                    <span className="mt-2 block text-[14px] text-ink-3">
                      Matching threshold τ = {data.results.result.scoring_config.similarity_threshold.toFixed(2)} · depth
                      decay γ = {data.results.result.scoring_config.gamma}
                    </span>
                  )}
                </>
              }
              facts={
                scored && (
                  <>
                    <Fact
                      label="composite alignment, out of 100 (provisional)"
                      value={<span data-testid="story-s-comp">{scored.S_comp?.toFixed(1)}</span>}
                    />
                    <Fact label={`topics carry the ${data?.results.target.company} score`} value={scored.scoring_universe_size} testId="story-universe" />
                  </>
                )
              }
              note={
                data &&
                !scored && (
                  <InsufficientState
                    company={data.results.target.company}
                    role={data.results.target.role}
                    count={data.results.result.report_count}
                    raw={data.results.raw_report_count}
                    min={data.results.min_reports}
                  />
                )
              }
            >
              {(progress) =>
                data && scored && <ScoringScene topics={data.results.topics} sComp={scored.S_comp ?? 0} progress={progress} />
              }
            </Chapter>
            <Chapter
              loading={!data}
              index={5}
              id="gaps"
              title="Where to study next."
              lede="Topics that interviews stress and the syllabus covers least rank first, with the confidence and known limits stated beside them."
              visualIsContent
              note={
                data &&
                (confidence && scored ? (
                  <div className="space-y-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <ConfidenceBadge level={confidence.level} />
                      <ProvisionalChip />
                    </div>
                    {confidence.reasons.length > 0 && (
                      <ul className="list-disc space-y-0.5 pl-4 text-[14px] text-ink-3">
                        {confidence.reasons.map((r) => (
                          <li key={r}>{r}</li>
                        ))}
                      </ul>
                    )}
                    <p className="text-[14px] text-ink-2" data-testid="story-limitations">
                      Scores are provisional: the topic matcher has known mapping errors, listed on the Overview and explained
                      on the <Link to="/confidence" className="font-medium text-ink underline decoration-line underline-offset-4 hover:decoration-ink">Confidence</Link> page.
                    </p>
                    <p className="text-[14px] text-ink-2">
                      For each gap, <em>What to study next</em> on the Overview lists the VIT modules to revise and two checked
                      practice pages.
                    </p>
                  </div>
                ) : (
                  <p className="text-[14px] text-ink-2">
                    No priority gaps are computed for {data.results.target.company} {data.results.target.role}: it is below the
                    density gate.
                  </p>
                ))
              }
            >
              {(progress) =>
                scored && <GapsScene gaps={scored.top_priority_gaps ?? []} progress={progress} />
              }
            </Chapter>
          </>
        )}

        <section className="border-t border-line">
          <div className="mx-auto max-w-[1280px] px-8 py-28 max-[900px]:px-4 max-[900px]:py-20">
            <p className="max-w-[24ch] font-display text-[clamp(32px,4vw,52px)] leading-[1.05] font-medium tracking-[-0.025em] text-balance">
              Every number above comes from the dashboard's saved results.
            </p>
            <div className="mt-10 flex flex-wrap items-center gap-x-6 gap-y-4">
              <Link
                to="/"
                className="press inline-flex items-center gap-2 rounded-md bg-primary px-5 py-3 text-[15px] font-medium text-surface transition-opacity duration-150 hover:opacity-90"
              >
                Open the dashboard <ArrowRight size={16} aria-hidden="true" />
              </Link>
              <Link to="/confidence" className="text-[15px] font-medium text-ink underline decoration-line underline-offset-4 hover:decoration-ink">
                How far to trust a result
              </Link>
              <Link to="/methodology" className="text-[15px] font-medium text-ink underline decoration-line underline-offset-4 hover:decoration-ink">
                Methodology
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-line">
        <p className="mx-auto max-w-[1280px] px-8 py-4 text-[12px] text-ink-3 max-[900px]:px-4">
          Topic alignment is diagnostic, not a hiring guarantee: it compares syllabus topics with topics reported in public
          interview write-ups. Results v1.2 · taxonomy v1.0 · scoring config v1.2.
        </p>
      </footer>
    </div>
  );
}
