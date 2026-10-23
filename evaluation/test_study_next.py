"""
Dashboard 'What to study next': per top priority gap, the VIT core course modules to revise (the syllabus units that
give the topic its coverage) and two verified practice links. Read-only: scores are never recomputed or changed.
"""
import json

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend import study
from evaluation import export_study_modules as esm

client = TestClient(app)

NODES = [
    {"topic_id": "dsa", "type": "high_level_concept", "parent_id": None, "name": "DSA"},
    {"topic_id": "dsa.trees", "type": "high_level_concept", "parent_id": "dsa", "name": "Trees"},
    {"topic_id": "dsa.trees.bst", "type": "granular_skill", "parent_id": "dsa.trees", "name": "BST"},
    {"topic_id": "dsa.heaps", "type": "high_level_concept", "parent_id": "dsa", "name": "Heaps"},
    {"topic_id": "dsa.heaps.top_k", "type": "granular_skill", "parent_id": "dsa.heaps", "name": "Top K"},
]


def _unit(code, number, title, matched, component="theory", scores=None):
    return {"course_code": code, "module_number": number, "module_title": title, "component": component,
            "matched_topic_ids": matched, "similarity_scores": scores or {t: 0.6 for t in matched}}


def test_modules_by_topic_uses_direct_and_inherited_matches():
    parsed = {
        "courses": [{"course_code": "BCSE202L", "course_title": "Data Structures and Algorithms"},
                    {"course_code": "BCSE202P", "course_title": "Data Structures and Algorithms Lab"}],
        "two_pass_mappings": [
            _unit("BCSE202L", 3, "Trees", ["dsa.trees"]),
            _unit("BCSE202L", 4, "Search trees", ["dsa.trees.bst", "dsa.trees"], scores={"dsa.trees.bst": 0.71,
                                                                                          "dsa.trees": 0.55}),
            _unit("BCSE202P", 7, "BST operations", ["dsa.trees.bst"], component="lab", scores={"dsa.trees.bst": 0.52}),
            _unit("BCSE202L", 1, "Intro", []),
        ],
    }
    out = esm.modules_by_topic(parsed, NODES)
    bst = out["dsa.trees.bst"]
    # direct matches first, then units matched only via the parent topic; each group by similarity, highest first
    assert [(m["course_code"], m["module_number"]) for m in bst] == [("BCSE202L", 4), ("BCSE202P", 7), ("BCSE202L", 3)]
    assert bst[0]["match"] == "direct" and bst[0]["similarity"] == 0.71
    assert bst[2]["course_title"] == "Data Structures and Algorithms" and bst[2]["match"] == "parent topic"
    assert bst[1]["component"] == "lab"
    assert out["dsa.heaps.top_k"] == []  # neither the topic nor its high-level parent is in any unit


def test_study_items_join_gaps_modules_and_links():
    gaps = [{"rank": 1, "topic_id": "dsa.heaps.top_k", "topic_name": "Top K", "coverage": 0.0, "priority_gap": 0.3},
            {"rank": 2, "topic_id": "dsa.trees.bst", "topic_name": "BST", "coverage": 0.8, "priority_gap": 0.1}]
    modules = {"dsa.trees.bst": [{"course_code": "BCSE202L", "course_title": "DSA", "module_number": 4,
                                  "module_title": "Search trees", "component": "theory", "match": "direct"}],
               "dsa.heaps.top_k": []}
    links = {"dsa.trees.bst": [{"title": "a", "url": "https://www.geeksforgeeks.org/a/"},
                               {"title": "b", "url": "https://www.geeksforgeeks.org/b/"}]}
    items = study.study_items(gaps, modules, links)
    assert [i["topic_id"] for i in items] == ["dsa.heaps.top_k", "dsa.trees.bst"]
    assert items[0]["in_core_curriculum"] is False and items[0]["modules"] == []
    assert items[0]["note"] == "Not covered in core curriculum"
    assert items[0]["practice"] == []
    assert items[1]["in_core_curriculum"] is True and items[1]["modules"][0]["module_number"] == 4
    assert len(items[1]["practice"]) == 2 and items[1]["coverage"] == 0.8


def test_every_shown_gap_has_two_verified_geeksforgeeks_links():
    links = study.load_links()
    for target in ("amazon_sde1", "microsoft_sde1", "flipkart_sde1"):
        data = client.get(f"/api/v1/study/{target}").json()
        assert data["items"], target
        for item in data["items"]:
            assert len(item["practice"]) == 2, item["topic_id"]
            assert all(p["url"].startswith("https://www.geeksforgeeks.org/") for p in item["practice"])
            assert item["practice"] == links[item["topic_id"]]


def test_study_endpoint_follows_saved_gap_order_and_leaves_scores_alone():
    before = client.get("/api/v1/results/amazon_sde1").json()["result"]
    data = client.get("/api/v1/study/amazon_sde1").json()
    assert data["status"] == "SUCCESS" and data["links_verified_on"] == "2026-10-23"
    assert [i["topic_id"] for i in data["items"]] == [g["topic_id"] for g in before["top_priority_gaps"][:10]]
    assert all(i["modules"] or i["note"] == "Not covered in core curriculum" for i in data["items"])
    assert any(i["modules"] for i in data["items"])
    assert client.get("/api/v1/results/amazon_sde1").json()["result"] == before


def test_study_endpoint_insufficient_and_unknown_targets():
    data = client.get("/api/v1/study/google_swe_l3").json()
    assert data["status"] == "INSUFFICIENT_DATA" and data["items"] == []
    assert client.get("/api/v1/study/nope").status_code == 404
    assert client.get("/api/v1/study/..%2Fconfig%2Fapi").status_code == 404


def test_export_never_overwrites(tmp_path):
    out = tmp_path / "study_modules.json"
    out.write_text("{}", encoding="utf-8")
    with pytest.raises(FileExistsError):
        esm.export(lambda: {"courses": [], "two_pass_mappings": []}, str(out))
    assert json.loads(out.read_text(encoding="utf-8")) == {}
