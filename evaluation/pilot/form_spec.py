"""
Phase 16 pilot: the single source of truth for the Google Form, its Apps Script, its CSV export template and the
analysis. Two student tracks: A = took an OA/interview (topics asked, gap ratings, usefulness); B = any CSE student who
looks at the dashboard for 5 minutes (one perceived-match rating, usefulness).

Question titles and the company profiles (top-10 important topics for M1, top-10 priority gaps for M2) come from the
saved v1.2 results and topic tables, so the form, `data/pilot/pilot_template.csv` and `analyze_pilot.py` always agree.
Regenerate the form and template with `python evaluation/pilot/build_form.py` after results change.
"""
import json
import os
from typing import Any, Dict, List, Set

from pipeline.config import ROOT, load_targets

RESULTS_DIR = os.path.join(ROOT, "results")
TOPICS_DIR = os.path.join(ROOT, "results", "topics")
TAXONOMY_PATH = os.path.join(ROOT, "data", "taxonomy", "taxonomy_v1.0.json")
FORM_PATH = os.path.join(ROOT, "docs", "pilot", "FORM.md")
TEMPLATE_PATH = os.path.join(ROOT, "data", "pilot", "pilot_template.csv")
SCRIPT_PATH = os.path.join(ROOT, "docs", "pilot", "create_form.gs")
RESULTS_VERSION = "v1.2"
TOP_N = 10

CONSENT = "Consent"
CONSENT_YES = "I have read the information sheet and agree that my anonymised answers are used in the PREPLINE pilot"
PARTICIPANT = "Participant ID (given to you by the researcher, e.g. P01)"
TRACK = "Which describes you?"
TRACK_A = "I took an online assessment or interview with one of these companies (any outcome, including internships)"
TRACK_B = "I have not; I will look at the PREPLINE dashboard for about 5 minutes"
COMPANY = "Company and role you interviewed for"
COMPANY_B = "Company profile you looked at on the dashboard"
PERCEIVED = "These gaps match my perceived weak areas"
ROLE = "Exact role title (as in the offer or invitation)"
ROUNDS = "Rounds you took part in"
TOPICS = "Topics you were actually asked about"
GAP_PREFIX = "Gap relevance:"
USEFULNESS = "Usefulness"
COMMENTS = "Anything else? (optional)"
NONE_OF_THESE = "None of these"
ROUND_OPTIONS = ["Online assessment", "Technical interview", "System design", "Hiring manager / behavioural", "Other"]
RATING_SCALE = ["1", "2", "3", "4", "5", "N/A"]
USEFULNESS_ITEMS = [
    "The priority-gap list was easy to understand",
    "The gaps shown would help me plan my preparation",
    "The confidence information helped me judge how far to trust the results",
    "I would use PREPLINE before a real interview",
    "I would recommend PREPLINE to a classmate",
]


def _read(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def profiles() -> List[Dict[str, Any]]:
    """Per configured target: label, status, top-10 important topic names (M1) and top-10 priority gap names (M2)."""
    out = []
    for t in load_targets():
        result = _read(os.path.join(RESULTS_DIR, f"{t['id']}_{RESULTS_VERSION}_course_syllabi.json"))
        topics = _read(os.path.join(TOPICS_DIR, f"{t['id']}_{RESULTS_VERSION}_topics.json"))["topics"]
        important = sorted((x for x in topics if (x["importance"] or 0) > 0), key=lambda x: (-x["importance"], x["topic_id"]))
        out.append({
            "target_id": t["id"],
            "label": f"{t['company']} {t['role']}",
            "status": result["status"],
            "top_important": [x["topic_name"] for x in important[:TOP_N]],
            "gaps": [g["topic_name"] for g in result.get("top_priority_gaps", [])[:TOP_N]],
        })
    return out


def topic_options() -> List[str]:
    """The granular interview skills of taxonomy v1.0, in taxonomy order (the 'Topics asked' checkbox options)."""
    data = _read(TAXONOMY_PATH)
    nodes = data["nodes"] if isinstance(data, dict) and "nodes" in data else data
    return [n["name"] for n in nodes if n["type"] == "granular_skill"]


def gap_row(rank: int, topic: str) -> str:
    return f"{rank}. {topic}"


def gap_column(label: str, rank: int, topic: str) -> str:
    """Google Forms exports a multiple-choice grid as '<question title> [<row>]'."""
    return f"{GAP_PREFIX} {label} [{gap_row(rank, topic)}]"


def scored_profiles() -> List[Dict[str, Any]]:
    """Targets with a PREPLINE profile (top priority gaps); Track B can only look at these."""
    return [p for p in profiles() if p["gaps"]]


def columns() -> List[str]:
    cols = ["Timestamp", CONSENT, PARTICIPANT, TRACK, COMPANY, ROLE, ROUNDS, TOPICS]
    for p in profiles():
        cols += [gap_column(p["label"], i, topic) for i, topic in enumerate(p["gaps"], 1)]
    cols += [COMPANY_B, PERCEIVED]
    cols += [f"{USEFULNESS} [{item}]" for item in USEFULNESS_ITEMS]
    return cols + [COMMENTS]


def parse_topics(cell: str) -> Set[str]:
    """
    Google Forms joins checkbox answers with ', ', and some topic names contain commas ("Semaphores, Mutexes, and
    Monitors"), so answers are recovered by matching the known option names, longest first.
    """
    remaining, found = cell or "", set()
    for name in sorted(topic_options(), key=len, reverse=True):
        if name in remaining:
            found.add(name)
            remaining = remaining.replace(name, "")
    return found
