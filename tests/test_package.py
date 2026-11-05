"""Check package boundaries without importing the evaluation framework."""

import subprocess
import sys


def test_domain_imports_have_no_framework_or_network_dependencies():
    subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import llm_transitivity.domain.cases; "
                "import llm_transitivity.domain.config; "
                "import llm_transitivity.domain.selection; "
                "import llm_transitivity.domain.scoring; "
                "assert not {'inspect_ai', 'inspect_flow', 'requests', 'dotenv'} "
                "& sys.modules.keys()"
            ),
        ],
        check=True,
    )


def test_compatibility_imports_do_not_build_runs_or_load_credentials():
    subprocess.run(
        [
            sys.executable,
            "-c",
            """
import importlib
from unittest.mock import Mock, patch
import dotenv
import requests
from llm_transitivity.inspect import flow
from llm_transitivity.evidence import metadata

forbidden = Mock(side_effect=AssertionError('Unexpected import side effect'))
with (
    patch.object(flow, 'build_pilot_spec', forbidden),
    patch.object(metadata, 'run_metadata', forbidden),
    patch.object(dotenv, 'load_dotenv', forbidden),
    patch.object(requests.Session, 'request', forbidden),
):
    for name in (
        'flow', 'run_pilot', 'pilot_config', 'inspect_tasks', 'inspect_scoring',
        'prepare_pilot', 'dataset_validation', 'experiment_config',
        'benchmark_cases', 'experiment_metadata', 'openrouter_telemetry',
        'collect_openrouter', 'estimate_pilot_cost',
    ):
        importlib.import_module(name)
forbidden.assert_not_called()
""",
        ],
        check=True,
    )


def test_managed_dry_run_works_outside_repository(tmp_path):
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    results = root / "results/pilot"
    before = {path.name for path in results.iterdir()}
    subprocess.run(
        [sys.executable, str(root / "run_pilot.py"), "--preflight", "--dry-run"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert {path.name for path in results.iterdir()} == before
