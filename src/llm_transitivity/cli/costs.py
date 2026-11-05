"""Write a current fixed-provider cost estimate."""

import json
from pathlib import Path

from llm_transitivity.costs.estimate import estimate
from llm_transitivity.evidence.serialization import json_bytes


def main(root: Path) -> None:
    report = estimate(root)
    path = root / "docs/pilot_cost_estimate.json"
    path.write_bytes(json_bytes(report))
    print(json.dumps(report["totals_usd"], indent=2))
    print(f"Saved {path}")
