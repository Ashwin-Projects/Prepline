import type { ComparisonRow, ResultsResponse, Topic } from "../lib/api";
import { domainName } from "../lib/format";

// Everything the story shows comes from these two saved-results responses; nothing is hard-coded.
export interface StoryData {
  results: ResultsResponse;
  comparison: ComparisonRow[];
}

// Course codes (e.g. BCSE202L) from syllabus file names; theory and lab PDFs of one course stay separate codes.
export function courseCodes(files: string[]): string[] {
  const codes = new Set<string>();
  for (const file of files) {
    const base = file.split(/[\\/]/).pop() ?? file;
    const match = /^(B[A-Z]{3}\d{3}[A-Z])/.exec(base);
    if (match) codes.add(match[1]);
  }
  return [...codes].sort();
}

export interface TopicBreakdown {
  total: number;
  byDomain: { domain: string; name: string; count: number }[];
  highLevel: number;
  granular: number;
}

export function topicBreakdown(topics: Topic[]): TopicBreakdown {
  const counts = new Map<string, number>();
  for (const t of topics) counts.set(t.domain, (counts.get(t.domain) ?? 0) + 1);
  const byDomain = [...counts.entries()]
    .map(([domain, count]) => ({ domain, name: domainName(domain), count }))
    .sort((a, b) => b.count - a.count || a.domain.localeCompare(b.domain));
  const highLevel = topics.filter((t) => t.type === "high_level_concept").length;
  return { total: topics.length, byDomain, highLevel, granular: topics.length - highLevel };
}

export interface EvidenceRow {
  id: string;
  label: string;
  raw: number;
  usable: number | null;
  min: number;
  passed: boolean;
}

export function evidenceRows(rows: ComparisonRow[]): EvidenceRow[] {
  return rows.map((r) => ({
    id: r.target_id,
    label: `${r.company} ${r.role}`,
    raw: r.raw_report_count,
    usable: r.report_count,
    min: r.min_reports,
    passed: r.density_gate_passed,
  }));
}

// Deterministic pseudo-random numbers in [0, 1) so scattered layouts are identical on every render and visit.
export function seeded(seed: number): () => number {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
