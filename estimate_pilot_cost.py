"""Keep the existing pilot cost command available."""

from pathlib import Path

from llm_transitivity.cli.costs import main as costs_main
from llm_transitivity.costs.calculation import generation_cost
from llm_transitivity.costs.estimate import estimate

__all__ = ["estimate", "generation_cost", "main"]


def main() -> None:
    costs_main(Path(__file__).resolve().parent)


if __name__ == "__main__":
    main()
