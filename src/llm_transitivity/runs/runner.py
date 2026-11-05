"""Execute a Flow specification with a managed result archive."""

from pathlib import Path

from inspect_flow.api import run

from llm_transitivity.runs.archive import finalize_archive, prepare_archive


def execute(spec, root: Path) -> bool:
    archive = prepare_archive(spec, root)
    success, error_type = None, None
    print(f"Results: {archive}")
    try:
        result = run(spec=spec)
        success = result.success
        return success
    except BaseException as error:
        error_type = type(error).__name__
        raise
    finally:
        finalize_archive(archive, flow_success=success, error_type=error_type)
