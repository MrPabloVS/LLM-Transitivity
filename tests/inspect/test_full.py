"""Verify full-corpus selection, source fidelity, and fixed execution controls."""

from collections import Counter

from llm_transitivity.datasets.inputs import load_input
from llm_transitivity.datasets.pilot import verify
from llm_transitivity.domain.config import profile_models
from llm_transitivity.inspect.full import build_full_spec
from llm_transitivity.inspect.samples import build_samples
from tests.paths import PROJECT_ROOT


def test_full_spec_uses_every_case_and_preserves_model_controls():
    spec = build_full_spec(PROJECT_ROOT)
    assert len(spec.tasks) == 108
    assert spec.options.max_tasks == 108
    assert spec.options.max_samples == 64
    assert spec.options.metadata["planned_responses"] == 324000
    assert spec.options.metadata["effective_sample_ceiling"] == 6912
    counts = Counter()
    expected = {"openrouter/" + m.identifier: m for m in profile_models("pilot3")}
    for task in spec.tasks:
        assert not task.args["dataset"].startswith("pilot/")
        assert task.metadata["phase"] == "full-corpus"
        assert task.metadata["selected_case_count"] in {2000, 4000}
        assert task.model.config.max_connections == 1152
        assert task.model.model_args["provider"]["only"] == [
            expected[task.model.name].provider
        ]
        assert task.model.model_args["provider"]["allow_fallbacks"] is False
        counts[task.model.name] += task.metadata["selected_case_count"]
    assert set(counts.values()) == {54000}
    assert len(counts) == 6


def test_full_samples_keep_all_source_text_targets_and_stable_ids():
    seen = set()
    total = 0
    for entry in verify(PROJECT_ROOT)["datasets"]:
        data = load_input(PROJECT_ROOT, entry["dataset"])
        for sample, case in zip(build_samples(data), data.cases, strict=True):
            assert sample.input[-1].content == case.prompt
            assert sample.target == ("yes" if case.source_validity == "valid" else "no")
            assert sample.metadata["sample_uid"] not in seen
            seen.add(sample.metadata["sample_uid"])
            assert sample.id == sample.metadata["original_row"]
            total += 1
    assert total == len(seen) == 54000
