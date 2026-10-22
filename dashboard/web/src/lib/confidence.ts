import type { Result } from "./api";

export type ConfidenceLevel = "High" | "Medium" | "Low" | "Insufficient data";

export interface Confidence {
  level: ConfidenceLevel;
  reasons: string[];
}

// Badge from the indicators the Confidence page explains: report margin above the density gate, the size of the
// scoring universe, and fallback depth among covered topics. No reasons -> High, one -> Medium, more -> Low.
export function confidenceOf(result: Result, minReports: number): Confidence {
  if (result.status !== "SUCCESS") {
    return {
      level: "Insufficient data",
      reasons: [`${result.report_count} of ${minReports} reports needed after filtering`],
    };
  }
  const reasons: string[] = [];
  const margin = result.report_count - minReports;
  if (margin < 3) reasons.push(`only ${margin} report${margin === 1 ? "" : "s"} above the ${minReports}-report gate`);
  const universe = result.scoring_universe_size ?? 0;
  if (universe < 10) reasons.push(`S_comp rests on ${universe} interview topics`);
  const presentFallback = result.depth_counts?.present_topics?.fallback ?? 0;
  if (presentFallback > 0) reasons.push(`${presentFallback} covered topics use fallback depth`);
  const level: ConfidenceLevel = reasons.length === 0 ? "High" : reasons.length === 1 ? "Medium" : "Low";
  return { level, reasons };
}
