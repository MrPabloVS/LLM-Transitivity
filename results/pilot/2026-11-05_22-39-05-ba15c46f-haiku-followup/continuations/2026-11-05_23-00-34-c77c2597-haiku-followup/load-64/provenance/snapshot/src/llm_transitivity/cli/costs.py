"""Write a current fixed-provider cost estimate."""

import argparse
import json
from pathlib import Path

from llm_transitivity.costs.archive import save_estimate
from llm_transitivity.costs.estimate import estimate


def main(root: Path, argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="transitivity costs", description=__doc__)
    parser.add_argument("--profile", choices=["sonnet", "haiku"], default="sonnet")
    parser.add_argument("--followup", action="store_true")
    args = parser.parse_args(argv)
    report = (
        estimate(root)
        if args.profile == "sonnet" and not args.followup
        else estimate(root, profile=args.profile, followup=args.followup)
    )
    path = save_estimate(root, report)
    print(json.dumps(report["totals_usd"], indent=2))
    print(f"Saved {path}")
