"""Export model events and optionally refresh generation metadata."""

import argparse
from pathlib import Path

from dotenv import load_dotenv

from llm_transitivity.runs.export import export_run


def main(root: Path, argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="transitivity export", description=__doc__)
    parser.add_argument("log_dir", type=Path)
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Refresh generation metadata using read-only OpenRouter requests",
    )
    parser.add_argument(
        "--include-stored-content",
        action="store_true",
        help="Also request stored content; may require management-key access",
    )
    args = parser.parse_args(argv)
    if args.include_stored_content and not args.fetch:
        parser.error("--include-stored-content requires --fetch")
    load_dotenv(root / ".env")
    try:
        output = export_run(
            args.log_dir, fetch=args.fetch, include_content=args.include_stored_content
        )
    except ValueError as error:
        parser.error(str(error))
    print(f"Exported calls to {output}. Original Inspect logs were not modified.")
