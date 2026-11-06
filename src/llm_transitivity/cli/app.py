"""Expose installed experiment commands without root-level Python adapters."""

import argparse
import importlib
import sys
import tomllib
from pathlib import Path

COMMANDS = {
    "correction": "Execute an approved text correction with frozen model settings",
    "interpret": "Create static analysis, figures, and a continuous PDF from a saved report",
    "explore": "Open DuckDB UI for saved report tables and cases",
    "report": "Build a full-corpus report from saved evidence without API requests",
    "full": "Prepare and run the verified full corpus with Pilot 3 controls",
    "followup": "Run the Haiku pilot and direct 64-slot load validation",
    "pilot": "Run or preview the coverage pilot",
    "datasets": "Prepare or verify pilot datasets",
    "costs": "Save a current public-provider cost estimate",
    "export": "Export a run and optionally refresh generation metadata",
}


def repository_root(path: Path | None) -> Path:
    candidates = (
        [path.resolve()] if path is not None else [Path.cwd(), *Path.cwd().parents]
    )
    for candidate in candidates:
        try:
            project = tomllib.loads((candidate / "pyproject.toml").read_text())
        except OSError, tomllib.TOMLDecodeError:
            continue
        if project.get("project", {}).get("name") == "llm-transitivity":
            return candidate
    raise ValueError("Run inside the project or set --root to its repository directory")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="transitivity",
        description="Prepare, run and inspect the transitivity experiment.",
        epilog="Commands: "
        + "; ".join(f"{name}: {text}" for name, text in COMMANDS.items()),
    )
    parser.add_argument(
        "--root",
        type=Path,
        help="Repository directory; defaults to the current project",
    )
    parser.add_argument("command", choices=COMMANDS)
    parser.add_argument("arguments", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    # Command help works before any repository or credential lookup.
    if any(value in {"-h", "--help"} for value in args.arguments):
        root = Path.cwd()
    else:
        try:
            root = repository_root(args.root)
        except ValueError as error:
            parser.error(str(error))
    module = importlib.import_module(f"llm_transitivity.cli.{args.command}")
    module.main(root, args.arguments)


if __name__ == "__main__":
    main()
