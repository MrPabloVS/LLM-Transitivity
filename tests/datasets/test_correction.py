"""Check the exact amendment and preserve all selection identities."""

import json
import subprocess

import pytest

from llm_transitivity.datasets.corpus import MAIN_REVISION, verify_dataset
from llm_transitivity.datasets.correction import DATASETS, MANIFEST, approved_changes
from llm_transitivity.datasets.load_pool import verify_load_pool
from llm_transitivity.datasets.pilot import verify
from tests.paths import PROJECT_ROOT


def test_exact_correction_and_original_rows():
    root = PROJECT_ROOT
    manifest = json.loads((root / MANIFEST).read_text())
    assert len(manifest["cases"]) == 612
    assert sum(r["replacements"] for r in manifest["cases"]) == 1224
    assert len({r["corrected_uid"] for r in manifest["cases"]}) == 612
    for name in DATASETS:
        dataset = verify_dataset(root, MAIN_REVISION, name)
        allowed = approved_changes(root, name, dataset.originals)
        for number, (old, new) in enumerate(zip(dataset.originals, dataset.records), 1):
            expected = old.copy()
            if number in allowed:
                expected[2] = allowed[number]["corrected_text"]
            assert new == expected
    pilot = verify(root)
    old = json.loads(
        subprocess.check_output(
            ["git", "-C", str(root), "show", "c1832fc:datasets/pilot/manifest.json"]
        )
    )
    assert [
        [r["original_row"] for r in e["selected_rows"]] for e in pilot["datasets"]
    ] == [[r["original_row"] for r in e["selected_rows"]] for e in old["datasets"]]
    load = verify_load_pool(root)
    old = json.loads(
        subprocess.check_output(
            ["git", "-C", str(root), "show", "c1832fc:datasets/load/manifest.json"]
        )
    )
    assert [(r["dataset"], r["original_row"]) for r in load["selected_rows"]] == [
        (r["dataset"], r["original_row"]) for r in old["selected_rows"]
    ]


def test_manifest_rejects_extra_text_change(tmp_path):
    payload = json.loads((PROJECT_ROOT / MANIFEST).read_text())
    payload["cases"][0]["corrected_text"] += " unauthorized"
    path = tmp_path / MANIFEST
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload))
    original = json.loads(
        (PROJECT_ROOT / "prompts/userPrompts/HS_HF_PA_500_complete.json").read_text()
    )
    with pytest.raises(ValueError, match="authorized"):
        approved_changes(tmp_path, "HS_HF_PA_2000", original)


def test_frozen_models_and_task_isolation():
    from llm_transitivity.datasets.correction import SOURCE_RUN
    from llm_transitivity.runs.correction import specs

    actual = specs(PROJECT_ROOT)
    original = json.loads(
        (PROJECT_ROOT / SOURCE_RUN / "corpus/provenance/flow_spec.json").read_text()
    )
    frozen = {(t["model"]["name"], t["args"]["dataset"]): t for t in original["tasks"]}
    assert len(actual["corpus"].tasks) == 12
    assert sum(len(t.sample_id) for t in actual["corpus"].tasks) == 3672
    assert len(actual["preflight"].tasks) == 6
    assert all(len(t.sample_id) == 1 for t in actual["preflight"].tasks)
    for task in actual["corpus"].tasks:
        from inspect_flow import FlowSpec

        reference = FlowSpec.model_validate(
            {**original, "tasks": [frozen[(task.model.name, task.args["dataset"])]]}
        ).tasks[0]
        assert task.model == reference.model
    actual["preflight"].tasks[0].model.config.max_tokens = 1
    assert actual["corpus"].tasks[0].model.config.max_tokens == 1024
