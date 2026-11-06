"""Run or preview the managed coverage pilot."""

import argparse
from pathlib import Path

from dotenv import load_dotenv
from inspect_flow.api import run

from llm_transitivity.inspect.flow import build_pilot_spec
from llm_transitivity.runs.runner import execute


def main(root: Path, argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="transitivity pilot", description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check the spec without creating an archive or calling models",
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Run the same single source case on the selected models",
    )
    parser.add_argument(
        "--profile", choices=["sonnet", "haiku", "pilot2"], default="sonnet"
    )
    parser.add_argument("--model", action="append")
    parser.add_argument("--concurrency", type=int, choices=[16, 32, 64], default=16)
    parser.add_argument("--load", action="store_true")
    parser.add_argument("--max-tasks", type=int)
    args = parser.parse_args(argv)
    load_dotenv(root / ".env")
    if (
        args.profile == "sonnet"
        and not args.model
        and args.concurrency == 16
        and not args.load
        and args.max_tasks is None
    ):
        spec = build_pilot_spec(root, preflight=args.preflight)
    else:
        spec = build_pilot_spec(
            root,
            preflight=args.preflight,
            profile=args.profile,
            selected_models=tuple(args.model) if args.model else None,
            concurrency=args.concurrency,
            load=args.load,
            **({"max_tasks": args.max_tasks} if args.max_tasks is not None else {}),
        )
    if args.dry_run:
        run(spec=spec, dry_run=True)
    elif not execute(spec, root):
        raise SystemExit(1)
