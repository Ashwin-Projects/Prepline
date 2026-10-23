"""
Phase 16 pilot: the single source of truth for the (hand-built) Google Form, its CSV export template and the analysis.

    Consent -> Q1 company (Amazon / Microsoft / Flipkart) -> that company's section: Q2 grid (rows = its top-10
    priority gaps) and Q3 "taken an OA/interview?" -> Yes = Track A: Q4 topics encountered (M1 vs the company's top-10 topics by importance), then Q5;
    No = Track B: Q5 -> Q6 improvement (optional).

Google Forms exports a grid as one column per row, titled '<question> [<row>]'. Q2 has the same title in every company
section, so a gap that two companies share appears in several identically titled columns; the analysis merges them.

Grid rows come from the saved v1.2 results so the form, `data/pilot/pilot_template.csv` and `analyze_pilot.py` always
agree. Regenerate FORM.md and the template with `python evaluation/pilot/build_form.py` after results change.
"""
import json
import os
from typing import Any, Dict, List, Set

from pipeline.config import ROOT, load_targets

RESULTS_DIR = os.path.join(ROOT, "results")
TOPICS_DIR = os.path.join(ROOT, "results", "topics")
TAXONOMY_PATH = os.path.join(ROOT, "data", "taxonomy", "taxonomy_v1.0.json")
FORM_PATH = os.path.join(ROOT, "docs", "pilot", "FORM.md")
PROTOCOL_PATH = os.path.join(ROOT, "docs", "pilot", "PILOT_PROTOCOL.md")
TEMPLATE_PATH = os.path.join(ROOT, "data", "pilot", "pilot_template.csv")
RESULTS_VERSION = "v1.2"
TOP_N = 10
PILOT_TARGETS = ("amazon_sde1", "microsoft_sde1", "flipkart_sde1")

FORM_TITLE = "PREPLINE Pilot — Curriculum vs Interview Topic Gaps"
DESCRIPTION = ("PREPLINE compares the VIT CSE syllabus with the topics companies ask in interviews and lists the topics "
               "a student is most likely under-prepared for (topic gaps). This form takes about 5 minutes and taking "
               "part is voluntary. Anonymous: no names or emails are collected. Answers are used only for this "
               "academic project.")
CONSENT = "Consent"  # the checkbox's question title is not fixed; the analysis finds consent by its answer
CONSENT_YES = "I agree to take part."
COMPANY = "Which company's interview preparation would you like to evaluate?"
Q2 = "How well do the identified topic gaps match your own weak areas?"
GAP_SCALE = ["1 Not at all", "2 Slightly", "3 Moderately", "4 Very well", "5 Exactly matches my weak areas"]
Q3 = "Have you taken an online assessment or interview with this company?"
YES, NO = "Yes", "No"
Q4 = "Which technical topics did you encounter in that assessment or interview?"
OTHER, CANNOT_RECALL = "Other", "Cannot recall"
Q5 = "Please rate PREPLINE."
RATE_SCALE = ["1 Strongly disagree", "2 Disagree", "3 Neither agree nor disagree", "4 Agree", "5 Strongly agree"]
RATE_ITEMS = [
    "The identified topic gaps were easy to understand.",
    "The gaps were relevant to preparing for my selected company.",
    "The confidence labels helped me judge how much to trust the results.",
    "PREPLINE helps me decide what to study next.",
]
Q6 = "What is the one most important improvement you would suggest?"

_ARRAYS = ["dsa.arrays.two_pointers", "dsa.arrays.sliding_window", "dsa.arrays.prefix_sum"]
_DBMS = ["dbms.sql.queries_aggregations", "dbms.sql.joins", "dbms.sql.subqueries", "dbms.normalization.normal_forms",
         "dbms.transactions.acid", "dbms.transactions.isolation_locking", "dbms.indexing.b_trees"]
_OS = ["os.process_management.context_switch", "os.process_management.multithreading", "os.cpu_scheduling.algorithms",
       "os.process_synchronization.semaphores_mutex", "os.memory_management.paging_segmentation",
       "os.memory_management.page_replacement", "os.deadlocks.prevention_avoidance"]
_CN = ["cn.network_models.osi_layers", "cn.application_layer.http_https", "cn.application_layer.dns",
       "cn.transport_layer.tcp_udp", "cn.transport_layer.tcp_mechanisms", "cn.network_layer.ip_subnetting",
       "cn.network_layer.routing_protocols", "cn.network_security.tls_ssl"]
_SYSTEM_DESIGN = ["system_design.load_balancing.algorithms", "system_design.caching.strategies",
                  "system_design.database_scaling.sharding_replication", "system_design.messaging.pub_sub",
                  "system_design.rate_limiting"]

