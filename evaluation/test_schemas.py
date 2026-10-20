"""
Item 10: backend schemas use pydantic v2 idioms and emit no deprecation warnings.
"""
import importlib
import warnings

from pydantic.warnings import PydanticDeprecatedSince20

import backend.schemas


def test_schemas_emit_no_pydantic_deprecations():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        importlib.reload(backend.schemas)
    deprecations = [w for w in caught if issubclass(w.category, PydanticDeprecatedSince20)]
    assert deprecations == [], [str(w.message) for w in deprecations]


def test_examples_still_in_json_schema():
    schema = backend.schemas.TargetSelectionRequest.model_json_schema()
    assert schema["properties"]["company"]["examples"] == ["Amazon"]


def test_starlette_floor_in_requirements():
    # Security L5: starlette < 1.1.0 is inside the affected ranges of CVE-2026-48710/48817/48818.
    import os
    import re
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "requirements.txt"), encoding="utf-8") as f:
        lines = [line.strip() for line in f]
    match = next((re.fullmatch(r"starlette>=(\d+)\.(\d+)\.(\d+)", l) for l in lines if l.startswith("starlette")), None)
    assert match, "starlette must have a >= floor in requirements.txt"
    assert tuple(int(x) for x in match.groups()) >= (1, 1, 0)
