"""
Item 5: syllabus boilerplate (module, annexure, approved, academic council, proceedings,
years, dates, ...) is stripped before RAKE so it never becomes an intermediate concept.
"""
from pipeline.config import load_scoring_config
from pipeline.keyword_abstraction import strip_boilerplate, two_pass_abstract

STOPLIST = load_scoring_config()["syllabus"]["boilerplate_stoplist"]


def test_stoplist_covers_requested_terms():
    for term in ("module", "annexure", "approved", "academic council", "proceedings"):
        assert term in STOPLIST


def test_removes_stoplist_phrases_case_insensitive():
    out = strip_boilerplate("APPROVED by Academic Council PROCEEDINGS", ["approved", "academic council", "proceedings"]).lower()
    for phrase in ("approved", "academic council", "proceedings"):
        assert phrase not in out


def test_multiword_phrase_matches_across_whitespace():
    assert "council" not in strip_boilerplate("Academic\n  Council No. 63", ["academic council"]).lower()


def test_word_boundary_keeps_modular_arithmetic():
    out = strip_boilerplate("Modular arithmetic module", ["module"])
    assert "Modular arithmetic" in out
    assert "module" not in out.replace("Modular", "")


def test_removes_years_and_dates():
    out = strip_boilerplate("Board of Studies 03.07.2021 and 16-06-2022, revised 2024", [])
    for token in ("2021", "2022", "2024", "03.07", "16-06"):
        assert token not in out


def test_removes_bare_numbers_but_not_alphanumerics():
    out = strip_boilerplate("Module:1 x86 assembly 8 hours", ["module", "hours"])
    assert "x86" in out
    assert " 1 " not in f" {out} ".replace(":", " ") and " 8 " not in f" {out} "


def _concepts(text, source_type):
    return two_pass_abstract("src", text, source_type=source_type)["intermediate_concepts"]


def test_syllabus_concepts_exclude_boilerplate():
    text = "Approved by Academic Council No. 66 Date 16-06-2022. Module:1 Binary search trees 8 hours"
    concepts = _concepts(text, "syllabus")
    joined = " | ".join(concepts)
    for boilerplate in ("academic council", "approved", "2022", "module", "hours"):
        assert boilerplate not in joined, boilerplate
    assert "binary search trees" in concepts


def test_raw_text_preserved_in_record():
    text = "Module:1 Binary search trees"
    assert two_pass_abstract("src", text, source_type="syllabus")["raw_text"] == text


def test_interview_text_untouched():
    concepts = _concepts("Design the module loader approved in 2022", "interview")
    joined = " | ".join(concepts)
    assert "module" in joined
    assert "2022" in joined
