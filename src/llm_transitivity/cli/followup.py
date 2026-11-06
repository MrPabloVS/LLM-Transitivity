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
    parser.add_argument("--profile", choices=["haiku", "pilot2"], default="haiku")
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args(argv)
    if args.prepare_only and (
        args.detach or args.resume or args.continue_from or args.dry_run
    ):
        parser.error("Prepare-only cannot launch, resume, continue, or dry-run")
    if args.continue_from and args.profile != "haiku":
        parser.error("Derived continuation requires the haiku profile")
    if args.resume and args.continue_from:
        parser.error("Choose resume or a derived continuation")
    from llm_transitivity.runs.followup import execute, launch, prepare, preview

    if args.dry_run:
        if args.detach or args.resume or args.continue_from:
            parser.error("Dry-run cannot launch or resume a worker")
        print(
            json.dumps(
                preview(root)
                if args.profile == "haiku"
                else preview(root, profile=args.profile),
                indent=2,
            )
        )
        return
    if args.resume:
        directory = (root / args.resume).resolve()
    elif args.continue_from:
        directory = prepare(root, continue_from=(root / args.continue_from).resolve())
    elif args.profile == "haiku":
        directory = prepare(root)
    else:
        directory = prepare(root, profile=args.profile)
    print(f"Follow-up: {directory}", flush=True)
    if args.prepare_only:
        return
    if args.detach:
        print(f"Detached PID: {launch(root, directory)}")
    elif not execute(root, directory):
        raise SystemExit(1)
