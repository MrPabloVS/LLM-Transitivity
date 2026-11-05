"""Isolate source mutations from the preserved repository inputs."""

import json

import pytest

from llm_transitivity.datasets import pilot
from tests.paths import PROJECT_ROOT


@pytest.fixture
def copy_source_files(tmp_path, monkeypatch):
    def copy(paths):
        baseline = {}
        for relative in paths:
            payload = (PROJECT_ROOT / relative).read_bytes()
            baseline[relative] = payload
            target = tmp_path / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        monkeypatch.setattr(
            pilot, "git_bytes", lambda root, revision, path: baseline[path]
        )
        return tmp_path

    return copy


@pytest.fixture
def isolated_source(copy_source_files):
    name = "HS_LF_PR_2000"
    saved = json.loads((PROJECT_ROOT / pilot.MANIFEST).read_text())
    entry = next(e for e in saved["datasets"] if e["dataset"] == name)
    root = copy_source_files(
        [
            entry["working_path"],
            entry["original_path"],
            entry["pilot_path"],
            saved["system_prompt"]["path"],
            str(pilot.MANIFEST),
        ]
    )
    return root, name, entry
