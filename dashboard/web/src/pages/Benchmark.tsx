import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { BenchmarkResponse } from "../lib/api";
import { num } from "../lib/format";
import { useApi } from "../lib/useApi";
import { Card, ErrorState, Loading, PageHeader } from "../components/ui";

const SHORT: Record<string, string> = {
  keyword: "Keyword",
  tfidf: "TF-IDF",
  minilm_desc: "MiniLM desc. (prod.)",
  minilm_name_desc: "MiniLM name+desc.",
};

export default function Benchmark() {
  const { data, error, loading } = useApi<BenchmarkResponse>("/api/v1/benchmark");
  const chart = data
    ? Object.entries(data.methods).map(([id, m]) => ({ id, name: SHORT[id] ?? id, f1: m.test.overall.macro_f1 }))
    : [];
  const testSize = data ? data.split_sizes.test.syllabus + data.split_sizes.test.interview : 0;

  return (
    <>
      <PageHeader
        title="Benchmark"
        lede="Four topic matchers scored against the v1.0 gold labels (LLM-drafted, independently cross-checked, disagreements settled by the owner). Thresholds were chosen on dev and checked on val; test was held out from every choice."
      />
      {error && <ErrorState message={error} />}
      {loading && !data && <Loading />}
      {data && (
        <div className="grid grid-cols-12 gap-4" data-testid="benchmark">
          <Card className="col-span-8 max-[1150px]:col-span-12" title={`Test set (n = ${testSize})`} subtitle="Top-1 topic vs the gold primary label; macro averages include “none”." testId="method-table">
            <div className="overflow-x-auto">
              <table className="w-full text-[14px]">
                <thead>
                  <tr className="border-b border-line text-ink-2">
                    <th scope="col" className="whitespace-nowrap py-2 pr-3 text-left font-medium">Method</th>
                    <th scope="col" className="whitespace-nowrap px-2 py-2 text-right font-medium">τ (dev)</th>
                    <th scope="col" className="whitespace-nowrap px-2 py-2 text-right font-medium">Accuracy</th>
                    <th scope="col" className="whitespace-nowrap px-2 py-2 text-right font-medium">Macro-P</th>
                    <th scope="col" className="whitespace-nowrap px-2 py-2 text-right font-medium">Macro-R</th>
                    <th scope="col" className="whitespace-nowrap px-2 py-2 text-right font-medium">Macro-F1</th>
                    <th scope="col" className="whitespace-nowrap py-2 pl-2 text-right font-medium">Val F1</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(data.methods).map(([id, m]) => (
                    <tr key={id} className="border-b border-line last:border-b-0">
                      <td className="py-2 pr-3 text-ink">{data.method_labels[id] ?? id}</td>
                      <td className="tabular px-2 py-2 text-right">{m.threshold.toFixed(2)}</td>
                      <td className="tabular px-2 py-2 text-right">
                        {num(m.test.overall.accuracy)}{" "}
                        <span className="text-[12px] text-ink-3">({m.test.overall.correct}/{m.test.overall.n})</span>
                      </td>
                      <td className="tabular px-2 py-2 text-right">{num(m.test.overall.macro_precision)}</td>
                      <td className="tabular px-2 py-2 text-right">{num(m.test.overall.macro_recall)}</td>
                      <td className="tabular px-2 py-2 text-right font-semibold">{num(m.test.overall.macro_f1)}</td>
                      <td className="tabular py-2 pl-2 text-right text-ink-2">{num(m.val.overall.macro_f1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 rounded-md bg-surface-2 p-3 text-[13px] text-ink-2" data-testid="recommendation">
              {data.recommendation}
            </p>
          </Card>

          <Card className="col-span-4 max-[1150px]:col-span-12" title="Label agreement" subtitle="Gold labels: LLM draft, independent second labeller, human adjudication." testId="kappa-card">
            <p className="tabular text-[48px] font-semibold leading-none text-ink" data-testid="kappa">
              {data.label_agreement.kappa_draft_vs_second_labeller.toFixed(3)}
            </p>
            <p className="mt-1 text-[13px] text-ink-3">Cohen's κ, draft vs second labeller (primary label)</p>
            <dl className="tabular mt-4 grid grid-cols-3 gap-2 text-[14px]">
              <div><dt className="text-[12px] text-ink-3">Agree</dt><dd className="font-medium">{data.label_agreement.agree}</dd></div>
              <div><dt className="text-[12px] text-ink-3">Partial</dt><dd className="font-medium">{data.label_agreement.partial}</dd></div>
              <div><dt className="text-[12px] text-ink-3">Disagree</dt><dd className="font-medium">{data.label_agreement.disagree}</dd></div>
            </dl>
            <p className="mt-3 text-[13px] text-ink-2">
              {data.label_agreement.rule_adjudicated + data.label_agreement.human_adjudicated} rows settled by the owner
              ({data.label_agreement.rule_adjudicated} by rule, {data.label_agreement.human_adjudicated} individually).
            </p>
          </Card>

          <Card className="col-span-6 max-[1150px]:col-span-12" title="Test macro-F1 per method" testId="f1-chart">
            <div className="h-[240px]" role="img" aria-label="Bar chart of test macro-F1 per method">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chart} margin={{ top: 22, right: 8, bottom: 4, left: 0 }}>
                  <CartesianGrid vertical={false} stroke="var(--line)" />
                  <XAxis dataKey="name" tick={{ fill: "var(--ink-2)", fontSize: 12 }} axisLine={{ stroke: "var(--line)" }} tickLine={false} interval={0} />
                  <YAxis domain={[0, 1]} tick={{ fill: "var(--ink-3)", fontSize: 12 }} axisLine={false} tickLine={false} width={34} />
                  <Tooltip
                    cursor={{ fill: "var(--surface-2)" }}
                    contentStyle={{ background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 6, fontSize: 13 }}
                    labelStyle={{ color: "var(--ink)" }}
                    itemStyle={{ color: "var(--ink-2)" }}
                    formatter={(v: unknown) => [num(Number(v)), "Test macro-F1"]}
                  />
                  <Bar dataKey="f1" fill="var(--series)" radius={[4, 4, 0, 0]} barSize={44} isAnimationActive={false}>
                    <LabelList dataKey="f1" position="top" formatter={(v: unknown) => num(Number(v))} fill="var(--ink)" fontSize={12} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card className="col-span-6 max-[1150px]:col-span-12" title="Limitations" testId="limitations">
            <ul className="list-disc space-y-1.5 pl-5 text-[13px] text-ink-2">
              {data.limitations.map((l) => (
                <li key={l}>{l.replace(/\*\*/g, "").replace(/`/g, "")}</li>
              ))}
            </ul>
          </Card>
        </div>
      )}
    </>
  );
}
