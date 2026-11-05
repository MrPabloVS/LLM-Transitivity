"""Measure agreement with source labels and report response coverage."""

import re

from inspect_ai.scorer import (
    Metric,
    SampleScore,
    Score,
    Scorer,
    Target,
    metric,
    scorer,
)
from inspect_ai.solver import TaskState


@metric
def source_agreement() -> Metric:
    """Use only deterministically interpreted responses as the denominator."""

    def calculate(scores: list[SampleScore]) -> float:
        answered = [
            s.score
            for s in scores
            if (s.score.metadata or {}).get("status") == "answered"
        ]
        if not answered:
            return float("nan")
        # Inspect can reduce the standard C/I scores to numeric 1/0 values.
        return sum(s.value in ("C", 1) for s in answered) / len(answered)

    return calculate


@metric
def response_rates() -> Metric:
    """Report named response categories as fractions of scored samples."""

    def calculate(scores: list[SampleScore]) -> dict[str, float]:
        rates = {
            f"{status}_rate": (
                sum((s.score.metadata or {}).get("status") == status for s in scores)
                / len(scores)
                if scores
                else float("nan")
            )
            for status in [
                "answered",
                "empty",
                "content_filter",
                "invalid_format",
                "ambiguous",
                "error",
            ]
        }
        rates["format_compliant_rate"] = (
            sum(
                (s.score.metadata or {}).get("format_compliant") is True for s in scores
            )
            / len(scores)
            if scores
            else float("nan")
        )
        return rates

    return calculate


@scorer(
    metrics=[
        source_agreement(),
        response_rates(),
    ]
)
def source_label_match() -> Scorer:
    """Keep unusable responses separate from agreement and disagreement."""

    async def score(state: TaskState, target: Target) -> Score:
        if target.text not in {"yes", "no"}:
            raise ValueError("Expected a source-label target of yes or no")
        output = state.output
        raw = output.completion
        answer = raw.strip().lower()
        # Read an initial answer or a standalone answer on the final line.
        match = re.match(r"^(?:answer:\s*)?(yes|no)(?=$|[\s.,!?:;])", answer)
        position = "initial" if match else None
        if not match:
            match = re.fullmatch(
                r"(?:answer:\s*)?(yes|no)[.!?]?", answer.split("\n")[-1].strip()
            )
            position = "final_line" if match else None
        tokens = set(re.findall(r"\b(?:yes|no)\b", answer))
        extracted = match.group(1) if match and len(tokens) == 1 else None
        if output.error:
            status = "error"
        elif output.choices and output.stop_reason == "content_filter":
            status = "content_filter"
        elif not answer:
            status = "empty"
        elif len(tokens) > 1:
            status = "ambiguous"
        elif extracted is None:
            status = "invalid_format"
        else:
            status = "answered"
        value = (
            ("C" if extracted == target.text else "I") if status == "answered" else "N"
        )
        return Score(
            value=value,
            answer=raw,
            explanation="Compared with the source label; logical validity is not audited.",
            metadata={
                "status": status,
                "extraction_rule": "initial_or_final_line_v1",
                "extraction_position": position if status == "answered" else None,
                "expected": target.text,
                "extracted_answer": extracted if status == "answered" else None,
                "format_compliant": status == "answered" and answer in {"yes", "no"},
            },
        )

    return score
