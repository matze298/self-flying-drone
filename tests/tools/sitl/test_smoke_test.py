"""Tests for the SITL smoke-test script."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest
import typer
from pymavlink import mavutil
from typer.testing import CliRunner

if TYPE_CHECKING:
    from types import ModuleType


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
SMOKE_TEST_PATH = PROJECT_ROOT / "tools" / "sitl" / "smoke_test.py"
EXPECTED_HEARTBEAT_WAIT_S = 0.123
EXPECTED_CAPTURED_AT = "2026-07-06T12:34:56Z"
EXPECTED_LATITUDE_DEG = 47.397742
EXPECTED_LONGITUDE_DEG = 8.545594
EXPECTED_RELATIVE_ALTITUDE_M = 12.3
EXPECTED_BATTERY_VOLTAGE_V = 12.6
EXPECTED_BATTERY_CURRENT_A = 1.23
EXPECTED_BATTERY_REMAINING_PERCENT = 98
EXPECTED_CLI_TIMEOUT = 2.0
RUNNER = CliRunner()


@pytest.fixture
def smoke_test() -> ModuleType:
    """Load the standalone smoke-test script as a test module."""
    spec = importlib.util.spec_from_file_location("sitl_smoke_test", SMOKE_TEST_PATH)
    if spec is None or spec.loader is None:
        pytest.fail("Could not load SITL smoke-test module.")

    module = importlib.util.module_from_spec(spec)
    sys.modules["sitl_smoke_test"] = module
    previous_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous_dont_write_bytecode
    return module


def test_run_smoke_test_requires_position_by_default(
    smoke_test: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    """The default smoke-test path should fail when position telemetry is missing."""
    if mavutil.mavlink is None:
        raise RuntimeError("pymavlink dialect is not loaded.")

    mavlink = mavutil.mavlink
    heartbeat = mavlink.MAVLink_heartbeat_message(
        type=mavlink.MAV_TYPE_FIXED_WING,
        autopilot=mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA,
        base_mode=81,
        custom_mode=0,
        system_status=mavlink.MAV_STATE_STANDBY,
        mavlink_version=3,
    )
    connection = SimpleNamespace(
        target_system=1,
        target_component=0,
        wait_heartbeat=lambda **_: heartbeat,
        recv_match=lambda **_: None,
    )
    monkeypatch.setattr(smoke_test, "get_mav_connection", lambda _: connection)

    with pytest.raises(typer.Exit) as error:
        smoke_test.run_smoke_test("udp:127.0.0.1:14550", 1.0, tmp_path / "smoke.json")

    assert error.value.exit_code == 1


def test_run_smoke_test_requires_battery_by_default(
    smoke_test: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    """The default smoke-test path should fail when battery telemetry is missing."""
    if mavutil.mavlink is None:
        raise RuntimeError("pymavlink dialect is not loaded.")

    mavlink = mavutil.mavlink
    heartbeat = mavlink.MAVLink_heartbeat_message(
        type=mavlink.MAV_TYPE_FIXED_WING,
        autopilot=mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA,
        base_mode=81,
        custom_mode=0,
        system_status=mavlink.MAV_STATE_STANDBY,
        mavlink_version=3,
    )
    connection = SimpleNamespace(
        target_system=1,
        target_component=0,
        wait_heartbeat=lambda **_: heartbeat,
        recv_match=lambda **_: None,
    )
    monkeypatch.setattr(smoke_test, "get_mav_connection", lambda _: connection)
    monkeypatch.setattr(
        smoke_test.GlobalPosition,
        "from_message",
        staticmethod(
            lambda *_args, **_kwargs: smoke_test.GlobalPosition(
                lat=EXPECTED_LATITUDE_DEG,
                lon=EXPECTED_LONGITUDE_DEG,
                relative_alt=EXPECTED_RELATIVE_ALTITUDE_M,
            ),
        ),
    )

    with pytest.raises(typer.Exit) as error:
        smoke_test.run_smoke_test("udp:127.0.0.1:14550", 1.0, tmp_path / "smoke.json")

    assert error.value.exit_code == 1


def test_main_wires_cli_options_to_smoke_test(smoke_test: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    """The Typer CLI should pass parsed smoke-test options into the runner."""
    captured_options: dict[str, object] = {}

    def fake_run_smoke_test(
        connect: str,
        timeout: float,
        output: pathlib.Path,
        expected_vehicle: object,
        *,
        require_position: bool,
        require_battery: bool,
        require_ardupilot: bool,
    ) -> object:
        captured_options.update(
            {
                "connect": connect,
                "timeout": timeout,
                "output": output,
                "expected_vehicle": expected_vehicle,
                "require_position": require_position,
                "require_battery": require_battery,
                "require_ardupilot": require_ardupilot,
            }
        )
        return smoke_test.HeartbeatSummary(
            system_id=1,
            component_id=0,
            mode="MANUAL",
            armed=False,
            custom_mode=0,
            vehicle_type=1,
            autopilot=3,
            heartbeat_wait_s=0.123,
            captured_at=EXPECTED_CAPTURED_AT,
            latitude_deg=EXPECTED_LATITUDE_DEG,
            longitude_deg=EXPECTED_LONGITUDE_DEG,
            relative_altitude_m=EXPECTED_RELATIVE_ALTITUDE_M,
            battery_voltage_v=EXPECTED_BATTERY_VOLTAGE_V,
            battery_current_a=EXPECTED_BATTERY_CURRENT_A,
            battery_remaining_percent=EXPECTED_BATTERY_REMAINING_PERCENT,
        )

    app = typer.Typer()
    app.command()(smoke_test.main)
    monkeypatch.setattr(smoke_test, "run_smoke_test", fake_run_smoke_test)

    result = RUNNER.invoke(
        app,
        [
            "--connect",
            "udp:127.0.0.1:14551",
            "--timeout",
            str(int(EXPECTED_CLI_TIMEOUT)),
            "--output",
            "artifacts/sitl/custom.json",
            "--expected-vehicle",
            "rover",
            "--no-require-position",
            "--no-require-battery",
            "--no-require-ardupilot",
        ],
    )

    assert result.exit_code == 0
    assert captured_options["connect"] == "udp:127.0.0.1:14551"
    assert captured_options["timeout"] == EXPECTED_CLI_TIMEOUT
    assert captured_options["output"] == pathlib.Path("artifacts/sitl/custom.json")
    assert captured_options["expected_vehicle"] == smoke_test.ExpectedVehicle.ROVER
    assert captured_options["require_position"] is False
    assert captured_options["require_battery"] is False
    assert captured_options["require_ardupilot"] is False
