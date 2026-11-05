"""Check package boundaries without importing the evaluation framework."""

import subprocess
import sys

from tests.paths import PROJECT_ROOT


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


def test_cli_imports_do_not_build_runs_or_load_credentials():
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
        'llm_transitivity.cli.app', 'llm_transitivity.cli.pilot',
        'llm_transitivity.cli.datasets', 'llm_transitivity.cli.costs',
        'llm_transitivity.cli.export',
    ):
        importlib.import_module(name)
forbidden.assert_not_called()
""",
        ],
        check=True,
    )


def test_managed_dry_run_works_outside_repository(tmp_path):

    root = PROJECT_ROOT
    results = root / "results/pilot"
    before = {path.name for path in results.glob("*")}
    subprocess.run(
        [
            sys.executable,
            "-m",
            "llm_transitivity.cli.app",
            "--root",
            str(root),
            "pilot",
            "--preflight",
            "--dry-run",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert {path.name for path in results.glob("*")} == before
