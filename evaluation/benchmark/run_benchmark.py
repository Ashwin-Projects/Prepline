"""
Phase 13 part 2: matcher benchmark on the gold labels (labels_v1.0.csv) and the grouped split (splits_v1.0.csv).

Every method scores each item against the taxonomy nodes of the type its source_type allows (node-type rule: syllabus ->
high_level_concept, interview -> granular_skill) and predicts the top-1 node if its score clears the threshold, else
"none" (ties alphabetical by topic_id, as in production):
    keyword          share of a node name's words found in the item text
    tfidf            TF-IDF cosine between the item text and the node's name + description
    minilm_desc      production: two-pass concepts (RAKE) vs node descriptions, all-MiniLM-L6-v2, best concept per node
    minilm_name_desc as minilm_desc, but nodes embedded as "name: description"

Each method's threshold is swept on DEV only (0.30-0.70, step 0.05; best macro-F1, then accuracy, then closest to the
production 0.50, then lower), confirmed on VAL, and TEST is scored once with that threshold. Results are written to
results/benchmark/benchmark_v1.0.json (never overwritten), BENCHMARK.md and a test-F1 bar chart. Production
config and tau are not changed.

Usage:
    python evaluation/benchmark/run_benchmark.py            # score once; refuses if the results file exists
    python evaluation/benchmark/run_benchmark.py --render   # rebuild BENCHMARK.md + chart from the saved results
"""
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from evaluation.benchmark.build_splits import DEFAULT_SPLITS
from evaluation.benchmark.validate_labels import DEFAULT_LABELS, NONE_LABEL, load_labels

THRESHOLDS = [round(0.30 + 0.05 * i, 2) for i in range(9)]
PRODUCTION_THRESHOLD = 0.50
SPLITS = ("dev", "val", "test")
OUT_DIR = os.path.join(ROOT, "results", "benchmark")
OUT_JSON = os.path.join(OUT_DIR, "benchmark_v1.0.json")
OUT_MD = os.path.join(OUT_DIR, "BENCHMARK.md")
OUT_PNG = os.path.join(OUT_DIR, "benchmark_v1.0_test_f1.png")
METHODS = {
    "keyword": "(a) keyword match on node names",
    "tfidf": "(b) TF-IDF over node name + description",
    "minilm_desc": "(c) MiniLM, node descriptions only (current production)",
    "minilm_name_desc": "(d) MiniLM, node name + description",
}
PRODUCTION_METHOD = "minilm_desc"
CHART_LABELS = {"keyword": "(a) Keyword\nnode names", "tfidf": "(b) TF-IDF\nname + description",
                "minilm_desc": "(c) MiniLM description\n(production)", "minilm_name_desc": "(d) MiniLM\nname + description"}
LIMITATIONS = [
    "**Small val and test.** Val is 35 items (4 courses, 2 reports) and test 45 items (2 courses, 3 reports); one "
    "item is 2-3 percentage points, and the scores depend on which courses landed in each split. Macro-F1 over ~20 "
    "labels with a handful of items each is noisy; read counts, not only percentages.",
    "**Gold labels are LLM-drafted.** An LLM draft and an independent LLM labeller agreed on 211/247 primaries "
    "(kappa 0.812); the owner settled the other 56 (rules R1-R5 plus 8 individual decisions). The 191 agreeing rows "
    "were not individually checked by a person (see evaluation/benchmark/ADJUDICATION.md).",
    "**Many gold labels are `none`** (courses outside the taxonomy, R1-R3), so a matcher that predicts `none` often "
    "scores well on accuracy; macro-F1 is the main metric for that reason.",
    "**Top-1 only.** The production pipeline gives credit to every node above τ (60/40 split); this benchmark scores "
    "only the top-1 node against the gold primary. Secondaries are not scored.",
    "**Methods (a) and (b) see the raw text; (c) and (d) see the two-pass RAKE concepts**, as production does.",
    "**The test split was computed twice.** A mistyped command after the first run re-ran the script; it reproduced "
    "the same test numbers and its write was refused. No choice was made from either computation.",
]
_STOP = {"and", "the", "of", "a", "an", "in", "to", "for", "on", "with", "vs", "&"}


