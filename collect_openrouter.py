"""Keep the existing OpenRouter export command available."""

from pathlib import Path

from llm_transitivity.cli.export import main as export_main
from llm_transitivity.runs.export import export_log, export_run

__all__ = ["export_log", "export_run", "main"]


def main() -> None:
    export_main(Path(__file__).resolve().parent)


if __name__ == "__main__":
    main()
