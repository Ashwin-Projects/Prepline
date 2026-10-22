import { ArrowRight } from "lucide-react";
import { Card, PageHeader } from "../components/ui";
import { Tex } from "../components/Tex";

const LANES = [
  {
    label: "Syllabus",
    steps: [
      { title: "Course PDFs", detail: "25 core courses: modules, hours, lab experiments" },
      { title: "Two-pass abstraction", detail: "boilerplate stripped, RAKE concepts" },
      { title: "Match high-level nodes", detail: "MiniLM, τ = 0.50" },
      { title: "Coverage(t)", detail: "presence × depth decay; granular nodes inherit" },
    ],
  },
  {
    label: "Interviews",
    steps: [
      { title: "Interview reports", detail: "behavioural, vague and link-only rows filtered" },
      { title: "Two-pass abstraction", detail: "one question at a time" },
      { title: "Match granular skills", detail: "MiniLM, τ = 0.50, 60/40 credit" },
      { title: "Importance I(t)", detail: "per-report max, averaged over N" },
    ],
  },
];

function Step({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="w-[9rem] rounded-md border border-line bg-surface-2 px-2.5 py-2">
      <p className="text-[13px] font-semibold text-ink">{title}</p>
      <p className="text-[12px] leading-snug text-ink-3">{detail}</p>
    </div>
  );
}

const FORMULAS: { label: string; tex: string; note: string }[] = [
  {
    label: "Depth",
    tex: String.raw`D(t) = 1 + 4\cdot\frac{1}{|S_t|}\sum_{x\in S_t}\min\!\left(\frac{x}{R_x},\,1\right)\in[1,5]`,
    note: "Depth signals S_t (hours, lab hours, experiments) normalised by reference values R_x; no signal → D = 1 (fallback).",
  },
  {
    label: "Coverage",
    tex: String.raw`\mathrm{Coverage}(t) = C(t)\cdot\frac{1-e^{-\gamma D(t)}}{1-e^{-5\gamma}},\qquad \gamma = 0.5`,
    note: "C(t) ∈ {0, 1} is presence in the syllabus. Granular skills inherit coverage from their nearest high-level ancestor.",
  },
  {
    label: "Importance",
    tex: String.raw`I(t) = \frac{1}{N}\sum_{r=1}^{N}\max_{q\in r}\,\mathrm{credit}(q,t)`,
    note: "N = reports with at least one usable question; a question's credit is 1, or 60/40 when several topics match.",
  },
  {
    label: "Composite score",
    tex: String.raw`S_{\mathrm{comp}} = 100\cdot\frac{\sum_{t\in U} I(t)\,\mathrm{Coverage}(t)}{\sum_{t\in U} I(t)},\qquad U=\{t \mid I(t)>0\}`,
    note: "Computed only when N ≥ 15 (density gate).",
  },
  {
    label: "Priority gap",
    tex: String.raw`\mathrm{PriorityGap}(t) = I(t)\,\bigl(1-\mathrm{Coverage}(t)\bigr)`,
    note: "Ranked descending; ties broken by topic id.",
  },
];

export default function Methodology() {
  return (
    <>
      <PageHeader
        title="Methodology"
        lede="Every number in the dashboard comes from these formulas, applied to versioned inputs. Frozen constants change only with a new config version."
      />
      <div className="grid grid-cols-12 gap-4" data-testid="methodology">
        <Card className="col-span-12" title="Pipeline" testId="pipeline">
          <div className="flex items-center gap-3 overflow-x-auto pb-1">
            <div className="space-y-3">
              {LANES.map((lane) => (
                <div key={lane.label} className="flex items-center gap-2">
                  <span className="w-[4.5rem] shrink-0 text-[12px] font-medium uppercase tracking-wide text-ink-3">{lane.label}</span>
                  <ol className="flex items-center gap-2" aria-label={`${lane.label} pipeline`}>
                    {lane.steps.map((s, i) => (
                      <li key={s.title} className="flex items-center gap-2">
                        <Step {...s} />
                        {i < lane.steps.length - 1 && <ArrowRight size={14} className="shrink-0 text-ink-3" aria-hidden="true" />}
                      </li>
                    ))}
                  </ol>
                </div>
              ))}
            </div>
            <ArrowRight size={16} className="shrink-0 text-ink-3" aria-hidden="true" />
            <div className="rounded-md border border-primary bg-primary-soft px-3 py-3">
              <p className="text-[13px] font-semibold text-primary">S_comp + priority gaps</p>
              <p className="text-[12px] leading-snug text-ink-2">only if N ≥ 15 reports (density gate)</p>
            </div>
          </div>
        </Card>
        <Card className="col-span-8 max-[1150px]:col-span-12" title="Formulas" testId="formulas">
          <dl className="space-y-4">
            {FORMULAS.map((f) => (
              <div key={f.label}>
                <dt className="text-[12px] font-medium uppercase tracking-wide text-ink-3">{f.label}</dt>
                <dd>
                  <Tex block>{f.tex}</Tex>
                  <p className="text-[13px] text-ink-2">{f.note}</p>
                </dd>
              </div>
            ))}
          </dl>
        </Card>
        <Card className="col-span-4 max-[1150px]:col-span-12" title="Versioning" testId="versioning">
          <dl className="space-y-3 text-[14px]">
            {[
              ["Taxonomy", "v1.0 · 83 topics (37 high-level, 46 granular)"],
              ["Scoring config", "v1.2 · τ = 0.50, γ = 0.5, MIN_REPORTS = 15 (frozen)"],
              ["Results", "v1.2 · one file per target, never overwritten"],
              ["Benchmark", "v1.0 · 247 gold labels, grouped 70/15/15 split, seed 20261022"],
              ["Syllabus", "VIT CSE 2024-25, 25 of 26 core courses"],
            ].map(([k, v]) => (
              <div key={k}>
                <dt className="text-[12px] font-medium uppercase tracking-wide text-ink-3">{k}</dt>
                <dd className="text-ink">{v}</dd>
              </div>
            ))}
          </dl>
        </Card>
      </div>
    </>
  );
}
