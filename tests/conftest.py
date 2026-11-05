"""Provide fresh run specifications without shared mutable evaluation state."""

import pytest

from tests.paths import PROJECT_ROOT


@pytest.fixture
def mock_run_spec(tmp_path):
    from inspect_ai.model import GenerateConfig
    from inspect_flow import FlowModel

    from llm_transitivity.inspect.flow import build_pilot_spec

    spec = build_pilot_spec(PROJECT_ROOT)
    spec.tasks = [spec.tasks[0]]
    spec.tasks[0].model = FlowModel(
        name="mockllm/model", config=GenerateConfig(max_tokens=1024)
    )
    spec.log_dir = str(tmp_path / "one-run" / "inspect")
    spec.options.limit = 1
    spec.options.display = "none"
    return spec
