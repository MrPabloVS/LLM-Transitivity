"""Select source rows without changing their order or representation."""

from llm_transitivity.evidence.serialization import record_digest


def stratum(row: list) -> tuple:
    return tuple(row[i] for i in (0, 3, 4, 5, 6, 7))


def select_rows(working: list[list], groups: dict, count: int) -> list[int]:
    return sorted(
        number
        for numbers in groups.values()
        for number in sorted(numbers, key=lambda n: (record_digest(working[n - 1]), n))[
            :count
        ]
    )