def _words(text: str) -> set:
    """Lower-case alphanumeric words without stop words, plurals folded (trees -> tree)."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words if w not in _STOP}


def _allowed(nodes: List[Dict[str, Any]], node_type: str) -> List[Dict[str, Any]]:
    return [n for n in nodes if n["type"] == node_type]


def keyword_scores(text: str, nodes: List[Dict[str, Any]], node_type: str) -> Dict[str, float]:
    item_words = _words(text)
    scores = {}
    for node in _allowed(nodes, node_type):
        name_words = _words(node["name"])
        scores[node["topic_id"]] = len(name_words & item_words) / len(name_words) if name_words else 0.0
    return scores


def tfidf_scores(texts: List[str], nodes: List[Dict[str, Any]], node_types: List[str]) -> List[Dict[str, float]]:
    """Vectorizer fitted on the node documents only, so no benchmark text (dev, val or test) shapes the vocabulary."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    vectorizer = TfidfVectorizer(stop_words="english", sublinear_tf=True)
    node_matrix = vectorizer.fit_transform([f"{n['name']} {n['description']}" for n in nodes])
    sims = cosine_similarity(vectorizer.transform(texts), node_matrix)
    return [{n["topic_id"]: float(row[i]) for i, n in enumerate(nodes) if n["type"] == node_type}
            for row, node_type in zip(sims, node_types)]


def minilm_scores(items: List[Dict[str, str]], nodes: List[Dict[str, Any]], node_types: List[str],
                  node_text: str) -> List[Dict[str, float]]:
    """
    Production path: two-pass concepts per item, cosine against node embeddings, best concept per node.
    node_text "description" reproduces pipeline.embeddings exactly; "name_description" embeds "name: description".
    """
    from sentence_transformers import util

    from pipeline.embeddings import load_model
    from pipeline.keyword_abstraction import two_pass_abstract

    model = load_model()
    docs = [n["description"] if node_text == "description" else f"{n['name']}: {n['description']}" for n in nodes]
    node_embeddings = model.encode(docs, convert_to_tensor=True)
    results = []
    for item, node_type in zip(items, node_types):
        concepts = two_pass_abstract(item["item_id"], item["raw_text"], item["source_type"])["intermediate_concepts"]
        if not concepts:
            results.append({})
            continue
        rows = util.cos_sim(model.encode(list(concepts), convert_to_tensor=True), node_embeddings).tolist()
        results.append({n["topic_id"]: max(row[i] for row in rows)
                        for i, n in enumerate(nodes) if n["type"] == node_type})
    return results


