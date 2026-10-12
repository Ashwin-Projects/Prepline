"""Redirects Phase 12.1 unmapped-term logging to a temp file so test runs never write to data/processed/."""
import pytest

import pipeline.unmapped_terms_logger as unmapped_terms_logger


@pytest.fixture(autouse=True)
def isolated_unmapped_log(tmp_path, monkeypatch):
    log_path = str(tmp_path / "unmapped_terms.log")
    monkeypatch.setattr(unmapped_terms_logger, "LOG_PATH", log_path)
    return log_path
