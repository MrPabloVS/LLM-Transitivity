"""Check explicit profiles and the balanced source-preserving load pool."""

import json
from collections import Counter

import pytest

from llm_transitivity.datasets.load_pool import derive_load_pool, verify_load_pool
from llm_transitivity.domain.config import MODEL_SPECS, profile_models
from llm_transitivity.evidence.serialization import record_digest
from llm_transitivity.inspect.flow import build_pilot_spec
from llm_transitivity.inspect.tasks import load_zero_shot
from tests.paths import PROJECT_ROOT


def test_profiles_preserve_default_and_replace_only_anthropic():
    assert profile_models() == MODEL_SPECS
    haiku = profile_models("haiku")
    assert len(haiku) == 6
    assert [m for m in haiku if not m.identifier.startswith("anthropic/")] == [
        m for m in MODEL_SPECS if not m.identifier.startswith("anthropic/")
    ]
    assert (
        next(m for m in haiku if m.identifier.endswith("5.5")).reasoning_effort
        == "medium"
    )
    for args in [("invalid", None), ("haiku", ("unknown",)), ("haiku", ())]:
        with pytest.raises(ValueError):
            profile_models(*args)


def test_load_selection_is_exactly_two_per_source_stratum():
    records, manifest = derive_load_pool(PROJECT_ROOT)
    assert manifest == verify_load_pool(PROJECT_ROOT)
    assert len(records) == 216
    assert set(
        Counter(
            (r["dataset"], r["stratum_id"]) for r in manifest["selected_rows"]
        ).values()
    ) == {2}
    for row, origin in zip(records, manifest["selected_rows"], strict=True):
        assert record_digest(row) == origin["working_record_sha256"]
        originals = json.loads(
            (PROJECT_ROOT / "datasets" / (origin["dataset"] + ".json")).read_text()
        )
        assert row == originals[origin["original_row"] - 1]


def test_load_samples_have_global_ids_and_keep_source_identifiers():
    task = load_zero_shot(root=str(PROJECT_ROOT))
    samples = list(task.dataset)
    assert len({s.id for s in samples}) == 216
    assert all(s.id == s.metadata["sample_uid"] for s in samples)
    assert all(isinstance(s.metadata["source_id"], list) for s in samples)
    assert Counter(s.metadata["dataset_family"] for s in samples) == {
        "HS": 72,
        "mHS": 144,
    }


def test_haiku_coverage_and_direct_load_counts_and_mutability():
    ids = ("anthropic/claude-haiku-4.5", "anthropic/claude-haiku-5.5")
    coverage = build_pilot_spec(PROJECT_ROOT, profile="haiku", selected_models=ids)
    assert len(coverage.tasks) == 36
    assert coverage.options.metadata["planned_responses"] == 1080
    load = build_pilot_spec(PROJECT_ROOT, profile="haiku", load=True, concurrency=64)
    assert len(load.tasks) == 6
    assert load.options.metadata["planned_responses"] == 1296
    assert load.options.max_samples == 64 and load.options.max_tasks == 1
    assert all(t.model.config.max_connections == 64 for t in load.tasks)
    assert (
        next(
            t for t in load.tasks if "haiku-5.5" in t.model.name
        ).model.config.reasoning_effort
        == "medium"
    )
    load.tasks[0].model.model_args["provider"]["only"].append("bad")
    assert all(
        "bad" not in t.model.model_args["provider"]["only"] for t in load.tasks[1:]
    )
    assert profile_models()[0].provider == "openai"


@pytest.mark.parametrize(
    "kwargs", [{"concurrency": 63}, {"load": True, "preflight": True}]
)
def test_invalid_execution_fails_before_configuration(kwargs):
    with pytest.raises(ValueError):
        build_pilot_spec(PROJECT_ROOT, **kwargs)


def test_pilot2_profile_runs_all_dataset_tasks_with_shared_model_pool():
    from llm_transitivity.inspect.flow import build_pilot_spec
    from tests.paths import PROJECT_ROOT

    spec = build_pilot_spec(
        PROJECT_ROOT, profile="pilot2", concurrency=32, max_tasks=108
    )
    assert len(spec.tasks) == 108
    assert spec.options.max_tasks == 108
    assert spec.options.max_samples == 32
    assert spec.options.metadata["planned_responses"] == 3240
    assert spec.options.metadata["configured_sample_ceiling"] == 3456
    assert spec.options.metadata["effective_sample_ceiling"] == 2808
    assert (
        "docs/model_cards/pilot-2.0-manifest.json"
        in spec.options.metadata["source_sha256"]
    )
    assert {task.model.name for task in spec.tasks} == {
        "openrouter/" + m.identifier for m in profile_models("pilot2")
    }
    assert {m.generation_group for m in profile_models("pilot2")} == {
        "earlier",
        "later",
    }
    for task in spec.tasks:
        assert task.model.config.max_connections == 576
        if task.model.name.startswith("openrouter/anthropic/"):
            assert task.model.config.reasoning_effort == "medium"
            assert task.model.model_args["reasoning_enabled"] is False
            assert task.model.model_args["provider"]["only"] == ["anthropic"]

    spec.tasks[0].model.config.max_connections = 1
    assert spec.tasks[1].model.config.max_connections == 576


def test_invalid_active_task_count_fails_before_archive_creation():
    from llm_transitivity.inspect.flow import build_pilot_spec
    from tests.paths import PROJECT_ROOT

    with pytest.raises(ValueError, match="Active task count"):
        build_pilot_spec(PROJECT_ROOT, max_tasks=0)
