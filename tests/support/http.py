"""Build lookup responses with explicit JSON, text, and header behavior."""

from unittest.mock import Mock


def response(status=200, payload=None, text=""):
    obj = Mock(
        status_code=status,
        headers={"x-request-id": "lookup", "set-cookie": "secret-cookie"},
        text=text,
    )
    if text:
        obj.json.side_effect = ValueError("not JSON")
    else:
        obj.json.return_value = (
            payload if payload is not None else {"data": {"id": "gen-test"}}
        )
    return obj
