"""Preview the coverage pilot with: uv run --locked flow run flow.py --dry-run."""

from dotenv import load_dotenv

from inspect_tasks import PROJECT_ROOT
from pilot_config import build_pilot_spec

load_dotenv(PROJECT_ROOT / ".env")

build_pilot_spec()
