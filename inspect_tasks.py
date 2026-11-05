"""Keep the existing Inspect task entry point available."""

from pathlib import Path

from inspect_ai import task

from llm_transitivity.inspect.tasks import hs_zero_shot as package_task

PROJECT_ROOT = Path(__file__).resolve().parent


@task
def hs_zero_shot(dataset: str = "HS"):
    return package_task(dataset, root=str(PROJECT_ROOT))
