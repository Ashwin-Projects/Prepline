"""
Phase 16 pilot: pre-registered descriptive analysis of the Google Form export (docs/pilot/PILOT_PROTOCOL.md).
Students only, two tracks: A took an OA/interview (M1, M2, M3); B used the dashboard for 5 minutes (M2b, M3).

    M1 topic hit rate   per participant: share of the taxonomy topics they were asked that are in PREPLINE's top-10
                        important topics for their company; participants who ticked no taxonomy topic are skipped.
    M2 gap relevance    per participant: mean 1-5 rating over the top-10 priority gaps shown ("N/A" skipped).
    M3 usefulness       per participant: mean of the 5 usefulness items (1-5).
    M2b perceived match Track B: one 1-5 rating "these gaps match my perceived weak areas".

Each metric is the mean over participants, per company and overall (all consenting participants pooled). Responses
without the consent tick are excluded and counted. Descriptive only: no inferential statistics at this n.
A company with no PREPLINE profile (INSUFFICIENT_DATA) has no M1/M2.

Writes results/pilot/PILOT_RESULTS.md, pilot_results.json and pilot_m1_topic_hit_rate.png. Refuses to overwrite
unless --replace, and refuses SYNTHETIC data (participant ids starting "SYN") in the default results folder.

Usage:
    python evaluation/pilot/analyze_pilot.py data/pilot/responses.csv [--replace]
"""
import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from evaluation.pilot import form_spec as fs

DEFAULT_OUT_DIR = os.path.join(ROOT, "results", "pilot")
SYNTHETIC_PREFIX = "SYN"
FILES = ("PILOT_RESULTS.md", "pilot_results.json", "pilot_m1_topic_hit_rate.png")


def load_responses(path: str) -> List[Dict[str, str]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _rating(value: str) -> Optional[float]:
    value = (value or "").strip()
    return float(value) if value in ("1", "2", "3", "4", "5") else None


def participant_metrics(row: Dict[str, str], profile: Optional[Dict[str, Any]]) -> Dict[str, Optional[float]]:
    asked = fs.parse_topics(row.get(fs.TOPICS, ""))
    m1 = m2 = None
    if profile and profile["top_important"] and asked:
        m1 = len(asked & set(profile["top_important"])) / len(asked)
    if profile and profile["gaps"]:
        ratings = [_rating(row.get(fs.gap_column(profile["label"], i, g), "")) for i, g in enumerate(profile["gaps"], 1)]
        ratings = [r for r in ratings if r is not None]
        m2 = mean(ratings) if ratings else None
    items = [_rating(row.get(f"{fs.USEFULNESS} [{item}]", "")) for item in fs.USEFULNESS_ITEMS]
    items = [r for r in items if r is not None]
    return {"M1_topic_hit_rate": m1, "M2_gap_relevance": m2, "M3_usefulness": mean(items) if items else None}


TRACK_A_METRICS = ("M1_topic_hit_rate", "M2_gap_relevance", "M3_usefulness")
TRACK_B_METRICS = ("M2b_perceived_match", "M3_usefulness")


def _summary(rows: List[Dict[str, Optional[float]]], keys=TRACK_A_METRICS) -> Dict[str, Any]:
    out: Dict[str, Any] = {"n": len(rows)}
    for key in keys:
        values = [r[key] for r in rows if r[key] is not None]
        out[key] = mean(values) if values else None
        out[f"{key}_n"] = len(values)
        out[f"{key}_range"] = [min(values), max(values)] if values else None
    return out


def track_b_metrics(row: Dict[str, str]) -> Dict[str, Optional[float]]:
    items = [_rating(row.get(f"{fs.USEFULNESS} [{item}]", "")) for item in fs.USEFULNESS_ITEMS]
    items = [r for r in items if r is not None]
    return {"M2b_perceived_match": _rating(row.get(fs.PERCEIVED, "")), "M3_usefulness": mean(items) if items else None}


def analyze(responses: List[Dict[str, str]]) -> Dict[str, Any]:
    by_label = {p["label"]: p for p in fs.profiles()}
    consenting = [r for r in responses if fs.CONSENT_YES in (r.get(fs.CONSENT) or "")]
    a_rows: Dict[str, List[Dict[str, Optional[float]]]] = {label: [] for label in by_label}
    b_rows: Dict[str, List[Dict[str, Optional[float]]]] = {p["label"]: [] for p in fs.scored_profiles()}
    a_all, b_all = [], []
    for r in consenting:
        track = (r.get(fs.TRACK) or "").strip()
        if track == fs.TRACK_B:
            metrics = track_b_metrics(r)
            b_rows.setdefault((r.get(fs.COMPANY_B) or "").strip(), []).append(metrics)
            b_all.append(metrics)
        elif track == fs.TRACK_A:
            label = (r.get(fs.COMPANY) or "").strip()
            metrics = participant_metrics(r, by_label.get(label))
            a_rows.setdefault(label, []).append(metrics)
            a_all.append(metrics)
    return {
        "n_responses": len(responses),
        "n_excluded_no_consent": len(responses) - len(consenting),
        "n_excluded_no_track": len(consenting) - len(a_all) - len(b_all),
        "synthetic": any((r.get(fs.PARTICIPANT) or "").startswith(SYNTHETIC_PREFIX) for r in responses),
        "tracks": {
            "A": {"by_company": {k: _summary(v) for k, v in a_rows.items()}, "overall": _summary(a_all)},
            "B": {"by_company": {k: _summary(v, TRACK_B_METRICS) for k, v in b_rows.items()},
                  "overall": _summary(b_all, TRACK_B_METRICS)},
        },
        "M3_all_participants": _summary(a_all + b_all, ("M3_usefulness",)),
    }


def _fmt(value: Optional[float], pct: bool = False) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.0f} %" if pct else f"{value:.2f}"


