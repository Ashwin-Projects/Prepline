"""
Phase 16 pilot: pre-registered descriptive analysis of the Google Form export (docs/pilot/PILOT_PROTOCOL.md).
Students only. Everyone picks a company (Q1) and rates its top-10 priority gaps (Q2); Q3 splits them into Track A
(took an OA/interview with that company: Q4 topics encountered) and Track B (did not).

    M1 topic hit rate   Track A, per participant: of the Q4 options ticked that map to taxonomy topics, the share
                        whose topics include one of the company's top-10 priority gaps. Hashing, Greedy algorithms and
                        Other have no taxonomy node and are counted separately; Cannot recall is excluded; a participant
                        with no mapped option has no M1.
    M2 gap match        per participant: mean Q2 rating (1-5) over the gap rows answered.
    M3 rating           per participant: mean of the 4 Q5 statements (1-5).

Each metric is the mean over participants, per company and per track. Responses without the consent tick are excluded
and counted, as are responses missing Q1 or Q3. Descriptive only: no inferential statistics at this n.

Writes results/pilot/PILOT_RESULTS.md, pilot_results.json and pilot_m1_topic_hit_rate.png. Refuses to overwrite
unless --replace, and refuses SYNTHETIC data (an improvement answer, Q6, starting "SYNTHETIC") in the default folder.

Usage:
    python evaluation/pilot/analyze_pilot.py data/pilot/responses.csv [--replace]
"""
import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from evaluation.pilot import form_spec as fs

DEFAULT_OUT_DIR = os.path.join(ROOT, "results", "pilot")
SYNTHETIC_MARK = "SYNTHETIC"
FILES = ("PILOT_RESULTS.md", "pilot_results.json", "pilot_m1_topic_hit_rate.png")
TRACK_A_METRICS = ("M1_topic_hit_rate", "M2_gap_relevance", "M3_usefulness")
TRACK_B_METRICS = ("M2_gap_relevance", "M3_usefulness")

Response = Dict[str, List[str]]


