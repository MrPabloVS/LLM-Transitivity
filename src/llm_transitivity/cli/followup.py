"""Prepare or execute the authorized Haiku follow-up."""

import argparse
import json
from pathlib import Path


def main(root: Path, argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="transitivity followup", description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--detach", action="store_true")
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--continue-from", type=Path)
    args = parser.parse_args(argv)
    if args.resume and args.continue_from:
        parser.error("Choose resume or a derived continuation")
    from llm_transitivity.runs.followup import execute, launch, prepare, preview

    if args.dry_run:
        if args.detach or args.resume or args.continue_from:
            parser.error("Dry-run cannot launch or resume a worker")
        print(json.dumps(preview(root), indent=2))
        return
    directory = (
        (root / args.resume).resolve()
        if args.resume
        else prepare(root, continue_from=(root / args.continue_from).resolve())
        if args.continue_from
        else prepare(root)
    )
    print(f"Follow-up: {directory}", flush=True)
    if args.detach:
        print(f"Detached PID: {launch(root, directory)}")
    elif not execute(root, directory):
        raise SystemExit(1)
