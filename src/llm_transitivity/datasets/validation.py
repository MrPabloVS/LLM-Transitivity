"""Load benchmark datasets before any model calls or output writes."""

import json
from pathlib import Path


def load_dataset(path: Path) -> list[list]:
    """Read all cases and report the first incompatible row."""
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(f"{path}: cannot read dataset: {error}") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError(f"{path}: cannot decode dataset: {error}") from error

    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path}: expected a non-empty list of cases")

    text_fields = {
        0: "case type",
        2: "prompt",
        3: "frequency",
        4: "verbal time",
        5: "connectors",
        6: "validity",
        7: "canonical form",
    }
    for number, row in enumerate(rows, start=1):
        if not isinstance(row, list) or len(row) != 8:
            raise ValueError(f"{path}: case {number}: expected a list of 8 fields")
        for index, name in text_fields.items():
            if not isinstance(row[index], str) or not row[index].strip():
                raise ValueError(
                    f"{path}: case {number}: {name} (field {index}) "
                    "must be a non-empty string"
                )
    return rows
