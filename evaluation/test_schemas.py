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
