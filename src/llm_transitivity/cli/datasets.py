"""Prepare or verify the coverage pilot."""

import argparse
import subprocess
from pathlib import Path

from llm_transitivity.datasets.pilot import prepare, verify


def main(root: Path, argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="transitivity datasets", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("prepare")
    build.add_argument("--per-stratum", type=int, required=True)
    commands.add_parser("verify")
    args = parser.parse_args(argv)
    try:
        manifest = (
            prepare(root, args.per_stratum)
            if args.command == "prepare"
            else verify(root)
        )
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.error(str(error))
    entries = manifest["datasets"]
    print(
        f"Verified {sum(e['case_count'] for e in entries):,} full cases, "
        f"{sum(len(e['strata']) for e in entries)} strata, "
        f"{sum(len(e['selected_rows']) for e in entries)} pilot cases."
    )
