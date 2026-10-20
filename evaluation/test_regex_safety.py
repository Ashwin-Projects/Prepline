"""
Security H1: syllabus parsing must stay fast on adversarial text (no catastrophic regex backtracking).

Each case runs in a subprocess with a hard timeout, so a regression fails the test instead of hanging
the suite. The embedding stack is stubbed out so the subprocess imports in about a second.
"""
import os
import subprocess
import sys
import textwrap

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = " " * 10000

CASES = {
    "labelled L T P C + 10k spaces": ("segment", "Course Code: ABC123\nCourse Title: X\nL T P C" + W + "x\n"),
    "labelled L T P J C + 10k spaces + colon": ("segment", "Course Code: ABC123\nL T P J C" + W + ":" + W + "x\n"),
    "VIT L T P C + 10k spaces": ("segment", "ABC1234 Title L T P C" + W + "x\n"),
    "VIT marker, 10k-space continuation line": ("segment", "ABC1234 Title L T P C\nx" + W + "\n1 2 3\n"),
    "VIT title + 10k spaces": ("segment", "ABC1234 Title" + W + "x\n"),
    "VIT title + 10k spaces before digits": ("segment", "ABC1234 Title" + W + "1 2 3\n"),
    "bare header + 10k-space lines": ("segment", "ABC1234 Title" + W + "\n" + W + "1 2\n"),
    "module header + 10k spaces": ("modules", "ABC1234 Title 3 0 0 3\nModule" + W + ":" + W + "x\n"),
    "module title + 10k spaces before hours": ("modules", "ABC1234 Title 3 0 0 3\nModule:1 Trees" + W + "(" + W + "x\n"),
    "boilerplate: Module + 10k spaces": ("strip", "Module" + W + ":" + W + "x"),
}

_RUNNER = textwrap.dedent(
    """
    import sys, time, types
    sys.path.insert(0, ROOT)
    stub = types.ModuleType("pipeline.taxonomy_mapper")
    stub.map_source_to_taxonomy = lambda **kw: {"matched_topic_ids": []}
    sys.modules["pipeline.taxonomy_mapper"] = stub
    from pipeline import syllabus_parser as sp
    from pipeline.keyword_abstraction import strip_boilerplate
    kind, text = sys.argv[1], open(sys.argv[2], encoding="utf-8").read()
    start = time.perf_counter()
    if kind == "segment":
        sp.segment_courses(text)
    elif kind == "modules":
        for course in sp.segment_courses(text):
            sp.parse_course_modules(course)
    else:
        strip_boilerplate(text, ["module"])
    print(f"{time.perf_counter() - start:.4f}")
    """
).replace("ROOT", repr(ROOT))


@pytest.mark.parametrize("label", list(CASES))
def test_parsing_adversarial_whitespace_is_fast(label, tmp_path):
    kind, text = CASES[label]
    payload = tmp_path / "input.txt"
    payload.write_text(text, encoding="utf-8")
    try:
        out = subprocess.run(
            [sys.executable, "-c", _RUNNER, kind, str(payload)],
            capture_output=True, text=True, timeout=30, cwd=ROOT,
        )
    except subprocess.TimeoutExpired:
        pytest.fail(f"{label}: parsing did not finish within 30 s (catastrophic backtracking)")
    assert out.returncode == 0, out.stderr[-2000:]
    elapsed = float(out.stdout.strip().splitlines()[-1])
    assert elapsed < 1.0, f"{label}: {elapsed:.2f}s"
