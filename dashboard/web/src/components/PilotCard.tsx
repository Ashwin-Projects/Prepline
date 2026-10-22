import type { PilotResponse, PilotSummary } from "../lib/api";
import { date, num, pct } from "../lib/format";
import { useApi } from "../lib/useApi";
import { Card } from "./ui";

const TRACKS = [
  ["Track A", "Students who took an online assessment or interview (any outcome, internships included): topics asked, top-10 gap ratings, usefulness."],
  ["Track B", "Any CSE student after about 5 minutes on this dashboard: “these gaps match my perceived weak areas” (1–5), usefulness."],
];

function cell(value: number | null | undefined, n: number | undefined, asPct = false) {
  return value === null || value === undefined ? "n/a" : `${asPct ? pct(value) : num(value, 2)} (${n ?? 0})`;
}

const th = "px-2 py-1.5 text-right font-medium";
const td = "tabular px-2 py-1.5 text-right";

function TrackTable({ title, rows, kind, testId }: {
  title: string;
  rows: [string, PilotSummary][];
  kind: "A" | "B";
  testId: string;
}) {
  return (
    <div>
      <h3 className="mb-1 text-[13px] font-semibold text-ink">{title}</h3>
      <table className="w-full text-[14px]" data-testid={testId}>
        <thead>
          <tr className="border-b border-line text-ink-2">
            <th scope="col" className="py-1.5 pr-3 text-left font-medium">Company</th>
            <th scope="col" className={th}>n</th>
            {kind === "A" ? (
              <>
                <th scope="col" className={th}>M1 hit rate (n)</th>
                <th scope="col" className={th}>M2 relevance (n)</th>
              </>
            ) : (
              <th scope="col" className={th}>M2b perceived match (n)</th>
            )}
            <th scope="col" className={th}>M3 usefulness (n)</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([label, s]) => (
            <tr key={label} className="border-b border-line last:border-b-0">
              <td className="py-1.5 pr-3 text-ink">{label}</td>
              <td className={td}>{s.n}</td>
              {kind === "A" ? (
                <>
                  <td className={td}>{cell(s.M1_topic_hit_rate, s.M1_topic_hit_rate_n, true)}</td>
                  <td className={td}>{cell(s.M2_gap_relevance, s.M2_gap_relevance_n)}</td>
                </>
              ) : (
                <td className={td}>{cell(s.M2b_perceived_match, s.M2b_perceived_match_n)}</td>
              )}
              <td className={td}>{cell(s.M3_usefulness, s.M3_usefulness_n)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Phase 16 pilot (students only, two tracks): pre-registered design while in progress, descriptive results once analysed.
export function PilotCard({ className = "" }: { className?: string }) {
  const { data } = useApi<PilotResponse>("/api/v1/pilot");
  const results = data?.results ?? null;
  return (
    <Card
      className={className}
      title="Participant pilot (Phase 16)"
      subtitle="Students only, two tracks; pre-registered in docs/pilot/PILOT_PROTOCOL.md. Descriptive only, reported per track with its n."
      testId="pilot"
    >
      {!results ? (
        <div className="space-y-3">
          <p className="inline-flex items-center rounded-full bg-warn-soft px-2.5 py-0.5 text-[13px] font-medium text-warn" data-testid="pilot-status">
            In progress — no responses analysed yet
          </p>
          <dl className="grid grid-cols-2 gap-4 text-[13px] max-[900px]:grid-cols-1">
            {TRACKS.map(([name, detail]) => (
              <div key={name}>
                <dt className="font-medium text-ink">{name}</dt>
                <dd className="text-ink-2">{detail}</dd>
              </div>
            ))}
          </dl>
          <p className="text-[13px] text-ink-3">
            No inferential statistics at n = 10–20 per track. γ calibration is deferred (it needs round-level outcomes
            and a larger sample).
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-[13px] text-ink-2" data-testid="pilot-status">
            Track A {results.tracks.A.overall.n}, Track B {results.tracks.B.overall.n} participants (
            {results.n_excluded_no_consent} excluded without consent), analysed {date(results.generated_at)}.
            Usefulness over both tracks: {cell(results.M3_all_participants.M3_usefulness, results.M3_all_participants.M3_usefulness_n)}.
          </p>
          {results.synthetic && <p role="alert" className="font-medium text-bad">SYNTHETIC DATA — not pilot results.</p>}
          <TrackTable
            title="Track A — took an assessment or interview"
            kind="A"
            testId="pilot-table-a"
            rows={[...Object.entries(results.tracks.A.by_company), ["All Track A", results.tracks.A.overall]]}
          />
          <TrackTable
            title="Track B — after 5 minutes on the dashboard (perceived, not tested)"
            kind="B"
            testId="pilot-table-b"
            rows={[...Object.entries(results.tracks.B.by_company), ["All Track B", results.tracks.B.overall]]}
          />
        </div>
      )}
    </Card>
  );
}
