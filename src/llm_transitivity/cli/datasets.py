"""Prepare or verify the coverage pilot."""

import argparse
import subprocess
from pathlib import Path

from llm_transitivity.datasets.corpus import (
    MAIN_REVISION,
    dataset_names,
    verified_full_dataset,
)
from llm_transitivity.datasets.load_pool import prepare_load_pool, verify_load_pool
from llm_transitivity.datasets.pilot import prepare, verify


def main(root: Path, argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="transitivity datasets", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("prepare")
    build.add_argument("--per-stratum", type=int, required=True)
    check = commands.add_parser("verify")
    commands.add_parser("prepare-load")
    commands.add_parser("verify-load")
    check.add_argument(
        "--full",
        action="store_true",
        help="Verify all full datasets against preserved main",
    )
    args = parser.parse_args(argv)
    try:
        if args.command in {"prepare-load", "verify-load"}:
            operation = (
                prepare_load_pool
                if args.command == "prepare-load"
                else verify_load_pool
            )
            operation(root)
            print("Verified 216 load cases, two per observed pilot stratum.")
            return
        if args.command == "verify" and args.full:
            entries = [verified_full_dataset(root, name)[1] for name in dataset_names()]
            print(
                f"Verified {sum(e['case_count'] for e in entries):,} full cases, "
                f"{sum(len(e['strata']) for e in entries)} strata against main "
                f"{MAIN_REVISION}."
            )
            return
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
