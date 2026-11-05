import asyncio
import math

import pytest
from inspect_ai.model import ChatCompletionChoice, ChatMessageAssistant, ModelOutput
from inspect_ai.scorer import SampleScore, Score, Target
from inspect_ai.solver import TaskState

from inspect_scoring import response_rates, source_agreement, source_label_match


@pytest.mark.parametrize(
    "text,target,stop,error,status,value",
    [
        ("yes", "yes", "stop", None, "answered", "C"),
        ("no", "no", "stop", None, "answered", "C"),
        ("yes", "no", "stop", None, "answered", "I"),
        ("no", "yes", "stop", None, "answered", "I"),
        (" YES ", "yes", "stop", None, "answered", "C"),
        ("", "no", "stop", None, "empty", "N"),
        ("  ", "no", "stop", None, "empty", "N"),
        ("no", "no", "content_filter", None, "content_filter", "N"),
        ("", "yes", "content_filter", None, "content_filter", "N"),
        ("yes.", "yes", "stop", None, "answered", "C"),
        ("yes because...", "yes", "stop", None, "answered", "C"),
        ("No, the conclusion does not follow.", "no", "stop", None, "answered", "C"),
        ("Answer: yes", "no", "stop", None, "answered", "I"),
        ("yes or no", "yes", "stop", None, "ambiguous", "N"),
        ("Yes. Actually, no.", "yes", "stop", None, "ambiguous", "N"),
        ("The answer is yes", "yes", "stop", None, "invalid_format", "N"),
        ("yesterday", "yes", "stop", None, "invalid_format", "N"),
        ("nobody", "no", "stop", None, "invalid_format", "N"),
        ("no", "no", "stop", "provider failed", "error", "N"),
    ],
)
def test_response_categories(text, target, stop, error, status, value):
    output = ModelOutput(
        choices=[
            ChatCompletionChoice(
                message=ChatMessageAssistant(content=text), stop_reason=stop
            )
        ],
        error=error,
    )
    state = TaskState(
        model="mockllm/model",
        sample_id=1,
        epoch=1,
        input="test",
        messages=[],
        output=output,
    )
    result = asyncio.run(source_label_match()(state, Target(target)))
    assert result.value == value
    assert result.answer == text
    assert result.metadata["status"] == status
    assert result.metadata["expected"] == target
    assert result.metadata["format_compliant"] == (
        status == "answered" and text.strip().lower() in {"yes", "no"}
    )
    if status == "answered":
        assert result.metadata["extracted_answer"] in {"yes", "no"}
    else:
        assert result.metadata["extracted_answer"] is None


def test_metrics_exclude_unusable_answers_from_agreement():
    scores = [
        SampleScore(score=Score(value=value, metadata={"status": status}))
        for value, status in [
            ("C", "answered"),
            ("I", "answered"),
            ("N", "empty"),
            ("N", "content_filter"),
            ("N", "invalid_format"),
            ("N", "error"),
        ]
    ]
    assert source_agreement()(scores) == 0.5
    rates = response_rates()(scores)
    assert rates["answered_rate"] == 2 / 6
    for status in ["empty", "content_filter", "invalid_format", "error"]:
        assert rates[f"{status}_rate"] == 1 / 6


def test_no_answers_has_no_agreement_estimate():
    assert math.isnan(source_agreement()([]))
    assert math.isnan(
        source_agreement()(
            [SampleScore(score=Score(value="N", metadata={"status": "empty"}))]
        )
    )


def test_inspect_publishes_separate_metrics_with_mock_model(tmp_path):
    from inspect_ai import Task, eval
    from inspect_ai.dataset import Sample

    task = Task(
        dataset=[Sample(input="test", target="yes")],
        scorer=source_label_match(),
    )
    logs = eval(
        task,
        model="mockllm/model",
        model_args={
            "custom_outputs": [
                ModelOutput.from_content("mockllm/model", "Yes, it follows.")
            ]
        },
        log_dir=str(tmp_path),
        display="none",
    )
    assert logs[0].status == "success"
    metrics = logs[0].results.scores[0].metrics
    assert metrics["source_agreement"].value == 1
    assert metrics["answered_rate"].value == 1
    assert metrics["format_compliant_rate"].value == 0
    for status in ["empty", "content_filter", "invalid_format", "error"]:
        assert metrics[f"{status}_rate"].value == 0
