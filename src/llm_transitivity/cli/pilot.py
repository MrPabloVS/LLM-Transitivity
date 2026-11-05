"""Run or preview the managed coverage pilot."""

import argparse
from pathlib import Path

from dotenv import load_dotenv
from inspect_flow.api import run

from llm_transitivity.inspect.flow import build_pilot_spec
from llm_transitivity.runs.runner import execute


def main(root: Path) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check the spec without creating an archive or calling models",
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Run the same single source case on all six models",
    )
    args = parser.parse_args()
    load_dotenv(root / ".env")
    spec = build_pilot_spec(root, preflight=args.preflight)
    if args.dry_run:
        run(spec=spec, dry_run=True)
    elif not execute(spec, root):
        raise SystemExit(1)
