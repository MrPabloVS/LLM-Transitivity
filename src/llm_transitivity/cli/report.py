"""Build an offline Markdown and HTML report from a closed full-corpus run."""

import argparse
from pathlib import Path


def main(root: Path, argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--correction", type=Path)
    args = parser.parse_args(argv)
    from llm_transitivity.analysis.full_report import report

    report(
        root,
        root / args.run,
        root / args.output,
        root / args.correction if args.correction else None,
    )
