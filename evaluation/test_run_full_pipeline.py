"""
Item 9: versioned results. run_full_pipeline writes results/amazon_sde1_v1.2.json by default and
never overwrites an existing results file; compare_results builds the v1.0 -> v1.1 change log.
"""
import json
import os
import sys

import pytest

import evaluation.run_full_pipeline as rfp
from evaluation.compare_results import build_changes
from pipeline.config import find_target


def test_default_out_is_v1_2():
    assert os.path.basename(rfp.DEFAULT_OUT) == "amazon_sde1_v1.2.json"
    assert rfp.RESULTS_VERSION == "v1.2"


def test_resolve_pdf_paths_from_folder_glob(tmp_path):
    for name in ("BCSE202P_lab.pdf", "BCSE202L_th.pdf", "B.Tech_CSE_2024_2025.pdf"):
        (tmp_path / name).write_bytes(b"%PDF-1.4")
    found = rfp.resolve_pdf_paths([], str(tmp_path), "BCSE*.pdf")
    assert found == [str(tmp_path / "BCSE202L_th.pdf"), str(tmp_path / "BCSE202P_lab.pdf")]
    # explicit --pdf files come first; a file named twice is listed once
    extra = str(tmp_path / "B.Tech_CSE_2024_2025.pdf")
    both = rfp.resolve_pdf_paths([extra, found[0]], str(tmp_path), "BCSE*.pdf")
    assert both == [extra] + found


def test_refuses_to_run_without_pdfs(tmp_path, monkeypatch):
    out = tmp_path / "out.json"
    monkeypatch.setattr(sys, "argv", ["run_full_pipeline.py", "--pdf-dir", str(tmp_path), "--out", str(out)])
    with pytest.raises(SystemExit) as exc:
        rfp.main()
    assert "No syllabus PDFs" in str(exc.value)
    assert not out.exists()


def test_refuses_to_overwrite_existing_results(tmp_path, monkeypatch):
    out = tmp_path / "amazon_sde1_v1.0.json"
    out.write_text('{"S_comp": 51.538}', encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["run_full_pipeline.py", "--pdf", str(tmp_path / "missing.pdf"), "--out", str(out)])
    with pytest.raises(SystemExit) as exc:
        rfp.main()
    assert "overwrite" in str(exc.value)
    assert out.read_text(encoding="utf-8") == '{"S_comp": 51.538}'


def _result(s_comp, gaps, runtime, universe=3):
    return {
        "S_comp": s_comp,
        "runtime_seconds": runtime,
        "scoring_universe_size": universe,
        "report_count": 21,
        "top_priority_gaps": [
            {"rank": i + 1, "topic_id": t, "topic_name": t.title(), "importance": 0.1, "coverage": 0.0, "priority_gap": g}
            for i, (t, g) in enumerate(gaps)
        ],
    }


def test_build_changes_tables():
    old = _result(51.538, [("dsa.heaps", 0.0952), ("dsa.dp.grid", 0.0667)], 1050.9)
    step_a = _result(46.43, [("dsa.heaps", 0.1111), ("dsa.dp.grid", 0.0778)], 955.0)
    new = _result(30.0, [("dsa.dp.grid", 0.2), ("os.deadlocks.prevention_avoidance", 0.1)], 400.0)
    md = build_changes(old, new, [("Item 3 - interview filtering", step_a), ("Item 5 - boilerplate", new)],
                       notes=["v1.1 covers only 3 core courses."])

    assert "51.538" in md and "30.0" in md
    assert "1050.9" in md and "400.0" in md
    assert "v1.1 covers only 3 core courses." in md
    # side-by-side top gaps: one row per rank
    assert "| 1 | Dsa.Heaps (`dsa.heaps`) | 0.0952 | Dsa.Dp.Grid (`dsa.dp.grid`) | 0.2 |" in md
    # attribution: delta per step, and gaps entering/leaving the top 10
    assert "| Item 3 - interview filtering | 46.43 | -5.108 |" in md
    assert "| Item 5 - boilerplate | 30.0 | -16.43 |" in md
    assert "`os.deadlocks.prevention_avoidance`" in md.split("Item 5 - boilerplate", 1)[1]


AMAZON_V1_2 = os.path.join(rfp.ROOT, "results", "amazon_sde1_v1.2_course_syllabi.json")
SYLLABI_DIR = os.path.join(rfp.ROOT, "data", "raw", "syllabi")
COURSE_GLOB = "B[CM]*.pdf"


@pytest.mark.skipif(not rfp.resolve_pdf_paths([], SYLLABI_DIR, COURSE_GLOB),
                    reason="course syllabus PDFs are gitignored and not present")
def test_amazon_results_identical_after_target_refactor(tmp_path):
    """Re-runs Amazon SDE-1 from data/processed/amazon_sde1/ (config-driven target) against the 28 course PDFs (26 core courses)."""
    with open(AMAZON_V1_2, encoding="utf-8") as f:
        stored = json.load(f)
    target = dict(find_target("Amazon", "SDE-1"), excluded_csv=str(tmp_path / "excluded.csv"))
    pdfs = rfp.resolve_pdf_paths([], SYLLABI_DIR, COURSE_GLOB)

    rerun = rfp.run(pdfs, target, syllabus_id=stored["syllabus_id"],
                    transcriptions_dir=rfp.default_transcriptions_dir(SYLLABI_DIR))

    for key in ("company", "role", "report_count", "status", "S_comp", "scoring_universe_size", "taxonomy_version",
                "scoring_config_version", "syllabus_files", "core_courses", "courses_kept", "syllabus_units",
                "units_by_component", "units_with_matches", "topics_present", "depth_counts", "top_priority_gaps",
                "unmapped_terms_summary", "top_unmapped_terms"):
        assert rerun[key] == stored[key], key
    filtered = {k: v for k, v in rerun["interview_filter"].items() if k != "excluded_questions_file"}
    assert filtered == {k: v for k, v in stored["interview_filter"].items() if k != "excluded_questions_file"}


def test_default_transcriptions_dir(tmp_path):
    assert rfp.default_transcriptions_dir(str(tmp_path)) is None
    (tmp_path / "transcribed").mkdir()
    assert rfp.default_transcriptions_dir(str(tmp_path)) == str(tmp_path / "transcribed")
    assert rfp.default_transcriptions_dir(None) is None