def load_responses(path: str) -> List[Response]:
    """Each response maps a column title to its cells, in header order (repeated grid titles give several cells)."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        out = []
        for row in reader:
            response: Response = {}
            for title, value in zip(header, row):
                response.setdefault(title, []).append(value)
            out.append(response)
    return out


def missing_columns(path: str) -> List[str]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        header = set(next(csv.reader(f), []))
    return [c for c in dict.fromkeys(fs.columns()) if c not in header]


def _first(response: Response, title: str) -> str:
    return next((v.strip() for v in response.get(title, []) if v.strip()), "")


def _rating(value: str) -> Optional[float]:
    """Grid labels look like '4 Very well'; the leading digit is the rating."""
    m = re.match(r"\s*([1-5])\b", value or "")
    return float(m.group(1)) if m else None


def participant_metrics(response: Response, profile: Dict[str, Any], track: str) -> Dict[str, Any]:
    gaps = [_rating(_first(response, fs.gap_column(g))) for g in profile["gaps"]]
    gaps = [r for r in gaps if r is not None]
    items = [_rating(_first(response, fs.rate_column(item))) for item in fs.RATE_ITEMS]
    items = [r for r in items if r is not None]
    out: Dict[str, Any] = {"M2_gap_relevance": mean(gaps) if gaps else None,
                           "M3_usefulness": mean(items) if items else None}
    if track == "A":
        ticked = fs.parse_topics(_first(response, fs.Q4))
        mapped = [o for o in ticked if o in fs.OPTION_TOPICS]
        gap_ids = set(profile["gap_ids"])
        hits = [o for o in mapped if gap_ids & set(fs.OPTION_TOPICS[o])]
        out["M1_topic_hit_rate"] = len(hits) / len(mapped) if mapped else None
        out["ticked"] = sorted(ticked)
    return out


def _summary(rows: List[Dict[str, Any]], keys) -> Dict[str, Any]:
    out: Dict[str, Any] = {"n": len(rows)}
    for key in keys:
        values = [r[key] for r in rows if r[key] is not None]
        out[key] = mean(values) if values else None
        out[f"{key}_n"] = len(values)
        out[f"{key}_range"] = [min(values), max(values)] if values else None
    return out


def analyze(responses: List[Response]) -> Dict[str, Any]:
    by_company = {p["company"]: p for p in fs.profiles()}
    consenting = [r for r in responses if fs.CONSENT_YES in _first(r, fs.CONSENT)]
    rows: Dict[str, Dict[str, List[Dict[str, Any]]]] = {t: {c: [] for c in by_company} for t in ("A", "B")}
    for r in consenting:
        company, answer = _first(r, fs.COMPANY), _first(r, fs.Q3)
        track = {fs.YES: "A", fs.NO: "B"}.get(answer)
        if company in by_company and track:
            rows[track][company].append(participant_metrics(r, by_company[company], track))
    a_all = [m for v in rows["A"].values() for m in v]
    b_all = [m for v in rows["B"].values() for m in v]
    selected = {o: sum(o in m["ticked"] for m in a_all) for o in fs.UNMAPPED}
    return {
        "n_responses": len(responses),
        "n_excluded_no_consent": len(responses) - len(consenting),
        "n_excluded_incomplete": len(consenting) - len(a_all) - len(b_all),
        "synthetic": any(_first(r, fs.Q6).startswith(SYNTHETIC_MARK) for r in responses),
        "top10_gaps": {c: p["gaps"] for c, p in by_company.items()},
        "tracks": {
            "A": {"by_company": {c: _summary(v, TRACK_A_METRICS) for c, v in rows["A"].items()},
                  "overall": _summary(a_all, TRACK_A_METRICS)},
            "B": {"by_company": {c: _summary(v, TRACK_B_METRICS) for c, v in rows["B"].items()},
                  "overall": _summary(b_all, TRACK_B_METRICS)},
        },
        "q4_unmapped": {"n_track_a": len(a_all), "selected": selected,
                        "cannot_recall": sum(fs.CANNOT_RECALL in m["ticked"] for m in a_all)},
        "M3_all_participants": _summary(a_all + b_all, ("M3_usefulness",)),
    }


def _fmt(value: Optional[float], pct: bool = False) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.0f} %" if pct else f"{value:.2f}"


def build_markdown(result: Dict[str, Any], source: str) -> str:
    a, b, m3, u = result["tracks"]["A"], result["tracks"]["B"], result["M3_all_participants"], result["q4_unmapped"]
    lines = [
        "# PREPLINE pilot results (Phase 16)",
        "",
        f"Generated by `evaluation/pilot/analyze_pilot.py` from `{source}` on {result['generated_at'][:10]}. "
        "Pre-registered in `docs/pilot/PILOT_PROTOCOL.md`; descriptive only — no inferential statistics at this n, and "
        "no γ calibration (that needs round-level outcomes and a larger sample). Students only, reported per track.",
        "",
        f"Responses: {result['n_responses']}; excluded without consent: {result['n_excluded_no_consent']}; without a "
        f"company or Q3 answer: {result['n_excluded_incomplete']}; analysed: Track A {a['overall']['n']}, "
        f"Track B {b['overall']['n']}.",
        "",
    ]
    if result["synthetic"]:
        lines += ["> **SYNTHETIC DATA — not pilot results.**", ""]
    lines += ["## Track A — took an online assessment or interview with the company", "",
              "| Company | n | M1 topic hit rate (n) | M2 gap match, 1–5 (n) | M3 rating, 1–5 (n) |",
              "|---|---|---|---|---|"]
    for label, s in list(a["by_company"].items()) + [("All Track A", a["overall"])]:
        lines.append(f"| {label} | {s['n']} | {_fmt(s['M1_topic_hit_rate'], True)} ({s['M1_topic_hit_rate_n']}) | "
                     f"{_fmt(s['M2_gap_relevance'])} ({s['M2_gap_relevance_n']}) | "
                     f"{_fmt(s['M3_usefulness'])} ({s['M3_usefulness_n']}) |")
    lines += ["", "Q4 answers outside the taxonomy (Track A participants who ticked each; not part of M1):", ""]
    lines += [f"- {o}: {n} of {u['n_track_a']}" for o, n in u["selected"].items()]
    lines += [f"- {fs.CANNOT_RECALL} (excluded): {u['cannot_recall']} of {u['n_track_a']}", ""]
    lines += ["## Track B — has not taken an assessment or interview with the company", "",
              "| Company | n | M2 gap match, 1–5 (n) | M3 rating, 1–5 (n) |", "|---|---|---|---|"]
    for label, s in list(b["by_company"].items()) + [("All Track B", b["overall"])]:
        lines.append(f"| {label} | {s['n']} | {_fmt(s['M2_gap_relevance'])} ({s['M2_gap_relevance_n']}) | "
                     f"{_fmt(s['M3_usefulness'])} ({s['M3_usefulness_n']}) |")
    lines += [
        "",
        f"**M3, both tracks:** {_fmt(m3['M3_usefulness'])} (n = {m3['M3_usefulness_n']}).",
        "",
        "- **M1** of the Q4 options ticked that map to taxonomy topics, the share covering one of the company's top-10 "
        "priority gaps (option-level, so coarser than topic-level).",
        "- **M2** mean Q2 rating of how well the top-10 gaps match the participant's own weak areas. Track B's is "
        "perceived, not tested, and is never pooled with Track A's.",
        "- **M3** mean of the 4 Q5 statements (1 = strongly disagree, 5 = strongly agree).",
        "",
        f"![M1 topic hit rate per company (Track A)]({FILES[2]})",
        "",
    ]
    return "\n".join(lines)


def write_chart(result: Dict[str, Any], path: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    items = [(label, s) for label, s in result["tracks"]["A"]["by_company"].items() if s["M1_topic_hit_rate"] is not None]
    fig, ax = plt.subplots(figsize=(7, 3.6), dpi=200)
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    labels = [label for label, _ in items]
    values = [s["M1_topic_hit_rate"] * 100 for _, s in items]
    ax.bar(labels, values, color="#2a78d6", width=0.5)
    for x, (_, s) in enumerate(items):
        ax.text(x, s["M1_topic_hit_rate"] * 100 + 2, f"{s['M1_topic_hit_rate'] * 100:.0f} % (n={s['M1_topic_hit_rate_n']})",
                ha="center", fontsize=9, color="#0b0b0b")
    ax.set_ylim(0, 110)
    ax.set_ylabel("Topics met that PREPLINE lists as top-10 gaps (%)", color="#52514e", fontsize=9)
    ax.tick_params(colors="#52514e", labelsize=9)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="y", color="#e6e5e0", linewidth=0.8)
    ax.set_axisbelow(True)
    title = "M1 topic hit rate per company (Track A)"
    if result["synthetic"]:
        title += " — SYNTHETIC DATA"
    ax.set_title(title, loc="left", fontsize=11, color="#0b0b0b")
    fig.tight_layout()
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)


def run(csv_path: str, out_dir: str = DEFAULT_OUT_DIR, replace: bool = False) -> Dict[str, Any]:
    result = analyze(load_responses(csv_path))
    result["synthetic"] = result["synthetic"] or SYNTHETIC_MARK in os.path.basename(csv_path).upper()
    if result["synthetic"] and os.path.abspath(out_dir) == os.path.abspath(DEFAULT_OUT_DIR):
        raise ValueError("SYNTHETIC responses are never written to results/pilot")
    paths = [os.path.join(out_dir, name) for name in FILES]
    if not replace and any(os.path.exists(p) for p in paths):
        raise FileExistsError(f"pilot results exist in {out_dir}; pass --replace to update them")
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    result["source"] = os.path.basename(csv_path)
    os.makedirs(out_dir, exist_ok=True)
    with open(paths[0], "w", encoding="utf-8") as f:
        f.write(build_markdown(result, result["source"]))
    with open(paths[1], "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    write_chart(result, paths[2])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-registered descriptive analysis of the pilot form export.")
    parser.add_argument("csv", help="Google Form CSV export (columns as in data/pilot/pilot_template.csv)")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--replace", action="store_true", help="update existing pilot results")
    args = parser.parse_args()
    missing = missing_columns(args.csv)
    if missing:
        sys.exit(f"The export lacks {len(missing)} expected column(s), e.g. {missing[0]!r}; check the form titles "
                 f"against docs/pilot/FORM.md.")
    result = run(args.csv, args.out_dir, args.replace)
    print(f"Analysed Track A {result['tracks']['A']['overall']['n']}, Track B {result['tracks']['B']['overall']['n']} "
          f"({result['n_excluded_no_consent']} excluded without consent); wrote {args.out_dir}")


if __name__ == "__main__":
    main()
