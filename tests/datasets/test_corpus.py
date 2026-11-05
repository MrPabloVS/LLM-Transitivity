"""Verify complete sources without constructing a pilot selection."""

import subprocess
import sys
from unittest.mock import Mock

from llm_transitivity.datasets import corpus, pilot
from tests.paths import PROJECT_ROOT


def test_complete_dataset_verification_does_not_sample(monkeypatch):
    forbidden = Mock(side_effect=AssertionError("Unexpected pilot selection"))
    monkeypatch.setattr(pilot, "select_rows", forbidden)
    rows, entry = corpus.verified_full_dataset(PROJECT_ROOT, "HS_HF_PR_2000")
    assert len(rows) == len(entry["selected_rows"]) == 2000
    assert [row["original_row"] for row in entry["selected_rows"]] == list(
        range(1, 2001)
    )
    forbidden.assert_not_called()


def test_corpus_import_does_not_load_pilot_or_inspect():
    subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import llm_transitivity.datasets.corpus; "
                "assert not {'llm_transitivity.datasets.pilot', 'inspect_ai', "
                "'inspect_flow'} & sys.modules.keys()"
            ),
        ],
        check=True,
    )
