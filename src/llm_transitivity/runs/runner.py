"""Execute a Flow specification with a managed result archive."""

import sys
from pathlib import Path

from inspect_flow.api import run

from llm_transitivity.runs.archive import finalize_archive, prepare_archive


def execute(spec, root: Path) -> bool:
    archive = prepare_archive(spec, root)
    print(f"Results: {archive}")
    try:
        result = run(spec=spec)
    except BaseException as error:
        try:
            finalize_archive(
                archive, flow_success=None, error_type=type(error).__name__
            )
        # Preserve the primary failure even if finalization is interrupted.
        except BaseException as finalization_error:  # noqa: BLE001
            note = f"Archive finalization failed: {type(finalization_error).__name__}"
            error.add_note(note)
            print(note, file=sys.stderr)
        raise
    else:
        finalize_archive(archive, flow_success=result.success)
        return result.success
