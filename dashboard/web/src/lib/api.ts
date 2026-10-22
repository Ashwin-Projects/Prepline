// Typed client for the read-only dashboard endpoints (backend/dashboard.py).
export const API_BASE: string = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export interface TargetSummary {
  id: string;
  company: string;
  role: string;
  results_available: boolean;
  status: "SUCCESS" | "INSUFFICIENT_DATA" | null;
  S_comp: number | null;
}

export interface Gap {
  rank: number;
  topic_id: string;
  topic_name: string;
  importance: number;
  coverage: number;
  priority_gap: number;
}

export interface Topic {
  topic_id: string;
  topic_name: string;
  domain: string;
  type: "high_level_concept" | "granular_skill";
  importance: number | null;
  coverage: number;
  priority_gap: number | null;
  depth: number;
  depth_status: "measured" | "fallback";
  presence: number;
  coverage_source: "direct" | "inherited";
  inherited_from: string | null;
}

export interface Result {
  status: "SUCCESS" | "INSUFFICIENT_DATA";
  S_comp: number | null;
  report_count: number;
  taxonomy_version: string | null;
  scoring_config_version: string;
  scoring_config: { gamma: number; similarity_threshold: number };
  generated_at: string;
  syllabus_id: string;
  syllabus_files: string[];
  interview_filter: { questions_total: number; questions_included: number; questions_excluded: number };
  scoring_universe_size?: number;
  topics_present?: number;
  topics_in_taxonomy?: number;
  depth_counts?: { all_topics: Record<string, number>; present_topics: Record<string, number> };
  top_priority_gaps?: Gap[];
  unmapped_terms_summary?: {
    distinct_terms: number;
    total_occurrences: number;
    distinct_terms_by_source_type: Record<string, number>;
  };
  top_unmapped_terms?: { term: string; source_type: string; occurrences: number }[];
}

export interface ResultsResponse {
  target: { id: string; company: string; role: string };
  result: Result;
  raw_report_count: number;
  min_reports: number;
  topics: Topic[];
}

export interface ComparisonRow {
  target_id: string;
  company: string;
  role: string;
  results_available: boolean;
  status: "SUCCESS" | "INSUFFICIENT_DATA" | null;
  S_comp: number | null;
  raw_report_count: number;
  report_count: number | null;
  min_reports: number;
  density_gate_passed: boolean;
  scoring_universe_size: number | null;
  fallback_topics: number | null;
  topics_in_taxonomy: number | null;
  unmapped_distinct_terms: number | null;
  top_priority_gaps: Gap[];
  generated_at: string | null;
}

export interface Metrics {
  n: number;
  correct: number;
  accuracy: number;
  macro_precision: number;
  macro_recall: number;
  macro_f1: number;
}

export interface SplitReport {
  overall: Metrics;
  by_source_type: Record<string, Metrics>;
  by_domain: Record<string, Metrics>;
}

export interface BenchmarkResponse {
  benchmark_version: string;
  generated_at: string;
  production_threshold: number;
  thresholds_swept: number[];
  selection_rule: string;
  split_sizes: Record<
    string,
    { syllabus: number; interview: number; syllabus_groups: string[]; interview_groups: string[] }
  >;
  methods: Record<
    string,
    { description: string; threshold: number; dev: SplitReport; val: SplitReport; test: SplitReport }
  >;
  method_labels: Record<string, string>;
  label_agreement: {
    kappa_draft_vs_second_labeller: number;
    agree: number;
    partial: number;
    disagree: number;
    rule_adjudicated: number;
    human_adjudicated: number;
    llm_cross_checked_only: number;
  };
  limitations: string[];
  recommendation: string;
}

export async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { signal });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText} for ${path}`);
  return (await response.json()) as T;
}

export interface PilotSummary {
  n: number;
  M1_topic_hit_rate?: number | null;
  M1_topic_hit_rate_n?: number;
  M2_gap_relevance?: number | null;
  M2_gap_relevance_n?: number;
  M2b_perceived_match?: number | null;
  M2b_perceived_match_n?: number;
  M3_usefulness: number | null;
  M3_usefulness_n: number;
}

export interface PilotTrack {
  by_company: Record<string, PilotSummary>;
  overall: PilotSummary;
}

export interface PilotResponse {
  status: "in_progress" | "results_available";
  results: null | {
    generated_at: string;
    n_responses: number;
    n_excluded_no_consent: number;
    synthetic: boolean;
    tracks: { A: PilotTrack; B: PilotTrack };
    M3_all_participants: PilotSummary;
  };
}

export interface ValidationCompany {
  target_id: string;
  label: string;
  n_reports: number;
  n_folds_scored: number;
  hit_rate: number | null;
  baseline: { mean: number; p2_5: number; p97_5: number; draws: number; seed: number };
}

export interface ValidationResponse {
  available: boolean;
  results: null | { label: string; generated_at: string; top_k: number; draws: number; seed: number; companies: ValidationCompany[] };
}
