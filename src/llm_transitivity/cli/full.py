"""Prepare or execute all source cases with Pilot 3 controls."""

import argparse
from pathlib import Path


def main(root: Path, argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--detach", action="store_true")
    parser.add_argument("--resume", type=Path)
    args = parser.parse_args(argv)
    if args.dry_run and (args.detach or args.resume or args.prepare_only):
        parser.error("Dry-run cannot launch, resume, or prepare")
    if args.prepare_only and (args.detach or args.resume):
        parser.error("Prepare-only cannot launch or resume")
    if args.dry_run:
        from llm_transitivity.inspect.full import build_full_spec

        spec = build_full_spec(root)
        print(
            {
                "tasks": len(spec.tasks),
                "responses": spec.options.metadata["planned_responses"],
                "max_tasks": spec.options.max_tasks,
                "max_samples": spec.options.max_samples,
                "adaptive_connections": spec.options.metadata["adaptive_connections"],
                "max_connections_per_model": spec.options.metadata[
                    "max_connections_per_model"
                ],
            }
        )
        return
    from llm_transitivity.runs.full import execute, launch, prepare

    directory = (root / args.resume).resolve() if args.resume else prepare(root)
    print(f"Full corpus: {directory}", flush=True)
    if args.prepare_only:
        return
    if args.detach:
        print(f"Detached PID: {launch(root, directory)}")
    elif not execute(root, directory):
        raise SystemExit(1)
