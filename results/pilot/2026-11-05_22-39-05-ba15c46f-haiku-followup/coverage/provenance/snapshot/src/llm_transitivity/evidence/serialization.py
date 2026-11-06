"""Preserve the existing JSON bytes and SHA-256 representations."""

import hashlib
import json


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def record_digest(row: list) -> str:
    return digest(
        json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )
