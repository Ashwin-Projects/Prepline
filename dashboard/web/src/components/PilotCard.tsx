import type { PilotResponse, PilotSummary } from "../lib/api";
import { date, num, pct } from "../lib/format";
import { useApi } from "../lib/useApi";
import { Card } from "./ui";

const METRICS = [
  ["M1 Topic hit rate", "Share of the topics a student was actually asked that are in PREPLINE's top-10 important topics for that company."],
  ["M2 Gap relevance", "Mean 1–5 rating of “this gap matched my real weak areas” over the top-10 gaps shown."],
  ["M3 Usefulness", "Mean of 5 usability items (1–5)."],
];

function cell(value: number | null, n: number, asPct = false) {
  return value === null ? "n/a" : `${asPct ? pct(value) : num(value, 2)} (${n})`;
}

function Row({ label, s }: { label: string; s: PilotSummary }) {
  return (
    <tr className="border-b border-line last:border-b-0">
      <td className="py-1.5 pr-3 text-ink">{label}</td>
      <td className="tabular px-2 py-1.5 text-right">{s.n}</td>
      <td className="tabular px-2 py-1.5 text-right">{cell(s.M1_topic_hit_rate, s.M1_topic_hit_rate_n, true)}</td>
      <td className="tabular px-2 py-1.5 text-right">{cell(s.M2_gap_relevance, s.M2_gap_relevance_n)}</td>
      <td className="tabular py-1.5 pl-2 text-right">{cell(s.M3_usefulness, s.M3_usefulness_n)}</td>
    </tr>
  );
}

// Phase 16 pilot: pre-registered metrics while in progress, and the descriptive results once analysed.
export function PilotCard({ className = "" }: { className?: string }) {
  const { data } = useApi<PilotResponse>("/api/v1/pilot");
  const results = data?.results ?? null;
  return (
    <Card
      className={className}
      title="Pilot (Phase 16)"
      subtitle="Small descriptive pilot with VIT CSE students who interviewed at these companies; pre-registered in docs/pilot/PILOT_PROTOCOL.md."
      testId="pilot"
    >
      {!results ? (
        <div className="space-y-3">
          <p className="inline-flex items-center rounded-full bg-warn-soft px-2.5 py-0.5 text-[13px] font-medium text-warn" data-testid="pilot-status">
            In progress — no responses analysed yet
          </p>
          <dl className="grid grid-cols-3 gap-4 text-[13px] max-[900px]:grid-cols-1">
            {METRICS.map(([name, detail]) => (
              <div key={name}>
                <dt className="font-medium text-ink">{name}</dt>
                <dd className="text-ink-2">{detail}</dd>
              </div>
            ))}
          </dl>
          <p className="text-[13px] text-ink-3">
            Descriptive only: no inferential statistics at n = 10–20. γ calibration is deferred (it needs round-level
            outcomes and a larger sample).
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-[13px] text-ink-2" data-testid="pilot-status">
            Results from {results.overall.n} participants ({results.n_excluded_no_consent} excluded without consent),
            analysed {date(results.generated_at)}. Descriptive only.
          </p>
          {results.synthetic && (
            <p role="alert" className="font-medium text-bad">SYNTHETIC DATA — not pilot results.</p>
          )}
          <table className="w-full text-[14px]" data-testid="pilot-table">
            <thead>
              <tr className="border-b border-line text-ink-2">
                <th scope="col" className="py-1.5 pr-3 text-left font-medium">Company</th>
                <th scope="col" className="px-2 py-1.5 text-right font-medium">n</th>
                <th scope="col" className="px-2 py-1.5 text-right font-medium">M1 hit rate (n)</th>
                <th scope="col" className="px-2 py-1.5 text-right font-medium">M2 relevance (n)</th>
                <th scope="col" className="py-1.5 pl-2 text-right font-medium">M3 usefulness (n)</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(results.by_company).map(([label, s]) => (
                <Row key={label} label={label} s={s} />
              ))}
              <Row label="All participants" s={results.overall} />
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
