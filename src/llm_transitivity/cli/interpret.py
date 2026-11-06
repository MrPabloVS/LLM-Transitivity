"""Create a static interpretation of the verified full-corpus report."""

import argparse
from pathlib import Path


def main(root: Path, argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    from llm_transitivity.analysis.interpret import interpret

    interpret(root, root / args.report, root / args.output)