def build_markdown(result: Dict[str, Any], source: str) -> str:
    a, b, m3 = result["tracks"]["A"], result["tracks"]["B"], result["M3_all_participants"]
    lines = [
        "# PREPLINE pilot results (Phase 16)",
        "",
        f"Generated by `evaluation/pilot/analyze_pilot.py` from `{source}` on {result['generated_at'][:10]}. "
        "Pre-registered in `docs/pilot/PILOT_PROTOCOL.md`; descriptive only — no inferential statistics at this n, and "
        "no γ calibration (that needs round-level outcomes and a larger sample). Students only, two tracks.",
        "",
        f"Responses: {result['n_responses']}; excluded without consent: {result['n_excluded_no_consent']}; without a "
        f"track: {result['n_excluded_no_track']}; analysed: Track A {a['overall']['n']}, Track B {b['overall']['n']}.",
        "",
    ]
    if result["synthetic"]:
        lines += ["> **SYNTHETIC DATA — not pilot results.** Participant ids start with SYN.", ""]
    lines += ["## Track A — took an online assessment or interview", "",
              "| Company | n | M1 topic hit rate (n) | M2 gap relevance, 1–5 (n) | M3 usefulness, 1–5 (n) |",
              "|---|---|---|---|---|"]
    for label, s in list(a["by_company"].items()) + [("All Track A", a["overall"])]:
        lines.append(f"| {label} | {s['n']} | {_fmt(s['M1_topic_hit_rate'], True)} ({s['M1_topic_hit_rate_n']}) | "
                     f"{_fmt(s['M2_gap_relevance'])} ({s['M2_gap_relevance_n']}) | "
                     f"{_fmt(s['M3_usefulness'])} ({s['M3_usefulness_n']}) |")
    lines += ["", "## Track B — any CSE student, after about 5 minutes on the dashboard", "",
              "| Company profile viewed | n | M2b perceived match, 1–5 (n) | M3 usefulness, 1–5 (n) |",
              "|---|---|---|---|"]
    for label, s in list(b["by_company"].items()) + [("All Track B", b["overall"])]:
        lines.append(f"| {label} | {s['n']} | {_fmt(s['M2b_perceived_match'])} ({s['M2b_perceived_match_n']}) | "
                     f"{_fmt(s['M3_usefulness'])} ({s['M3_usefulness_n']}) |")
    lines += [
        "",
        f"**M3 usefulness, both tracks:** {_fmt(m3['M3_usefulness'])} (n = {m3['M3_usefulness_n']}).",
        "",
        "- **M1** share of the topics a Track A participant was asked that are in PREPLINE's top-10 important topics.",
        "- **M2** mean rating of “this gap matched my real weak areas” over the top-10 gaps shown (N/A skipped).",
        "- **M2b** Track B rating of “these gaps match my perceived weak areas” (perceived, not tested).",
        "- **M3** mean of the 5 usefulness items. A company without a PREPLINE profile has no M1/M2.",
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
    ax.set_ylabel("Topics asked that PREPLINE ranks top-10 (%)", color="#52514e", fontsize=9)
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
    if result["synthetic"] and os.path.abspath(out_dir) == os.path.abspath(DEFAULT_OUT_DIR):
        raise ValueError("SYNTHETIC responses (participant ids SYN..) are never written to results/pilot")
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
    with open(args.csv, encoding="utf-8-sig", newline="") as f:
        header = next(csv.reader(f), [])
    missing = [c for c in fs.columns() if c not in header]
    if missing:
        sys.exit(f"The export lacks {len(missing)} expected column(s), e.g. {missing[0]!r}; check the form titles "
                 f"against docs/pilot/FORM.md.")
    result = run(args.csv, args.out_dir, args.replace)
    print(f"Analysed Track A {result['tracks']['A']['overall']['n']}, Track B {result['tracks']['B']['overall']['n']} "
          f"({result['n_excluded_no_consent']} excluded without consent); "
          f"wrote {args.out_dir}")


if __name__ == "__main__":
    main()
