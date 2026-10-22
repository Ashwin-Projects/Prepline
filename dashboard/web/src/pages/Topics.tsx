import { useMemo, useState } from "react";
import { ArrowDown, ArrowUp, Search } from "lucide-react";
import type { ResultsResponse, Topic } from "../lib/api";
import { domainName, domainShort, num, pct } from "../lib/format";
import { useTarget } from "../lib/target";
import { useApi } from "../lib/useApi";
import { TargetSelect } from "../components/TargetSelect";
import { ErrorState, Loading, PageHeader } from "../components/ui";

type SortKey = "topic_name" | "domain" | "importance" | "coverage" | "depth" | "priority_gap";

const COLUMNS: { key: SortKey; label: string; numeric?: boolean }[] = [
  { key: "topic_name", label: "Topic" },
  { key: "domain", label: "Domain" },
  { key: "importance", label: "Importance", numeric: true },
  { key: "coverage", label: "Coverage", numeric: true },
  { key: "depth", label: "Depth D(t)", numeric: true },
  { key: "priority_gap", label: "Priority gap", numeric: true },
];

export function filterTopics(topics: Topic[], query: string, domain: string): Topic[] {
  const q = query.trim().toLowerCase();
  return topics.filter(
    (t) =>
      (domain === "all" || t.domain === domain) &&
      (!q || t.topic_name.toLowerCase().includes(q) || t.topic_id.toLowerCase().includes(q)),
  );
}

