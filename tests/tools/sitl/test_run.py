"""Tests for the ArduPilot SITL helper."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
HELPER_PATH = PROJECT_ROOT / "tools" / "sitl" / "run.py"


@pytest.fixture
def helper() -> ModuleType:
    """Load the standalone helper script as a test module."""
    spec = importlib.util.spec_from_file_location("sitl_run_helper", HELPER_PATH)
    if spec is None or spec.loader is None:
        pytest.fail("Could not load SITL helper module.")

    module = importlib.util.module_from_spec(spec)
    sys.modules["sitl_run_helper"] = module
    previous_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous_dont_write_bytecode
    return module


def test_env_file_sets_default_repo_path(helper: ModuleType, tmp_path: pathlib.Path) -> None:
    """A local .env value should be used when no CLI path is passed."""
    (tmp_path / ".env").write_text("ARDUPILOT_REPO=~/ws/ardupilot\n", encoding="utf-8")

    repo_path = helper.resolve_ardupilot_repo(None, project_root=tmp_path)

    assert repo_path == pathlib.Path("~/ws/ardupilot").expanduser()


def test_cli_repo_path_overrides_env_file(helper: ModuleType, tmp_path: pathlib.Path) -> None:
    """An explicit CLI path should take precedence over .env."""
    (tmp_path / ".env").write_text("ARDUPILOT_REPO=/ignored\n", encoding="utf-8")

    repo_path = helper.resolve_ardupilot_repo("~/custom/ardupilot", project_root=tmp_path)

    assert repo_path == pathlib.Path("~/custom/ardupilot").expanduser()


def test_checkout_validation_requires_sim_vehicle(helper: ModuleType, tmp_path: pathlib.Path) -> None:
    """A checkout is valid only when the SITL launcher exists."""
    assert not helper.is_ardupilot_checkout(tmp_path)

    launcher = tmp_path / "Tools" / "autotest" / "sim_vehicle.py"
    launcher.parent.mkdir(parents=True)
    launcher.write_text("#!/usr/bin/env python3\n", encoding="utf-8")

    assert helper.is_ardupilot_checkout(tmp_path)


def test_build_sim_vehicle_command_includes_plane_console_map_and_wipe(helper: ModuleType) -> None:
    """The generated SITL command should launch ArduPlane with expected options."""
    repo_path = pathlib.Path("ardupilot")

    command = helper.build_sim_vehicle_command(
        repo_path,
        vehicle=helper.Vehicle.plane,
        wipe=True,
        mavlink_out="udp:127.0.0.1:14550",
    )

    assert command[0] == str(repo_path / "Tools" / "autotest" / "sim_vehicle.py")
    assert "-v" in command
    assert "ArduPlane" in command
    assert "--console" in command
    assert "--map" in command
    assert "-w" in command
    assert "--out=udp:127.0.0.1:14550" in command


def test_build_sim_vehicle_command_can_launch_copter(helper: ModuleType) -> None:
    """The generated SITL command should expose a copter vehicle option."""
    repo_path = pathlib.Path("ardupilot")

    command = helper.build_sim_vehicle_command(repo_path, vehicle=helper.Vehicle.copter, wipe=False, mavlink_out=None)

    assert "-v" in command
    assert "ArduCopter" in command
    assert "-w" not in command
    assert not any(part.startswith("--out=") for part in command)


def test_build_sim_vehicle_command_launches_heli_as_copter_frame(helper: ModuleType) -> None:
    """Helicopter SITL should use ArduCopter with the heli frame."""
    repo_path = pathlib.Path("ardupilot")

    command = helper.build_sim_vehicle_command(repo_path, vehicle=helper.Vehicle.heli, wipe=False, mavlink_out=None)

    assert "-v" in command
    assert "ArduCopter" in command
    assert "-f" in command
    assert "heli" in command


def test_build_sim_vehicle_command_can_override_mavlink_output(helper: ModuleType) -> None:
    """The MAVLink output endpoint should be configurable."""
    repo_path = pathlib.Path("ardupilot")

    command = helper.build_sim_vehicle_command(
        repo_path,
        vehicle=helper.Vehicle.plane,
        wipe=False,
        mavlink_out="udp:127.0.0.1:14551",
    )

    assert "--out=udp:127.0.0.1:14551" in command


def test_external_tool_env_removes_active_venv_from_path(helper: ModuleType) -> None:
    """ArduPilot tools should not inherit uv's isolated script virtualenv."""
    env = {
        "PATH": "/repo/.venv/bin:/usr/local/bin:/usr/bin",
        "PYTHONHOME": "/bad/pythonhome",
        "PYTHONPATH": "/bad/pythonpath",
        "UV": "1",
        "UV_PROJECT_ENVIRONMENT": "/repo/.venv",
        "VIRTUAL_ENV": "/repo/.venv",
    }

    clean_env = helper.external_tool_env(env)

    assert clean_env["PATH"] == "/usr/local/bin:/usr/bin"
    assert "PYTHONHOME" not in clean_env
    assert "PYTHONPATH" not in clean_env
    assert "UV" not in clean_env
    assert "UV_PROJECT_ENVIRONMENT" not in clean_env
    assert "VIRTUAL_ENV" not in clean_env


def test_external_tool_env_removes_project_venv_even_without_virtual_env(helper: ModuleType) -> None:
    """A stale project .venv PATH entry should not affect ArduPilot's env-python shebangs."""
    project_venv_bin = str(helper.PROJECT_ROOT / ".venv" / "bin")
    env = {
        "PATH": f"{project_venv_bin}:/usr/local/bin:/usr/bin",
    }

    clean_env = helper.external_tool_env(env)

    assert clean_env["PATH"] == "/usr/local/bin:/usr/bin"
