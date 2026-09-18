"""
Scoring Engine Module (Phases 8–11)

Phase 8: Syllabus Topic Presence, Workload Depth Modeling & Coverage Calculation
Phase 9: Per-Report Topic Importance (Pending)
Phase 10: Overall Composite Alignment Score S_comp (Pending)
Phase 11: Priority Gap Ranking (Pending)
"""

import json
import math
import os
from typing import Dict, Any, List, Optional, Union, Tuple

DEFAULT_TAXONOMY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "taxonomy",
    "taxonomy_v1.0.json"
)

DEFAULT_TAXONOMY_VERSION = "v1.0"
GAMMA_DEFAULT = 0.5  # MVP baseline depth decay constant

# Exact MVP reference values for depth signal normalization
MVP_REFERENCE_VALUES = {
    "unit_hours": 10.0,
    "slide_count": 20.0,
    "slides": 20.0,
    "lab_hours": 10.0,
    "lab_count": 5.0,
    "assignment_count": 5.0,
    "assignments": 5.0
}


def load_taxonomy_nodes(taxonomy_input: Union[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Loads and returns taxonomy nodes from a list of dicts or a JSON file path."""
    if isinstance(taxonomy_input, list):
        return taxonomy_input
    elif isinstance(taxonomy_input, str):
        if not os.path.exists(taxonomy_input):
            raise FileNotFoundError(f"Taxonomy file not found at path: {taxonomy_input}")
        with open(taxonomy_input, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["nodes"] if isinstance(data, dict) and "nodes" in data else data
    else:
        raise ValueError("taxonomy_input must be a file path string or a list of node dictionaries.")


def normalize_signal(signal_key: str, raw_val: Optional[Union[int, float]]) -> Optional[float]:
    """
    Computes N(x) = min(x / R_x, 1.0) for a given signal if raw_val is not None.
    Returns None if raw_val is missing/None or invalid.
    """
    if raw_val is None:
        return None
    ref_val = MVP_REFERENCE_VALUES.get(signal_key)
    if ref_val is None or ref_val <= 0:
        return None
    
    try:
        val = float(raw_val)
        if val < 0:
            return None
        return min(val / ref_val, 1.0)
    except (ValueError, TypeError):
        return None


def calculate_syllabus_coverage(
    parsed_syllabus_dict: Dict[str, Any],
    taxonomy_nodes: Union[str, List[Dict[str, Any]]] = DEFAULT_TAXONOMY_PATH,
    gamma: float = GAMMA_DEFAULT
) -> Dict[str, Any]:
    """
    Phase 8: Calculates syllabus-wide topic presence C(t), workload depth D(t), depth_status,
    and normalized coverage Coverage(t) for all taxonomy topics.

    Mathematical formulation:
    - C(t) = 1 if topic t is matched in any syllabus module, else 0
    - N(x) = min(x / R_x, 1.0) for available non-None depth signals
    - D_norm(t) = sum(N(x)) / number_of_available_signals
    - D(t) = 1.0 + 4.0 * D_norm(t)  (1.0 <= D(t) <= 5.0)
    - If no signals available: D(t) = 1.0, depth_status = "fallback", depth_signal_count = 0
    - If signals available: depth_status = "measured", depth_signal_count = count
    - Coverage(t) = C(t) * [(1 - exp(-gamma * D(t))) / (1 - exp(-5 * gamma))]
    """
    nodes = load_taxonomy_nodes(taxonomy_nodes)
    taxonomy_version = parsed_syllabus_dict.get("taxonomy_version", DEFAULT_TAXONOMY_VERSION)
    syllabus_id = parsed_syllabus_dict.get("syllabus_id", "UNKNOWN")

    two_pass_mappings = parsed_syllabus_dict.get("two_pass_mappings", [])

    # 1. Collect matched topic IDs and depth signals across all syllabus modules
    topic_signals_map: Dict[str, List[float]] = {}
    present_topics = set()

    for mapping in two_pass_mappings:
        matched_ids = mapping.get("matched_topic_ids", [])
        depth_signals = mapping.get("depth_signals", {}) or {}

        # Extract non-None normalized depth signals from this module
        module_norm_signals = []
        for sig_key, raw_val in depth_signals.items():
            norm_val = normalize_signal(sig_key, raw_val)
            if norm_val is not None:
                module_norm_signals.append(norm_val)

        for topic_id in matched_ids:
            present_topics.add(topic_id)
            if topic_id not in topic_signals_map:
                topic_signals_map[topic_id] = []
            topic_signals_map[topic_id].extend(module_norm_signals)

    # Pre-calculate gamma normalization denominator: 1 - exp(-5 * gamma)
    denom = 1.0 - math.exp(-5.0 * gamma)

    topic_coverage_list = []

    # 2. Iterate over all taxonomy topics
    for node in nodes:
        topic_id = node["topic_id"]
        topic_name = node.get("name", topic_id)

        is_present = 1 if topic_id in present_topics else 0

        signals = topic_signals_map.get(topic_id, [])
        signal_count = len(signals)

        if signal_count > 0:
            d_norm = sum(signals) / float(signal_count)
            depth = 1.0 + 4.0 * d_norm
            depth_status = "measured"
            depth_signal_count = signal_count
        else:
            depth = 1.0
            depth_status = "fallback"
            depth_signal_count = 0

        # Ensure depth is strictly bounded in [1.0, 5.0]
        depth = max(1.0, min(5.0, depth))

        if is_present == 1:
            coverage = (1.0 - math.exp(-gamma * depth)) / denom
            coverage = max(0.0, min(1.0, coverage))
        else:
            coverage = 0.0

        topic_coverage_list.append({
            "topic_id": topic_id,
            "topic_name": topic_name,
            "presence": is_present,
            "depth": round(depth, 4),
            "coverage": round(coverage, 4),
            "depth_status": depth_status,
            "depth_signal_count": depth_signal_count,
            "taxonomy_version": taxonomy_version
        })

    return {
        "syllabus_id": syllabus_id,
        "taxonomy_version": taxonomy_version,
        "topic_coverage": topic_coverage_list
    }


def calculate_topic_importance(
    questions_input: Union[str, List[Dict[str, Any]], Any],
    total_reports_count: int = 21,
    taxonomy_nodes: Union[str, List[Dict[str, Any]]] = DEFAULT_TAXONOMY_PATH
) -> Dict[str, Any]:
    """
    Phase 9: Calculates per-report topic importance I(t) for all taxonomy topics.

    Mathematical formulation:
    - For each question q in report r, compute topic credits via taxonomy_mapper.map_source_to_taxonomy()
    - W(r,t) = max_{q in r} (credit(q,t))  (max credit for topic t within report r)
    - I(t) = sum_{r} W(r,t) / total_reports_count
    - 0 <= I(t) <= 1.0
    """
    from pipeline.taxonomy_mapper import map_source_to_taxonomy, DEFAULT_TAXONOMY_VERSION

    nodes = load_taxonomy_nodes(taxonomy_nodes)
    if total_reports_count <= 0:
        raise ValueError("total_reports_count must be a positive integer.")

    # 1. Parse questions_input into a standardized list of dicts
    question_records: List[Dict[str, Any]] = []

    if isinstance(questions_input, str):
        if not os.path.exists(questions_input):
            raise FileNotFoundError(f"Questions CSV file not found at path: {questions_input}")
        import csv
        with open(questions_input, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                question_records.append(dict(row))
    elif isinstance(questions_input, list):
        question_records = questions_input
    elif hasattr(questions_input, "to_dict"):  # pandas DataFrame
        question_records = questions_input.to_dict(orient="records")
    else:
        raise ValueError("questions_input must be a CSV file path string, list of dicts, or pandas DataFrame.")

    # 2. Group question credits by report_id
    # report_credits_map: report_id -> {topic_id -> max_credit}
    report_credits_map: Dict[str, Dict[str, float]] = {}

    for idx, q_rec in enumerate(question_records):
        report_id = str(q_rec.get("report_id", f"REP_{idx}")).strip()
        
        # Determine question raw text
        q_text = str(q_rec.get("question_text", "")).strip()
        topic_text = str(q_rec.get("topic", "")).strip()

        raw_text = q_text if q_text and q_text.lower() != "nan" else topic_text
        if not raw_text or raw_text.lower() == "nan":
            continue

        source_id = f"{report_id}_q{idx}"
        mapping = map_source_to_taxonomy(
            source_id=source_id,
            raw_text=raw_text,
            source_type="interview"
        )
        credit_dict = mapping.get("credit", {})

        if report_id not in report_credits_map:
            report_credits_map[report_id] = {}

        # W(r,t) = max(question-level credit for topic t within report r)
        for topic_id, credit_val in credit_dict.items():
            current_max = report_credits_map[report_id].get(topic_id, 0.0)
            if credit_val > current_max:
                report_credits_map[report_id][topic_id] = credit_val

    # 3. Calculate topic importance I(t) across all taxonomy nodes
    interview_importance_list = []

    for node in nodes:
        topic_id = node["topic_id"]
        topic_name = node.get("name", topic_id)

        w_sum = 0.0
        matched_report_count = 0

        for r_id, credits in report_credits_map.items():
            w_rt = credits.get(topic_id, 0.0)
            if w_rt > 0:
                w_sum += w_rt
                matched_report_count += 1

        importance = w_sum / float(total_reports_count)
        importance = max(0.0, min(1.0, importance))

        interview_importance_list.append({
            "topic_id": topic_id,
            "topic_name": topic_name,
            "importance": round(importance, 4),
            "matched_report_count": matched_report_count,
            "taxonomy_version": DEFAULT_TAXONOMY_VERSION
        })

    return {
        "total_reports_count": total_reports_count,
        "taxonomy_version": DEFAULT_TAXONOMY_VERSION,
        "interview_importance": interview_importance_list
    }


def _extract_importance_map(
    importance_dict: Union[Dict[str, Any], List[Dict[str, Any]]]
) -> Tuple[Dict[str, float], Dict[str, str], Optional[int], Optional[str]]:
    """
    Extracts topic_id -> importance float map, topic_id -> topic_name map,
    total_reports_count, and taxonomy_version from importance_dict.
    """
    imp_map: Dict[str, float] = {}
    name_map: Dict[str, str] = {}
    total_reports_count: Optional[int] = None
    taxonomy_version: Optional[str] = None

    if isinstance(importance_dict, dict):
        total_reports_count = importance_dict.get("total_reports_count")
        taxonomy_version = importance_dict.get("taxonomy_version")

        items = importance_dict.get("interview_importance")
        if items is None:
            for k, v in importance_dict.items():
                if k in ("total_reports_count", "taxonomy_version"):
                    continue
                if isinstance(v, (int, float)):
                    imp_map[k] = float(v)
                elif isinstance(v, dict) and "importance" in v:
                    imp_map[k] = float(v["importance"])
                    if "topic_name" in v:
                        name_map[k] = v["topic_name"]
        elif isinstance(items, list):
            for item in items:
                tid = item.get("topic_id")
                if tid:
                    imp_map[tid] = float(item.get("importance", 0.0))
                    if "topic_name" in item:
                        name_map[tid] = item["topic_name"]

    elif isinstance(importance_dict, list):
        for item in importance_dict:
            tid = item.get("topic_id")
            if tid:
                imp_map[tid] = float(item.get("importance", 0.0))
                if "topic_name" in item:
                    name_map[tid] = item["topic_name"]

    return imp_map, name_map, total_reports_count, taxonomy_version


def _extract_coverage_map(
    coverage_dict: Union[Dict[str, Any], List[Dict[str, Any]]]
) -> Tuple[Dict[str, float], Dict[str, str], Optional[str]]:
    """
    Extracts topic_id -> coverage float map, topic_id -> topic_name map,
    and taxonomy_version from coverage_dict.
    """
    cov_map: Dict[str, float] = {}
    name_map: Dict[str, str] = {}
    taxonomy_version: Optional[str] = None

    if isinstance(coverage_dict, dict):
        taxonomy_version = coverage_dict.get("taxonomy_version")

        items = coverage_dict.get("topic_coverage")
        if items is None:
            for k, v in coverage_dict.items():
                if k in ("syllabus_id", "taxonomy_version"):
                    continue
                if isinstance(v, (int, float)):
                    cov_map[k] = float(v)
                elif isinstance(v, dict) and "coverage" in v:
                    cov_map[k] = float(v["coverage"])
                    if "topic_name" in v:
                        name_map[k] = v["topic_name"]
        elif isinstance(items, list):
            for item in items:
                tid = item.get("topic_id")
                if tid:
                    cov_map[tid] = float(item.get("coverage", 0.0))
                    if "topic_name" in item:
                        name_map[tid] = item["topic_name"]

    elif isinstance(coverage_dict, list):
        for item in coverage_dict:
            tid = item.get("topic_id")
            if tid:
                cov_map[tid] = float(item.get("coverage", 0.0))
                if "topic_name" in item:
                    name_map[tid] = item["topic_name"]

    return cov_map, name_map, taxonomy_version


MIN_REPORTS = 15


def calculate_composite_score(
    importance_dict: Union[Dict[str, Any], List[Dict[str, Any]]],
    coverage_dict: Union[Dict[str, Any], List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    Phase 10: Calculates the Composite Alignment Score S_comp (0.0 to 100.0%).

    Mathematical formulation:
    - Universe U = { t | I(t) > 0 }
    - S_comp = [ sum_{t in U} (I(t) * Coverage(t)) / sum_{t in U} I(t) ] * 100
    - If sum_{t in U} I(t) == 0 or U is empty, S_comp = 0.0
    - Enforces MIN_REPORTS = 15 density gate if total_reports_count is present and < 15.
    """
    imp_map, _, total_reports_count, imp_tax_ver = _extract_importance_map(importance_dict)
    cov_map, _, cov_tax_ver = _extract_coverage_map(coverage_dict)

    if total_reports_count is not None and total_reports_count < MIN_REPORTS:
        raise ValueError(
            f"Density gate failed: Minimum {MIN_REPORTS} independent reports required for scoring, "
            f"found {total_reports_count}."
        )

    taxonomy_version = imp_tax_ver or cov_tax_ver or DEFAULT_TAXONOMY_VERSION

    sum_weighted_coverage = 0.0
    sum_importance = 0.0
    universe_size = 0

    for topic_id, importance in imp_map.items():
        if importance > 0:
            coverage = cov_map.get(topic_id, 0.0)
            sum_weighted_coverage += importance * coverage
            sum_importance += importance
            universe_size += 1

    if sum_importance <= 0 or universe_size == 0:
        s_comp = 0.0
    else:
        s_comp = (sum_weighted_coverage / sum_importance) * 100.0

    s_comp = max(0.0, min(100.0, s_comp))

    return {
        "composite_score": round(s_comp, 4),
        "S_comp": round(s_comp, 4),
        "taxonomy_version": taxonomy_version,
        "scoring_universe_size": universe_size,
        "total_importance": round(sum_importance, 4)
    }


def rank_priority_gaps(
    importance_dict: Union[Dict[str, Any], List[Dict[str, Any]]],
    coverage_dict: Union[Dict[str, Any], List[Dict[str, Any]]],
    taxonomy_nodes: Optional[Union[str, List[Dict[str, Any]]]] = DEFAULT_TAXONOMY_PATH
) -> List[Dict[str, Any]]:
    """
    Phase 11: Ranks priority preparation gaps for topics with positive interview importance I(t) > 0.

    Mathematical formulation:
    - PriorityGap(t) = I(t) * (1 - Coverage(t)) for t where I(t) > 0
    - Excludes topics with I(t) <= 0
    - Sorted descending by PriorityGap(t)
    - Deterministic tie-breaking by topic_id ascending
    - Returns list of PriorityGapItem-compatible dicts with 1-indexed rank
    """
    imp_map, imp_name_map, _, _ = _extract_importance_map(importance_dict)
    cov_map, cov_name_map, _ = _extract_coverage_map(coverage_dict)

    tax_name_map: Dict[str, str] = {}
    if taxonomy_nodes:
        try:
            nodes = load_taxonomy_nodes(taxonomy_nodes)
            for n in nodes:
                tax_name_map[n["topic_id"]] = n.get("name", n["topic_id"])
        except Exception:
            pass

    gaps = []

    for topic_id, importance in imp_map.items():
        if importance > 0:
            coverage = cov_map.get(topic_id, 0.0)
            priority_gap = importance * (1.0 - coverage)

            topic_name = (
                tax_name_map.get(topic_id) or
                imp_name_map.get(topic_id) or
                cov_name_map.get(topic_id) or
                topic_id
            )

            gaps.append({
                "topic_id": topic_id,
                "topic_name": topic_name,
                "importance": round(importance, 4),
                "coverage": round(coverage, 4),
                "priority_gap": round(priority_gap, 4),
                "_raw_gap": priority_gap
            })

    # Sort descending by priority_gap (_raw_gap), break ties alphabetically by topic_id
    gaps.sort(key=lambda x: (-x["_raw_gap"], x["topic_id"]))

    ranked_items = []
    for rank_idx, item in enumerate(gaps, start=1):
        ranked_items.append({
            "rank": rank_idx,
            "topic_id": item["topic_id"],
            "topic_name": item["topic_name"],
            "importance": item["importance"],
            "coverage": item["coverage"],
            "priority_gap": item["priority_gap"]
        })

    return ranked_items



