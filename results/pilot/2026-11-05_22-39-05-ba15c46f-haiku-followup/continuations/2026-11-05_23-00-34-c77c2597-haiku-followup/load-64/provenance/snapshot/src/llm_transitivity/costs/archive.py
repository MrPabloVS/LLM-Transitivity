"""Save each estimate in a new directory without replacing earlier evidence."""

from datetime import datetime
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from llm_transitivity.evidence.serialization import json_bytes


def save_estimate(root: Path, report: dict) -> Path:
    timestamp = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).strftime(
        "%Y-%m-%d_%H-%M-%S"
    )
    directory = root / "results/cost_estimates" / f"{timestamp}-{uuid4().hex[:8]}"
    directory.mkdir(parents=True, exist_ok=False)
    path = directory / "estimate.json"
    with path.open("xb") as file:
        file.write(json_bytes(report))
    return path
