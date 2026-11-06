"""Give validated benchmark records named fields without changing their values."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkCase:
    case_type: str
    source_id: object
    prompt: str
    frequency: str
    verbal_time: str
    connectors: str
    source_validity: str
    canonical_form: str

    @classmethod
    def from_record(cls, record: list) -> BenchmarkCase:
        """Adapt an eight-field record after dataset validation."""
        return cls(*record)
