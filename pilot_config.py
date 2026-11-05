"""Keep the existing Flow configuration entry point available."""

from pathlib import Path

from llm_transitivity.inspect.flow import MODEL_GROUPS, MODELS
from llm_transitivity.inspect.flow import build_pilot_spec as package_spec

PROJECT_ROOT = Path(__file__).resolve().parent
__all__ = ["MODELS", "MODEL_GROUPS", "PROJECT_ROOT", "build_pilot_spec"]


def build_pilot_spec(*, preflight: bool = False):
    return package_spec(PROJECT_ROOT, preflight=preflight)
