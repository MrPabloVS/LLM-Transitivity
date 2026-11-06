"""Interpret response content independently from evaluation frameworks."""

import re
from dataclasses import dataclass

EXTRACTION_RULE = "initial_or_final_line_v1"


@dataclass(frozen=True)
class Interpretation:
    status: str
    extracted_answer: str | None
    format_compliant: bool
    extraction_position: str | None


def interpret_response(
    raw: str, *, error: bool = False, content_filtered: bool = False
) -> Interpretation:
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
    if error:
        status = "error"
    elif content_filtered:
        status = "content_filter"
    elif not answer:
        status = "empty"
    elif len(tokens) > 1:
        status = "ambiguous"
    elif extracted is None:
        status = "invalid_format"
    else:
        status = "answered"
    return Interpretation(
        status=status,
        extracted_answer=extracted if status == "answered" else None,
        format_compliant=status == "answered" and answer in {"yes", "no"},
        extraction_position=position if status == "answered" else None,
    )
