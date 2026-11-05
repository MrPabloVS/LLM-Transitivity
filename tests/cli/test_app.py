"""Check installed command routing without external model requests."""

from unittest.mock import Mock

import pytest

from llm_transitivity.cli import app
from tests.paths import PROJECT_ROOT


@pytest.mark.parametrize("command", app.COMMANDS)
def test_command_help_works_without_repository_or_requests(
    command, tmp_path, monkeypatch
):
    import requests

    forbidden = Mock(side_effect=AssertionError("Unexpected request"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(requests.Session, "request", forbidden)
    with pytest.raises(SystemExit) as caught:
        app.main([command, "--help"])
    assert caught.value.code == 0
    forbidden.assert_not_called()


def test_root_discovery_from_nested_directory(monkeypatch):
    monkeypatch.chdir(PROJECT_ROOT / "src/llm_transitivity")
    assert app.repository_root(None) == PROJECT_ROOT


def test_explicit_root_from_outside_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert app.repository_root(PROJECT_ROOT) == PROJECT_ROOT
    with pytest.raises(ValueError, match="--root"):
        app.repository_root(None)


def test_dispatch_passes_root_and_command_arguments(monkeypatch):
    module = Mock()
    monkeypatch.setattr(app.importlib, "import_module", Mock(return_value=module))
    app.main(["--root", str(PROJECT_ROOT), "pilot", "--preflight", "--dry-run"])
    module.main.assert_called_once_with(PROJECT_ROOT, ["--preflight", "--dry-run"])


def test_only_historical_python_script_remains_in_root():
    assert {path.name for path in PROJECT_ROOT.glob("*.py")} == {"runBenchmark.py"}
