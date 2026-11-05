import json
from pathlib import Path

from inspect_ai.log import read_eval_log
from inspect_ai.model import GenerateConfig
from inspect_flow import FlowModel
from inspect_flow.api import run

from experiment_metadata import EXPERIMENT_ID
from pilot_config import build_pilot_spec


def test_metadata_is_allowlisted_and_matches_configuration(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-secret-must-not-be-recorded")
    spec = build_pilot_spec()
    md = spec.options.metadata
    assert "test-secret-must-not-be-recorded" not in json.dumps(md)
    assert md["experiment_id"] == EXPERIMENT_ID
    assert md["experiment_run_id"]
    assert md["git"]["revision"]
    assert md["runtime"]["packages"]["inspect-ai"]
    assert set(md["source_sha256"]) >= {
        "inspect_tasks.py",
        "inspect_scoring.py",
        "uv.lock",
    }
    assert (
        md["generation_policy"]["max_output_tokens"]
        == spec.tasks[0].model.config.max_tokens
    )
    assert spec.options.log_samples is True
    assert spec.options.log_model_api is True
    for task in spec.tasks:
        assert task.metadata["requested_model"] == task.model.name.removeprefix(
            "openrouter/"
        )
        assert task.metadata["actual_provider"] is None
        assert task.metadata["reasoning_verified"] is False
        assert f"provider:{task.metadata['requested_provider']}" in task.tags


def test_metadata_survives_flow_and_eval_log_serialization(tmp_path):
    spec = build_pilot_spec()
    spec.tasks = [spec.tasks[0]]
    # Replace the live backend. This test has no external model calls.
    spec.tasks[0].model = FlowModel(
        name="mockllm/model", config=GenerateConfig(max_tokens=1024)
    )
    spec.log_dir = str(tmp_path)
    spec.log_dir_create_unique = False
    spec.options.limit = 1
    spec.options.display = "none"
    result = run(spec=spec)
    assert result.success
    paths = list(Path(result.log_dir).rglob("*.eval"))
    assert len(paths) == 1
    log = read_eval_log(str(paths[0]))
    assert log.status == "success"
    md = log.eval.metadata
    assert md["experiment_run_id"] == spec.options.metadata["experiment_run_id"]
    assert md["system_prompt"] == "zeroShot"
    assert md["dataset_name"].endswith("_20")
    assert md["provenance"]["original_sha256"]
    assert md["requested_provider"] == "openai"
    assert log.eval.task.startswith("zeroShot_")
    assert {"phase:coverage-pilot", "protocol:zeroShot", "family:HS"} <= set(
        log.eval.tags
    )
    sample = log.samples[0]
    assert sample.metadata["original_row"] == sample.id
    assert sample.metadata["original_labels"]["validity"] in {"valid", "invalid"}
    assert sample.metadata["sentence_sha256"]
    assert sample.metadata["sample_uid"]
    assert sample.metadata["tags"]
