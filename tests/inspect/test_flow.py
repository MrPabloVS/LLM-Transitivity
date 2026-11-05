"""Check coverage, generation groups, and preflight selection."""

from collections import Counter
from pathlib import Path

from llm_transitivity.inspect.flow import MODEL_GROUPS, MODELS, build_pilot_spec
from tests.paths import PROJECT_ROOT


def test_six_models_cover_all_eighteen_datasets_without_reasoning_or_fallback():
    spec = build_pilot_spec(PROJECT_ROOT)
    assert len(spec.tasks) == 108
    assert len(MODELS) == 6
    assert len({task.args["dataset"] for task in spec.tasks}) == 18
    for task in spec.tasks:
        assert task.model.config.max_tokens == 1024
        args = task.model.model_args
        assert args["max_retries"] == 0
        assert args["provider"]["allow_fallbacks"] is False
        assert len(args["provider"]["only"]) == 1
        if "gpt-4o-mini" not in task.model.name:
            assert args["reasoning_enabled"] is False


def test_generation_groups_and_shared_folder():
    assert Counter(MODEL_GROUPS.values()) == {"earlier": 3, "later": 3}
    spec = build_pilot_spec(PROJECT_ROOT)
    assert Counter(task.metadata["generation_group"] for task in spec.tasks) == {
        "earlier": 54,
        "later": 54,
    }
    assert Path(spec.log_dir).name == "inspect"
    assert Path(spec.log_dir).parent.parent == PROJECT_ROOT / "results/pilot"
    assert spec.log_dir_create_unique is False
    for task in spec.tasks:
        assert f"generation_group:{task.metadata['generation_group']}" in task.tags


def test_preflight_is_one_identical_case_on_each_model():
    spec = build_pilot_spec(PROJECT_ROOT, preflight=True)
    assert len(spec.tasks) == 6
    assert len({task.model.name for task in spec.tasks}) == 6
    assert len({task.args["dataset"] for task in spec.tasks}) == 1
    assert len({tuple(task.sample_id) for task in spec.tasks}) == 1
    assert len(spec.tasks[0].sample_id) == 1
    assert spec.options.metadata["planned_responses"] == 6
    assert spec.options.metadata["selected_cases_per_model"] == 1
    assert spec.options.metadata["phase"] == "preflight"
    assert Path(spec.log_dir).parent.name.endswith("_preflight")
    assert all("phase:preflight" in task.tags for task in spec.tasks)
