"""Build and verify a pilot against originals anchored to a Git revision."""

from pathlib import Path

from llm_transitivity.cli.datasets import main as datasets_main
from llm_transitivity.datasets.pilot import (
    DIMENSIONS,
    MANIFEST,
    TRANSLATED,
    construct,
    dataset_names,
    describe_dataset,
    describe_system,
    git_bytes,
    inventory,
    prepare,
    verified_pilot,
    verify,
)
from llm_transitivity.domain.selection import stratum
from llm_transitivity.evidence.serialization import digest, json_bytes, record_digest

ROOT = Path(__file__).resolve().parent

__all__ = [
    "DIMENSIONS",
    "MANIFEST",
    "ROOT",
    "TRANSLATED",
    "construct",
    "dataset_names",
    "describe_dataset",
    "describe_system",
    "digest",
    "git_bytes",
    "inventory",
    "json_bytes",
    "main",
    "prepare",
    "record_digest",
    "stratum",
    "verified_pilot",
    "verify",
]


def main() -> None:
    datasets_main(ROOT)


if __name__ == "__main__":
    main()
