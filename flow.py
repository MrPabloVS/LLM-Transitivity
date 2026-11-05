"""Preview the coverage pilot with: uv run --locked flow run flow.py --dry-run."""

from pathlib import Path

from dotenv import load_dotenv

from llm_transitivity.inspect.flow import build_pilot_spec


def build_flow():
    root = Path(__file__).resolve().parent
    load_dotenv(root / ".env")
    return build_pilot_spec(root)


build_flow() if __name__ in {"__flow__", "__main__"} else None
