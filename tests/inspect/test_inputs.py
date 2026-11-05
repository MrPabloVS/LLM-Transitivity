"""Keep input verification separate from filesystem-free Inspect adaptation."""

import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from llm_transitivity.datasets.inputs import load_input
from llm_transitivity.inspect.samples import build_samples, task_metadata, task_tags
from tests.paths import PROJECT_ROOT


@pytest.mark.parametrize("dataset", ["HS", "HS_HF_PR_2000", "pilot/HS_LF_PR_20"])
def test_sample_adaptation_has_no_file_or_git_operations(dataset, monkeypatch):
    data = load_input(PROJECT_ROOT, dataset)
    forbidden = Mock(
        side_effect=AssertionError("Unexpected input read during adaptation")
    )
    with monkeypatch.context() as patch:
        patch.setattr(Path, "open", forbidden)
        patch.setattr(Path, "read_bytes", forbidden)
        patch.setattr(Path, "read_text", forbidden)
        patch.setattr(subprocess, "check_output", forbidden)
        samples = build_samples(data)
        metadata = task_metadata(data)
        tags = task_tags(data, metadata)
    assert len(samples) == len(data.records)
    assert metadata["dataset_sha256"] == data.dataset_sha256
    assert f"family:{data.family}" in tags
    forbidden.assert_not_called()


@pytest.mark.parametrize("dataset", ["HS_HF_PR_2000", "pilot/HS_LF_PR_20"])
def test_loading_reads_original_file_once(dataset, monkeypatch):
    read_bytes, read_text = Path.read_bytes, Path.read_text
    reads = []

    def bytes_from(path):
        if path.parent.name == "userPrompts":
            reads.append(path)
        return read_bytes(path)

    def text_from(path, *args, **kwargs):
        if path.parent.name == "userPrompts":
            reads.append(path)
        return read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", bytes_from)
    monkeypatch.setattr(Path, "read_text", text_from)
    data = load_input(PROJECT_ROOT, dataset)
    build_samples(data)
    assert len(reads) == 1
    assert data.originals is not None
    assert data.originals[0][2]
