"""Keep export ordering, lookup caching, and full metadata independent of writes."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from inspect_ai.event import ModelEvent
from inspect_ai.model import GenerateConfig, ModelOutput

from llm_transitivity.runs import export


@pytest.mark.parametrize("fetch", [False, True])
def test_export_keeps_event_schema_and_per_sample_lookup_order(
    tmp_path, monkeypatch, fetch
):
    model = "openrouter/openai/gpt-4o-mini"
    events = []
    for generation_id in ["gen-first", "gen-second"]:
        output = ModelOutput.from_content(model, "yes")
        output.response_id = generation_id
        events.append(
            ModelEvent(
                model=model,
                input=[],
                tools=[],
                tool_choice="auto",
                config=GenerateConfig(),
                output=output,
            )
        )
    metadata = {
        "sample_uid": "source:1",
        "unknown": {"zero": 0, "null": None},
        "openrouter_http_calls": [
            {"response_body": {"json": {"id": value}}}
            for value in ["gen-retry", "gen-first", "gen-retry", None]
        ],
    }
    sample = SimpleNamespace(
        id=1, epoch=1, metadata=metadata, events=events, error=None
    )
    log = SimpleNamespace(
        samples=[sample],
        eval=SimpleNamespace(
            eval_id="eval", run_id="run", metadata={"experiment_run_id": "experiment"}
        ),
    )
    monkeypatch.setattr(export, "read_eval_log", Mock(return_value=log))
    lookup = Mock(
        side_effect=lambda generation_id, *args, **kwargs: {
            "generation_id": generation_id,
            "unknown": {"zero": 0, "null": None},
        }
    )
    monkeypatch.setattr(export, "generation_details", lookup)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
    path = tmp_path / "events.eval"
    path.write_bytes(b"mock log")
    records = export.export_log(path, fetch=fetch)
    assert [r["generation_id"] for r in records] == ["gen-first", "gen-second"]
    assert [r["model_event_index"] for r in records] == [1, 2]
    assert all(r["sample_metadata"] == metadata for r in records)
    assert all(r["sample_error"] is None for r in records)
    assert all(r["experiment_run_id"] == "experiment" for r in records)
    assert all(r["model_event"]["model"] == model for r in records)
    if fetch:
        assert [call.args[0] for call in lookup.call_args_list] == [
            "gen-first",
            "gen-retry",
            "gen-second",
        ]
        assert [r["generation_id"] for r in records[0]["generation_lookups"]] == [
            "gen-first",
            "gen-retry",
        ]
        assert records[1]["generation_lookups"][-1]["unknown"] == {
            "zero": 0,
            "null": None,
        }
    else:
        lookup.assert_not_called()
        assert all("generation_lookups" not in r for r in records)
