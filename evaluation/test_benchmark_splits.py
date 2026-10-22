"""
Phase 13 part 2: grouped dev/val/test split (evaluation/benchmark/SPLIT_PLAN.md). A course's theory and lab files and
an interview report's questions are one group; groups never straddle splits.
"""
import collections

import pytest

from evaluation.benchmark import build_splits as bs
from evaluation.benchmark import validate_labels as vl


@pytest.fixture(scope="module")
def rows():
    return vl.load_labels(vl.DEFAULT_LABELS)


@pytest.fixture(scope="module")
def splits(rows):
    return bs.build_splits(rows)


def test_group_key():
    assert bs.group_key({"source_type": "syllabus", "course_or_report": "BCSE202L"}) == "BCSE202"
    assert bs.group_key({"source_type": "syllabus", "course_or_report": "BCSE202P"}) == "BCSE202"
    assert bs.group_key({"source_type": "syllabus", "course_or_report": "BCSE101E"}) == "BCSE101"
    assert bs.group_key({"source_type": "interview", "course_or_report": "AMZ004"}) == "AMZ004"


def test_same_seed_same_splits(rows, splits):
    assert bs.build_splits(rows) == splits
    assert bs.SEED == 20261022


def test_no_group_in_two_splits(splits):
    seen = collections.defaultdict(set)
    for s in splits:
        seen[(s["source_type"], s["group"])].add(s["split"])
    assert all(len(v) == 1 for v in seen.values())


def test_every_row_assigned_once(rows, splits):
    assert sorted(s["item_id"] for s in splits) == sorted(r["item_id"] for r in rows)
    assert all(s["split"] in ("dev", "val", "test") for s in splits)


def test_each_split_has_both_source_types(splits):
    for split in ("dev", "val", "test"):
        assert {s["source_type"] for s in splits if s["split"] == split} == {"syllabus", "interview"}


def test_shares_within_one_group_of_target(rows, splits):
    for source_type in ("syllabus", "interview"):
        members = [s for s in splits if s["source_type"] == source_type]
        sizes = collections.Counter(s["group"] for s in members)
        for split, share in bs.TARGETS.items():
            achieved = sum(1 for s in members if s["split"] == split)
            assert abs(achieved - share * len(members)) <= max(sizes.values()), (source_type, split, achieved)


def test_dsa_theory_and_lab_together(splits):
    by_item = {s["item_id"]: s["split"] for s in splits}
    assert by_item["BCSE202L_mod_1"] == by_item["BCSE202P_exp_1"]


def test_never_overwrites(tmp_path, rows):
    out = tmp_path / "splits.csv"
    bs.write_splits(bs.build_splits(rows), str(out))
    with pytest.raises(FileExistsError):
        bs.write_splits(bs.build_splits(rows), str(out))
