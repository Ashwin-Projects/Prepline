import type { ValidationResponse } from "../lib/api";
import { pct } from "../lib/format";
import { useApi } from "../lib/useApi";
import { Card } from "./ui";

// Retrospective leave-one-report-out check on the collected reports; explicitly not the participant pilot.
export function ValidationCard({ className = "" }: { className?: string }) {
  const { data } = useApi<ValidationResponse>("/api/v1/validation");
  const results = data?.results ?? null;
  return (
    <Card
      className={className}
      title="Retrospective validation — not the participant pilot"
      subtitle="Leave-one-report-out: is a held-out report's topic set already in the top-10 important topics of the other reports?"
      testId="retro-validation"
    >
      {!results ? (
        <p className="text-[14px] text-ink-3">Not run yet (python evaluation/retro_validation.py).</p>
      ) : (
        <>
          <table className="w-full text-[14px]" data-testid="retro-table">
            <thead>
              <tr className="border-b border-line text-ink-2">
                <th scope="col" className="py-1.5 pr-3 text-left font-medium">Company</th>
                <th scope="col" className="px-2 py-1.5 text-right font-medium">Reports (scored)</th>
                <th scope="col" className="px-2 py-1.5 text-right font-medium">PREPLINE top-{results.top_k} hit rate</th>
                <th scope="col" className="py-1.5 pl-2 text-right font-medium">Random baseline (95 % of draws)</th>
              </tr>
            </thead>
            <tbody>
              {results.companies.map((c) => (
                <tr key={c.target_id} className="border-b border-line last:border-b-0">
                  <td className="py-1.5 pr-3 text-ink">{c.label}</td>
                  <td className="tabular px-2 py-1.5 text-right">
                    {c.n_reports} ({c.n_folds_scored})
                  </td>
                  <td className="tabular px-2 py-1.5 text-right font-semibold">{pct(c.hit_rate, 1)}</td>
                  <td className="tabular py-1.5 pl-2 text-right text-ink-2">
                    {pct(c.baseline.mean, 1)} ({pct(c.baseline.p2_5, 1)}–{pct(c.baseline.p97_5, 1)})
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-[12px] text-ink-3">
            Same public reports PREPLINE is built from; held-out topics use the same matcher, so mapping errors are not
            tested here. Baseline: {results.draws} seeded random draws (seed {results.seed}) of the same number of
            topics; the interval describes the draws, not a significance test. Details: results/validation/RETRO_VALIDATION.md.
          </p>
        </>
      )}
    </Card>
  );
}