def predict(scores: Dict[str, float], threshold: float) -> str:
    if not scores:
        return NONE_LABEL
    topic_id, score = min(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    return topic_id if score >= threshold else NONE_LABEL


def metrics(gold: List[str], pred: List[str]) -> Dict[str, Any]:
    """Top-1 accuracy and macro precision/recall/F1 over every label seen in gold or predictions (incl. none)."""
    from sklearn.metrics import precision_recall_fscore_support

    labels = sorted(set(gold) | set(pred))
    p, r, f, _ = precision_recall_fscore_support(gold, pred, labels=labels, average="macro", zero_division=0)
    correct = sum(g == q for g, q in zip(gold, pred))
    return {"n": len(gold), "correct": correct, "accuracy": round(correct / len(gold), 4) if gold else None,
            "macro_precision": round(float(p), 4), "macro_recall": round(float(r), 4), "macro_f1": round(float(f), 4)}


def sweep(scores: List[Dict[str, float]], gold: List[str]) -> List[Dict[str, Any]]:
    return [dict(threshold=t, **metrics(gold, [predict(s, t) for s in scores])) for t in THRESHOLDS]


def choose_threshold(rows: List[Dict[str, Any]]) -> float:
    best = min(rows, key=lambda r: (-r["macro_f1"], -r["accuracy"], abs(r["threshold"] - PRODUCTION_THRESHOLD),
                                    r["threshold"]))
    return best["threshold"]


def _report(ids: List[str], scores, gold, meta, threshold) -> Dict[str, Any]:
    pred = {i: predict(scores[i], threshold) for i in ids}
    out = {"overall": metrics([gold[i] for i in ids], [pred[i] for i in ids]), "by_source_type": {}, "by_domain": {}}
    for key, field in (("by_source_type", "source_type"), ("by_domain", "domain")):
        for value in sorted({meta[i][field] for i in ids}):
            sub = [i for i in ids if meta[i][field] == value]
            out[key][value] = metrics([gold[i] for i in sub], [pred[i] for i in sub])
    out["predictions"] = {i: pred[i] for i in ids}
    return out


def evaluate_method(scores: Dict[str, Dict[str, float]], gold: Dict[str, str], split: Dict[str, str],
                    meta: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    """Threshold from dev only; val and test are scored at that threshold."""
    ids = {s: [i for i in gold if split[i] == s] for s in SPLITS}
    dev_sweep = sweep([scores[i] for i in ids["dev"]], [gold[i] for i in ids["dev"]])
    threshold = choose_threshold(dev_sweep)
    result = {"threshold": threshold, "dev_sweep": dev_sweep}
    for s in SPLITS:
        result[s] = _report(ids[s], scores, gold, meta, threshold)
    return result


def write_json(data: Dict[str, Any], path: str) -> None:
    if os.path.exists(path):
        raise FileExistsError(f"{path} exists; benchmark results are versioned and never overwritten")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _pct(m: Dict[str, Any]) -> str:
    return f"{m['accuracy']:.3f} ({m['correct']}/{m['n']})"


def write_chart(result: Dict[str, Any], path: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    names = list(METHODS)
    values = [result["methods"][m]["test"]["overall"]["macro_f1"] for m in names]
    labels = [CHART_LABELS[m] for m in names]
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=200)
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    for x, v in enumerate(values):
        ax.add_patch(FancyBboxPatch((x - 0.3, 0), 0.6, max(v, 0.002), boxstyle="round,pad=0,rounding_size=0.04",
                                    linewidth=0, facecolor="#2a78d6", mutation_aspect=0.3))
        ax.text(x, v + 0.015, f"{v:.3f}", ha="center", va="bottom", fontsize=10, color="#0b0b0b")
    ax.set_xlim(-0.6, len(values) - 0.4)
    ax.set_ylim(0, max(1.0, max(values) + 0.1))
    ax.set_xticks(range(len(values)), labels, fontsize=9, color="#52514e")
    ax.set_ylabel("Macro-F1 (test)", color="#52514e")
    ax.tick_params(axis="y", colors="#52514e")
    ax.grid(axis="y", color="#e6e5e0", linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#c9c8c2")
    test = result["split_sizes"]["test"]
    ax.set_title(f"Topic-matching macro-F1 on the held-out test set (n={test['syllabus'] + test['interview']})",
                 loc="left", fontsize=11, color="#0b0b0b")
    fig.tight_layout()
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)


def recommendation(result: Dict[str, Any]) -> str:
    """Per SPLIT_PLAN.md the variant choice is made on val; dev and test are reported alongside, never used to choose."""
    m = result["methods"]
    f1 = {s: {name: m[name][s]["overall"]["macro_f1"] for name in METHODS} for s in ("dev", "val", "test")}
    best_val = max(METHODS, key=lambda name: (f1["val"][name], name == PRODUCTION_METHOD))
    best_test = max(METHODS, key=lambda name: f1["test"][name])
    figures = "; ".join(f"{name}: dev {f1['dev'][name]:.3f}, val {f1['val'][name]:.3f}, test {f1['test'][name]:.3f}"
                        for name in METHODS)
    if best_val == PRODUCTION_METHOD:
        return (f"Keep the production matcher ({PRODUCTION_METHOD}, τ unchanged): it has the best val macro-F1. "
                f"Dev and test favour {best_test} instead, so the evidence conflicts and is too small to justify a "
                f"change; re-run with a larger val set before deciding. Macro-F1 per method: {figures}.")
    return (f"Recommend evaluating {best_val} as a candidate replacement for {PRODUCTION_METHOD} "
            f"(threshold {m[best_val]['threshold']:.2f} from dev): it has the best val macro-F1. This is a "
            f"recommendation only; any change needs owner approval and a new config version. Macro-F1 per method: "
            f"{figures}.")


def build_markdown(result: Dict[str, Any]) -> str:
    m = result["methods"]
    sizes = result["split_sizes"]
    lines = [
        "# Matcher benchmark v1.0 (Phase 13)",
        "",
        f"Generated by `evaluation/benchmark/run_benchmark.py` on {result['generated_at'][:10]}. Gold labels "
        f"`{result['labels_file']}`, split `{result['splits_file']}` (seed 20261022), taxonomy "
        f"{result['taxonomy_version']}. Production config and τ were not changed.",
        "",
        "Each method predicts the top-1 node of the allowed type (syllabus → high_level_concept, interview → "
        "granular_skill) if its score clears the threshold, else `none`. Thresholds were swept on **dev** only "
        "(0.30–0.70, step 0.05), checked on **val**, and **test** was scored once.",
        "",
        "| Split | Syllabus rows (courses) | Interview rows (reports) |",
        "|---|---|---|",
    ]
    for s in SPLITS:
        lines.append(f"| {s} | {sizes[s]['syllabus']} ({', '.join(sizes[s]['syllabus_groups'])}) | "
                     f"{sizes[s]['interview']} ({', '.join(sizes[s]['interview_groups'])}) |")
    lines += ["", "## Test set (scored once)", "",
              "| Method | Threshold (from dev) | Accuracy | Macro-P | Macro-R | Macro-F1 | Syllabus acc. | Interview acc. |",
              "|---|---|---|---|---|---|---|---|"]
    for name, label in METHODS.items():
        t = m[name]["test"]
        lines.append(f"| {label} | {m[name]['threshold']:.2f} | {_pct(t['overall'])} | {t['overall']['macro_precision']:.3f} | "
                     f"{t['overall']['macro_recall']:.3f} | **{t['overall']['macro_f1']:.3f}** | "
                     f"{_pct(t['by_source_type']['syllabus'])} | {_pct(t['by_source_type']['interview'])} |")
    lines += ["", "## Dev and val at the chosen threshold", "",
              "| Method | Threshold | Dev acc. | Dev macro-F1 | Val acc. | Val macro-F1 |", "|---|---|---|---|---|---|"]
    for name, label in METHODS.items():
        d, v = m[name]["dev"]["overall"], m[name]["val"]["overall"]
        lines.append(f"| {label} | {m[name]['threshold']:.2f} | {_pct(d)} | {d['macro_f1']:.3f} | {_pct(v)} | {v['macro_f1']:.3f} |")
    lines += ["", "## Test accuracy by gold domain", "", "| Method | " + " | ".join(
        sorted(m["keyword"]["test"]["by_domain"])) + " |", "|---|" + "---|" * len(m["keyword"]["test"]["by_domain"])]
    for name, label in METHODS.items():
        by = m[name]["test"]["by_domain"]
        lines.append(f"| {label} | " + " | ".join(_pct(by[k]) for k in sorted(by)) + " |")
    lines += ["", f"![Test macro-F1 per method]({os.path.basename(OUT_PNG)})", "",
              "## Recommendation (production config and τ unchanged)", "", recommendation(result), "",
              "## Limitations", ""] + [f"- {item}" for item in LIMITATIONS] + [""]
    return "\n".join(lines) + "\n"


def render_reports(path: str = OUT_JSON) -> None:
    """Rebuild BENCHMARK.md and the chart from the saved results (no re-scoring; test is not evaluated again)."""
    with open(path, encoding="utf-8") as f:
        result = json.load(f)
    write_chart(result, OUT_PNG)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(build_markdown(result))


def main() -> None:
    if sys.argv[1:] == ["--render"]:
        render_reports()
        print(f"Re-rendered {OUT_MD} and {OUT_PNG} from {OUT_JSON}")
        return
    if os.path.exists(OUT_JSON):
        sys.exit(f"{OUT_JSON} exists; test is scored once per version. Use --render to rebuild the reports.")
    t_start = time.time()
    labels = load_labels(DEFAULT_LABELS)
    with open(DEFAULT_SPLITS, encoding="utf-8") as f:
        split_rows = list(csv.DictReader(f))
    split = {r["item_id"]: r["split"] for r in split_rows}
    group = {r["item_id"]: r["group"] for r in split_rows}
    from pipeline.config import load_scoring_config, resolve_path
    config = load_scoring_config()
    with open(resolve_path(config["taxonomy_path"]), encoding="utf-8") as f:
        data = json.load(f)
    nodes = data["nodes"] if isinstance(data, dict) and "nodes" in data else data
    rule = config["node_type_rule"]

    gold = {r["item_id"]: r["expected_primary"] for r in labels}
    meta = {r["item_id"]: {"source_type": r["source_type"],
                           "domain": r["expected_primary"].split(".")[0]} for r in labels}
    types = [rule[r["source_type"]] for r in labels]
    texts = [r["raw_text"] for r in labels]
    ids = [r["item_id"] for r in labels]

    timings, all_scores = {}, {}
    for name in METHODS:
        t = time.time()
        if name == "keyword":
            scored = [keyword_scores(text, nodes, nt) for text, nt in zip(texts, types)]
        elif name == "tfidf":
            scored = tfidf_scores(texts, nodes, types)
        else:
            scored = minilm_scores(labels, nodes, types, "description" if name == "minilm_desc" else "name_description")
        all_scores[name] = dict(zip(ids, scored))
        timings[name] = round(time.time() - t, 1)
        print(f"[{name}] scored {len(ids)} items in {timings[name]}s", flush=True)

    sizes = {}
    for s in SPLITS:
        members = [r for r in labels if split[r["item_id"]] == s]
        sizes[s] = {st: sum(1 for r in members if r["source_type"] == st) for st in ("syllabus", "interview")}
        for st in ("syllabus", "interview"):
            sizes[s][f"{st}_groups"] = sorted({group[r["item_id"]] for r in members if r["source_type"] == st})

    result = {
        "benchmark_version": "v1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "labels_file": "evaluation/benchmark/labels_v1.0.csv",
        "splits_file": "evaluation/benchmark/splits_v1.0.csv",
        "taxonomy_version": config["taxonomy_version"],
        "scoring_config_version": config["config_version"],
        "production_threshold": config["similarity_threshold"],
        "thresholds_swept": THRESHOLDS,
        "selection_rule": "dev only: max macro-F1, then accuracy, then closest to 0.50, then lower",
        "split_sizes": sizes,
        "methods": {},
        "timings_seconds": timings,
    }
    for name, label in METHODS.items():
        r = evaluate_method(all_scores[name], gold, split, meta)
        result["methods"][name] = dict(description=label, **r)
        print(f"[{name}] threshold {r['threshold']:.2f} (dev macro-F1 "
              f"{next(x['macro_f1'] for x in r['dev_sweep'] if x['threshold'] == r['threshold'])}); "
              f"val macro-F1 {r['val']['overall']['macro_f1']}; test macro-F1 {r['test']['overall']['macro_f1']}, "
              f"accuracy {r['test']['overall']['accuracy']}", flush=True)
    result["runtime_seconds"] = round(time.time() - t_start, 1)

    write_json(result, OUT_JSON)
    write_chart(result, OUT_PNG)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(build_markdown(result))
    print(f"Wrote {OUT_JSON}, {OUT_MD}, {OUT_PNG} in {result['runtime_seconds']}s")


if __name__ == "__main__":
    main()
