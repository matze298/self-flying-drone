"""Tests for the repository setup helper."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SETUP_PATH = PROJECT_ROOT / "setup.py"


@pytest.fixture
def setup_script() -> ModuleType:
    """Load the self-executable setup script as a test module."""
    spec = importlib.util.spec_from_file_location("setup_script", SETUP_PATH)
    if spec is None or spec.loader is None:
        pytest.fail("Could not load setup script module.")

    module = importlib.util.module_from_spec(spec)
    sys.modules["setup_script"] = module
    previous_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous_dont_write_bytecode
    return module


def test_setup_syncs_selected_workstreams_without_entering_shell(
    setup_script: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Default setup behavior should sync dependencies and then return."""
    commands: list[list[str]] = []

    def fake_run(command: list[str], *, cwd: pathlib.Path, check: bool) -> None:
        commands.append(command)
        assert cwd == setup_script.PROJECT_ROOT
        assert check is True

    monkeypatch.setattr(setup_script.subprocess, "run", fake_run)
    monkeypatch.setattr(setup_script, "activate_shell", pytest.fail, raising=False)

    setup_script.setup(workstream=["python"], docs=True, all_workstreams=False)

    assert commands == [["uv", "sync", "--group", "dev"]]
    assert f"Virtual environment is ready: {setup_script.PROJECT_VENV}" in capsys.readouterr().out


def test_default_setup_syncs_docs_workstream_and_returns(
    setup_script: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Default setup should sync docs dependencies and return to the caller."""
    commands: list[list[str]] = []

    def fake_run(command: list[str], *, cwd: pathlib.Path, check: bool) -> None:
        commands.append(command)
        assert cwd == setup_script.PROJECT_ROOT
        assert check is True

    monkeypatch.setattr(setup_script.subprocess, "run", fake_run)
    monkeypatch.setattr(setup_script, "activate_shell", pytest.fail, raising=False)

    setup_script.setup(workstream=None, docs=True, all_workstreams=False)

    assert commands == [["uv", "sync", "--group", "docs"]]
    assert f"Virtual environment is ready: {setup_script.PROJECT_VENV}" in capsys.readouterr().out


def test_sim_setup_syncs_workspace_packages(
    setup_script: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The sim workstream should include workspace package dependency groups."""
    commands: list[list[str]] = []

    def fake_run(command: list[str], *, cwd: pathlib.Path, check: bool) -> None:
        commands.append(command)
        assert cwd == setup_script.PROJECT_ROOT
        assert check is True

    monkeypatch.setattr(setup_script.subprocess, "run", fake_run)

    setup_script.setup(workstream=["sim"], docs=True, all_workstreams=False)

    assert commands == [["uv", "sync", "--all-packages", "--group", "sim"]]
    output = capsys.readouterr().out
    assert "Simulation Python tools are installed." in output
    assert f"Virtual environment is ready: {setup_script.PROJECT_VENV}" in output
