"""Check corpus coverage and protection of existing pilot evidence."""

import pytest

from llm_transitivity.datasets import pilot
from tests.paths import PROJECT_ROOT


def test_full_corpus_and_deterministic_selection():
    manifest = pilot.verify(PROJECT_ROOT)
    assert len(manifest["datasets"]) == 18
    assert sum(e["case_count"] for e in manifest["datasets"]) == 54000
    assert sum(len(e["strata"]) for e in manifest["datasets"]) == 108
    assert sum(len(e["selected_rows"]) for e in manifest["datasets"]) == 540


def test_preparation_refuses_to_replace_evidence():
    with pytest.raises(ValueError, match="already exist"):
        pilot.prepare(PROJECT_ROOT, 5)
