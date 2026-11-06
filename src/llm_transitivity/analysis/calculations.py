"""Calculate report measures without files, network access, or Inspect."""

import heapq
from collections import Counter
from statistics import mean


def measures(rows: list[dict], field: str = "after") -> dict:
    """Keep agreement, usable coverage, and strict format denominators separate."""
    values = [row[field] for row in rows]
    categories = Counter(value["status"] for value in values)
    answered = categories["answered"]
    correct = sum(value["value"] == "C" for value in values)
    compliant = sum(value["format_compliant"] for value in values)
    return {
        "samples": len(rows),
        "categories": dict(categories),
        "correct": correct,
        "incorrect": sum(value["value"] == "I" for value in values),
        "answered": answered,
        "agreement": correct / answered if answered else None,
        "coverage": answered / len(rows) if rows else None,
        "format_compliant": compliant,
        "format_rate": compliant / len(rows) if rows else None,
    }


def merge_generation(ledger: dict, identifier: str, observation: dict) -> None:
    """Deduplicate observations and retain unknown costs and conflicting quotes."""
    if identifier not in ledger:
        ledger[identifier] = {
            "generation_id": identifier,
            "model": observation["model"],
            "cost_usd": None,
            "cost_source": None,
            "observations": [],
            "cost_conflicts": [],
            "provider_error_codes": [],
        }
    entry = ledger[identifier]
    if entry["model"] != observation["model"]:
        raise ValueError("A generation ID is associated with different models")
    if observation not in entry["observations"]:
        entry["observations"].append(observation)
    error = observation.get("provider_error_code")
    if error is not None and error not in entry["provider_error_codes"]:
        entry["provider_error_codes"].append(error)
    cost = observation.get("cost_usd")
    if cost is not None:
        old = entry["cost_usd"]
        if old is not None and abs(old - cost) > 1e-10:
            entry["cost_conflicts"].append({"previous": old, "observed": cost})
        # Prefer the captured response over a later lookup without adding them.
        if old is None or observation["source"] == "captured_response":
            entry["cost_usd"] = cost
            entry["cost_source"] = observation["source"]


def queue_seconds(durations: list[float], slots: int) -> float:
    """Schedule independent samples in source order on a fixed worker pool."""
    if slots < 1 or any(value < 0 for value in durations):
        raise ValueError("Queue needs positive capacity and nonnegative durations")
    workers = [0.0] * slots
    for duration in durations:
        available = heapq.heappop(workers)
        heapq.heappush(workers, available + duration)
    return max(workers)


def percentile90(values: list[float]) -> float:
    """Use linear interpolation between the observed minimum and maximum ranks."""
    values = sorted(values)
    if not values:
        raise ValueError("A latency stratum cannot be empty")
    rank = (len(values) - 1) * 0.9
    low = int(rank)
    high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (rank - low)


def cost_projection(rows: list[dict], populations: dict[str, int]) -> dict:
    """Expand mean final-response costs within each observed stratum."""
    grouped = {}
    for row in rows:
        grouped.setdefault(row["stratum"], []).append(row["final_cost_usd"])
    if set(grouped) != set(populations):
        raise ValueError("Cost strata do not match the full population")
    missing = [key for key, values in grouped.items() if any(v is None for v in values)]
    if missing:
        return {
            "central_usd": None,
            "three_attempts_usd": None,
            "missing_strata": missing,
        }
    central = sum(mean(values) * populations[key] for key, values in grouped.items())
    return {
        "central_usd": central,
        "three_attempts_usd": 3 * central,
        "missing_strata": [],
    }


def interval_union(intervals: list[tuple[float, float]]) -> float:
    """Measure active time once when sample or task intervals overlap."""
    if not intervals:
        return 0.0
    intervals = sorted(intervals)
    start, end = intervals[0]
    total = 0.0
    for next_start, next_end in intervals[1:]:
        if next_start > end:
            total += end - start
            start, end = next_start, next_end
        else:
            end = max(end, next_end)
    return total + end - start


def task_overhead(
    samples: list[tuple[float, float, float]], start: float, end: float, slots: int
) -> float | None:
    """Exclude reused samples; task timestamps retain only whole seconds."""
    if any(s < start or e >= end + 1 for s, e, _ in samples):
        return None
    return max(0.0, end - start - queue_seconds([d for _, _, d in samples], slots))
