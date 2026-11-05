import json
from pathlib import Path

from inspect_ai.log import read_eval_log
from inspect_ai.model import GenerateConfig
from inspect_flow import FlowModel
from inspect_flow.api import run

from llm_transitivity.evidence.metadata import EXPERIMENT_ID
from llm_transitivity.inspect.flow import build_pilot_spec

ROOT = Path(__file__).resolve().parents[1]


def test_metadata_is_allowlisted_and_matches_configuration(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-secret-must-not-be-recorded")
    spec = build_pilot_spec(ROOT)
    md = spec.options.metadata
    assert "test-secret-must-not-be-recorded" not in json.dumps(md)
    assert md["experiment_id"] == EXPERIMENT_ID
    assert md["experiment_run_id"]
    assert md["git"]["revision"]
    assert md["runtime"]["packages"]["inspect-ai"]
    assert set(md["source_sha256"]) >= {
        "src/llm_transitivity/inspect/tasks.py",
        "src/llm_transitivity/inspect/scoring.py",
        "src/llm_transitivity/domain/config.py",
        "src/llm_transitivity/domain/cases.py",
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
    spec = build_pilot_spec(ROOT)
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


def test_policy_changes_reach_both_execution_and_metadata(monkeypatch):
    from dataclasses import replace

    from llm_transitivity.domain.config import GENERATION_POLICY
    from llm_transitivity.inspect import flow as pilot_config

    policy = replace(
        GENERATION_POLICY,
        max_output_tokens=256,
        max_connections=3,
        max_tasks=2,
        max_samples=3,
        request_timeout_seconds=45,
        request_max_retries=1,
        sdk_max_retries=1,
        flow_retry_attempts=2,
        flow_retry_cleanup=True,
        cache_prompt=True,
        stream=True,
        provider_fallback=True,
        require_parameters=False,
        reasoning_enabled=True,
    )
    monkeypatch.setattr(pilot_config, "GENERATION_POLICY", policy)
    spec = pilot_config.build_pilot_spec(
        Path(__file__).resolve().parents[1], preflight=True
    )
    assert spec.options.metadata["generation_policy"] == policy.metadata()
    assert spec.options.metadata["openrouter_capture"]["streaming"] is True
    assert spec.options.max_tasks == 2
    assert spec.options.max_samples == 3
    assert spec.options.retry_attempts == 2
    assert spec.options.retry_cleanup is True
    for task in spec.tasks:
        config = task.model.config
        assert (config.max_tokens, config.max_connections, config.timeout) == (
            256,
            3,
            45,
        )
        assert config.max_retries == 1
        assert config.cache_prompt is True
        args = task.model.model_args
        assert args["max_retries"] == 1
        assert args["stream"] is True
        assert args["provider"]["allow_fallbacks"] is True
        assert args["provider"]["require_parameters"] is False
        if "gpt-4o-mini" not in task.model.name:
            assert args["reasoning_enabled"] is True
            assert "reasoning:enabled" in task.tags
            assert task.metadata["reasoning_policy"] == "enabled"
