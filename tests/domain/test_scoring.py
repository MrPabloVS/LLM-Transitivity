"""Check bounded extraction independently from strict response formatting."""

import pytest

from llm_transitivity.domain.scoring import interpret_response


@pytest.mark.parametrize("word", ["yes", "no", "YES", "NO"])
@pytest.mark.parametrize("punctuation", ["", ".", "!", "?"])
@pytest.mark.parametrize(
    "template,position",
    [
        ("**{word}**{punctuation}", "initial"),
        ("**{word}**{punctuation} Explanation.", "initial"),
        ("Explanation.\n**{word}**{punctuation}", "final_line"),
        ("Explanation.\nTherefore, {word}{punctuation}", "final_line"),
        ("Therefore, {word}{punctuation}", "final_line"),
    ],
)
def test_supported_answer_forms(word, punctuation, template, position):
    result = interpret_response(template.format(word=word, punctuation=punctuation))
    assert result.status == "answered"
    assert result.extracted_answer == word.lower()
    assert result.extraction_position == position
    assert result.format_compliant is False


@pytest.mark.parametrize(
    "text",
    [
        "**yes*",
        "*no**",
        "***yes***",
        "**yes***",
        "**no**x",
        "Explanation.\n**yes** More text.",
        "Explanation.\nTherefore, no. More text.",
        "Explanation.\nTherefore yes.",
        "Explanation.\n**yes**!!",
        "Explanation.\nTherefore, nobody.",
        "Explanation. **yes**",
    ],
)
def test_rejects_unbalanced_or_unbounded_forms(text):
    result = interpret_response(text)
    assert result.status == "invalid_format"
    assert result.extracted_answer is None
    assert result.format_compliant is False


@pytest.mark.parametrize(
    "text", ["**yes** or no", "Yes\nTherefore, no.", "no\n**yes**"]
)
def test_conflicting_answers_remain_ambiguous(text):
    assert interpret_response(text).status == "ambiguous"


@pytest.mark.parametrize(
    "error,filtered,status",
    [(True, True, "error"), (True, False, "error"), (False, True, "content_filter")],
)
def test_error_and_filter_precedence(error, filtered, status):
    result = interpret_response("**yes** or no", error=error, content_filtered=filtered)
    assert result.status == status
    assert result.extracted_answer is None
    assert result.format_compliant is False
