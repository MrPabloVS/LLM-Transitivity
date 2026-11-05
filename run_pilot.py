"""Keep the existing managed pilot command available."""

from pathlib import Path

from llm_transitivity.cli.pilot import main as pilot_main
from llm_transitivity.runs.archive import finalize_archive, prepare_archive
from llm_transitivity.runs.runner import execute

__all__ = ["execute", "finalize_archive", "main", "prepare_archive"]


def main() -> None:
    pilot_main(Path(__file__).resolve().parent)


if __name__ == "__main__":
    main()
