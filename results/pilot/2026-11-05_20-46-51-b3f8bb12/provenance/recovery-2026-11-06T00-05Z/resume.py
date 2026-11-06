"""Resume the frozen pilot without changing the experiment configuration."""
import json
import sys
from pathlib import Path
from inspect_flow import FlowSpec
from inspect_flow.api import init, run
import llm_transitivity.inspect.tasks
from llm_transitivity.runs.archive import finalize_archive

root = Path(sys.argv[1])
archive = Path(sys.argv[2])
init(display="plain", dotenv_base_dir=str(root))
spec = FlowSpec.model_validate(json.loads((archive / "provenance/flow_spec.json").read_text()))
try:
    result = run(spec=spec, base_dir=str(root), handle_file=str(Path(__file__).with_name("flow-handle.json")))
except BaseException as error:
    try:
        finalize_archive(archive, flow_success=None, error_type=type(error).__name__)
    except BaseException as secondary:
        error.add_note(f"Archive finalization failed: {type(secondary).__name__}")
    raise
else:
    finalize_archive(archive, flow_success=result.success)
    raise SystemExit(0 if result.success else 1)
