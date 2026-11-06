"""Measure agreement with source labels and report response coverage."""

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

from llm_transitivity.domain.scoring import EXTRACTION_RULE, interpret_response


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
        interpretation = interpret_response(
            raw,
            error=bool(output.error),
            content_filtered=bool(
                output.choices and output.stop_reason == "content_filter"
            ),
        )
        status = interpretation.status
        extracted = interpretation.extracted_answer
        value = (
            ("C" if extracted == target.text else "I") if status == "answered" else "N"
        )
        return Score(
            value=value,
            answer=raw,
            explanation="Compared with the source label; logical validity is not audited.",
            metadata={
                "status": status,
                "extraction_rule": EXTRACTION_RULE,
                "extraction_position": interpretation.extraction_position,
                "expected": target.text,
                "extracted_answer": extracted if status == "answered" else None,
                "format_compliant": interpretation.format_compliant,
            },
        )

    return score