# Q4 options in form order -> taxonomy v1.0 granular skills (M1); None = no taxonomy node (reported apart), and
# Cannot recall is excluded.
_OPTIONS: Dict[str, Any] = {
    "Arrays and strings": _ARRAYS,
    "Two pointers / sliding window": ["dsa.arrays.two_pointers", "dsa.arrays.sliding_window"],
    "Hashing": None,
    "Linked lists": ["dsa.linked_lists.traversal_reversal"],
    "Stacks and queues": ["dsa.stacks_queues.monotonic_stack"],
    "Trees and binary search trees": ["dsa.trees.traversal", "dsa.trees.bst", "dsa.trees.lowest_common_ancestor"],
    "Heaps / priority queues": ["dsa.heaps.top_k"],
    "Graphs (BFS/DFS)": ["dsa.graphs.bfs_dfs", "dsa.graphs.topological_sort", "dsa.graphs.disjoint_set"],
    "Shortest paths": ["dsa.graphs.shortest_path"],
    "Dynamic programming": ["dsa.dp.1d", "dsa.dp.knapsack", "dsa.dp.grid", "dsa.dp.lcs"],
    "Greedy algorithms": None,
    "Backtracking / recursion": ["dsa.backtracking.subsets_permutations"],
    "Sorting and searching": ["dsa.sorting_searching.binary_search"],
    "DBMS / SQL": _DBMS,
    "Operating systems": _OS,
    "Computer networks": _CN,
    "OOP / object-oriented design": None,
    "System design": _SYSTEM_DESIGN,
    OTHER: None,
    CANNOT_RECALL: None,
}
OPTION_TOPICS: Dict[str, List[str]] = {o: ids for o, ids in _OPTIONS.items() if ids}
UNMAPPED = [o for o, ids in _OPTIONS.items() if ids is None and o != CANNOT_RECALL]
TOPIC_OPTIONS: List[str] = list(_OPTIONS)


def _read(path: str) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def taxonomy_nodes() -> List[Dict[str, Any]]:
    data = _read(TAXONOMY_PATH)
    return data["nodes"] if isinstance(data, dict) and "nodes" in data else data


def profiles() -> List[Dict[str, Any]]:
    """
    Amazon, Microsoft, Flipkart from the saved v1.2 results: top-10 priority gaps (the Q2 rows) and top-10 topics by
    importance I(t) (the M1 targets, ranked as in the retrospective validation: importance, then topic_id).
    """
    out = []
    for t in load_targets():
        if t["id"] not in PILOT_TARGETS:
            continue
        result = _read(os.path.join(RESULTS_DIR, f"{t['id']}_{RESULTS_VERSION}_course_syllabi.json"))
        gaps = result.get("top_priority_gaps", [])[:TOP_N]
        topics = _read(os.path.join(TOPICS_DIR, f"{t['id']}_{RESULTS_VERSION}_topics.json"))["topics"]
        important = sorted((x for x in topics if (x["importance"] or 0) > 0), key=lambda x: (-x["importance"], x["topic_id"]))
        out.append({
            "target_id": t["id"],
            "company": t["company"],
            "label": f"{t['company']} {t['role']}",
            "status": result["status"],
            "gaps": [g["topic_name"] for g in gaps],
            "gap_ids": [g["topic_id"] for g in gaps],
            "top_important": [x["topic_name"] for x in important[:TOP_N]],
            "top_important_ids": [x["topic_id"] for x in important[:TOP_N]],
        })
    return out


def gap_column(gap: str) -> str:
    """Google Forms exports a grid row as '<question title> [<row>]'."""
    return f"{Q2} [{gap}]"


def rate_column(item: str) -> str:
    return f"{Q5} [{item}]"


def columns() -> List[str]:
    """The export header in form order; Q2 columns repeat once per company section that shows the gap."""
    cols = ["Timestamp", CONSENT, COMPANY]
    for p in profiles():
        cols += [gap_column(g) for g in p["gaps"]]
    cols += [Q3, Q4] + [rate_column(item) for item in RATE_ITEMS]
    return cols + [Q6]


def parse_topics(cell: str) -> Set[str]:
    """
    Q4 answers. Google joins checkbox answers with ', ', and its built-in 'Other:' option exports the typed text
    instead of 'Other', so known options are matched longest first and any leftover text counts as Other.
    """
    remaining, found = cell or "", set()
    for name in sorted(TOPIC_OPTIONS, key=len, reverse=True):
        if name in remaining:
            found.add(name)
            remaining = remaining.replace(name, "")
    if remaining.replace(",", "").strip():
        found.add(OTHER)
    return found
