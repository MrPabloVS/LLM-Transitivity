"""Preview the ten-case trial with: uv run --locked flow run flow.py --dry-run."""

from dotenv import load_dotenv
from inspect_flow import FlowSpec, FlowTask

from inspect_tasks import PROJECT_ROOT, hs_zero_shot

load_dotenv(PROJECT_ROOT / ".env")

FlowSpec(
    log_dir=str(PROJECT_ROOT / "logs" / "inspect"),
    log_dir_create_unique=True,
    store=None,
    tasks=[
        FlowTask(
            factory=hs_zero_shot,
            args={"dataset": "HS"},
            model="openrouter/anthropic/claude-sonnet-4.5",
        )
    ],
)