export default function Topics() {
  const { target } = useTarget();
  const { data, error, loading } = useApi<ResultsResponse>(`/api/v1/results/${target}`);
  const [query, setQuery] = useState("");
  const [domain, setDomain] = useState("all");
  const [sort, setSort] = useState<{ key: SortKey; desc: boolean }>({ key: "priority_gap", desc: true });

  const rows = useMemo(() => {
    if (!data) return [];
    const list = filterTopics(data.topics, query, domain);
    const value = (t: Topic) => t[sort.key] ?? -1;
    return [...list].sort((a, b) => {
      const av = value(a), bv = value(b);
      const cmp = typeof av === "string" ? String(av).localeCompare(String(bv)) : Number(av) - Number(bv);
      return (sort.desc ? -cmp : cmp) || a.topic_id.localeCompare(b.topic_id);
    });
  }, [data, query, domain, sort]);

  const domains = useMemo(() => (data ? [...new Set(data.topics.map((t) => t.domain))].sort() : []), [data]);
  const scored = data?.result.status === "SUCCESS";

  return (
    <>
      <PageHeader
        title="Topic explorer"
        lede="All 83 taxonomy topics with interview importance, syllabus coverage and depth. Granular skills inherit coverage from their high-level parent."
        actions={<TargetSelect />}
      />
      {error && <ErrorState message={error} />}
      {loading && !data && <Loading />}
      {data && (
        <section className="rounded-lg border border-line bg-surface" data-testid="topic-explorer">
          <div className="flex flex-wrap items-center gap-3 border-b border-line p-3">
            <label className="relative flex-1 basis-64">
              <span className="sr-only">Search topics</span>
              <Search size={15} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-3" aria-hidden="true" />
              <input
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search topics, e.g. graph, sql, paging"
                className="w-full rounded-md border border-line bg-bg py-1.5 pl-8 pr-3 text-[14px] text-ink placeholder:text-ink-3"
                data-testid="topic-search"
              />
            </label>
            <label className="flex items-center gap-2 text-[13px] text-ink-2">
              Domain
              <select
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                className="cursor-pointer rounded-md border border-line bg-bg px-2 py-1.5 text-[14px] text-ink"
              >
                <option value="all">All domains</option>
                {domains.map((d) => (
                  <option key={d} value={d}>
                    {domainName(d)}
                  </option>
                ))}
              </select>
            </label>
            <span className="tabular text-[13px] text-ink-3" data-testid="topic-count">
              {rows.length} of {data.topics.length} topics
            </span>
          </div>
          {data.topics.length === 0 && (
            <p className="border-b border-line bg-surface-2 px-3 py-2 text-[13px] text-ink-2" role="status">
              No topic table has been exported for this target. Run{" "}
              <code className="font-mono">python evaluation/export_topic_tables.py</code> after its results file exists.
            </p>
          )}
          {!scored && data.topics.length > 0 && (
            <p className="border-b border-line bg-surface-2 px-3 py-2 text-[13px] text-ink-2" role="status">
              Importance and priority gap are not computed for {data.target.company} {data.target.role}: below the
              density gate. Coverage is the same syllabus for every company.
            </p>
          )}
          <div className="max-[900px]:overflow-x-auto">
            <table className="w-full border-collapse text-[14px]">
              <thead className="sticky top-0 z-10 bg-surface shadow-[0_1px_0_var(--line)]">
                <tr className="border-b border-line">
                  {COLUMNS.map((c) => (
                    <th
                      key={c.key}
                      scope="col"
                      aria-sort={sort.key === c.key ? (sort.desc ? "descending" : "ascending") : "none"}
                      className={`px-3 py-2 font-medium text-ink-2 ${c.numeric ? "text-right" : "text-left"}`}
                    >
                      <button
                        type="button"
                        className="inline-flex cursor-pointer items-center gap-1 hover:text-ink"
                        onClick={() => setSort((s) => ({ key: c.key, desc: s.key === c.key ? !s.desc : c.numeric === true }))}
                      >
                        {c.label}
                        {sort.key === c.key &&
                          (sort.desc ? <ArrowDown size={13} aria-hidden="true" /> : <ArrowUp size={13} aria-hidden="true" />)}
                      </button>
                    </th>
                  ))}
                  <th scope="col" className="px-3 py-2 text-left font-medium text-ink-2">Depth status</th>
                  <th scope="col" className="px-3 py-2 text-left font-medium text-ink-2">Coverage source</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((t) => (
                  <tr key={t.topic_id} className="border-b border-line last:border-b-0 hover:bg-surface-2">
                    <td className="max-w-[20rem] px-3 py-1.5">
                      <span className="block truncate text-ink" title={t.topic_name}>{t.topic_name}</span>
                      <span className="block truncate font-mono text-[11px] text-ink-3">{t.topic_id}</span>
                    </td>
                    <td className="whitespace-nowrap px-3 py-1.5 text-ink-2" title={domainName(t.domain)}>{domainShort(t.domain)}</td>
                    <td className="tabular px-3 py-1.5 text-right">{num(t.importance)}</td>
                    <td className="tabular px-3 py-1.5 text-right">{pct(t.coverage, 1)}</td>
                    <td className="tabular px-3 py-1.5 text-right">{num(t.depth, 2)}</td>
                    <td className="tabular px-3 py-1.5 text-right font-medium">{num(t.priority_gap)}</td>
                    <td className="px-3 py-1.5">
                      <span
                        className={`rounded px-1.5 py-0.5 text-[12px] ${
                          t.depth_status === "measured" ? "bg-good-soft text-good" : "bg-warn-soft text-warn"
                        }`}
                      >
                        {t.depth_status}
                      </span>
                    </td>
                    <td className="px-3 py-1.5 text-[13px] text-ink-2">
                      {t.coverage_source === "inherited" ? (
                        <>
                          <span className="block">inherited</span>
                          <span className="block font-mono text-[11px] text-ink-3">← {t.inherited_from}</span>
                        </>
                      ) : (
                        "direct"
                      )}
                    </td>
                  </tr>
                ))}
                {rows.length === 0 && data.topics.length > 0 && (
                  <tr>
                    <td colSpan={8} className="px-3 py-8 text-center text-ink-3">
                      No topics match “{query}”.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </>
  );
}
