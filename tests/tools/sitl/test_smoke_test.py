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
RAW_LATITUDE = 473977420
RAW_LONGITUDE = 85455940
RAW_RELATIVE_ALTITUDE = 12300
RAW_BATTERY_VOLTAGE = 12600
RAW_BATTERY_CURRENT = 123


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


def test_decode_heartbeat_reports_manual_unarmed(smoke_test: ModuleType) -> None:
    """Heartbeat decoding should expose the safe baseline state."""
    connection = SimpleNamespace(target_system=1, target_component=0)
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

    position = smoke_test.GlobalPosition(
        lat=EXPECTED_LATITUDE_DEG,
        lon=EXPECTED_LONGITUDE_DEG,
        relative_alt=EXPECTED_RELATIVE_ALTITUDE_M,
    )
    battery_status = smoke_test.BatteryStatus(
        voltage_v=EXPECTED_BATTERY_VOLTAGE_V,
        current_a=EXPECTED_BATTERY_CURRENT_A,
        remaining_percent=EXPECTED_BATTERY_REMAINING_PERCENT,
    )
    summary = smoke_test.decode_heartbeat(
        connection,
        heartbeat,
        position=position,
        battery_status=battery_status,
        heartbeat_wait_s=EXPECTED_HEARTBEAT_WAIT_S,
        captured_at=EXPECTED_CAPTURED_AT,
    )

    assert summary.system_id == 1
    assert summary.component_id == 0
    assert summary.mode == "MANUAL"
    assert summary.armed is False
    assert summary.custom_mode == 0
    assert summary.vehicle_type == mavlink.MAV_TYPE_FIXED_WING
    assert summary.autopilot == mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA
    assert summary.heartbeat_wait_s == EXPECTED_HEARTBEAT_WAIT_S
    assert summary.latitude_deg == EXPECTED_LATITUDE_DEG
    assert summary.longitude_deg == EXPECTED_LONGITUDE_DEG
    assert summary.relative_altitude_m == EXPECTED_RELATIVE_ALTITUDE_M
    assert summary.battery_voltage_v == EXPECTED_BATTERY_VOLTAGE_V
    assert summary.battery_current_a == EXPECTED_BATTERY_CURRENT_A
    assert summary.battery_remaining_percent == EXPECTED_BATTERY_REMAINING_PERCENT


def test_global_position_scales_message_fields(smoke_test: ModuleType) -> None:
    """GLOBAL_POSITION_INT should be scaled to degrees and meters."""
    message = SimpleNamespace(lat=RAW_LATITUDE, lon=RAW_LONGITUDE, relative_alt=RAW_RELATIVE_ALTITUDE)
    connection = SimpleNamespace(recv_match=lambda **_: message)

    position = smoke_test.GlobalPosition.from_message(connection)

    assert position.lat == EXPECTED_LATITUDE_DEG
    assert position.lon == EXPECTED_LONGITUDE_DEG
    assert position.relative_alt == EXPECTED_RELATIVE_ALTITUDE_M


def test_global_position_allows_missing_message(smoke_test: ModuleType) -> None:
    """Missing position telemetry should not fail the basic heartbeat smoke test."""
    connection = SimpleNamespace(recv_match=lambda **_: None)

    position = smoke_test.GlobalPosition.from_message(connection)

    assert position.lat is None
    assert position.lon is None
    assert position.relative_alt is None


def test_battery_status_scales_message_fields(smoke_test: ModuleType) -> None:
    """BATTERY_STATUS should be scaled to volts, amps, and percent."""
    message = SimpleNamespace(
        voltages=[RAW_BATTERY_VOLTAGE],
        current_battery=RAW_BATTERY_CURRENT,
        battery_remaining=EXPECTED_BATTERY_REMAINING_PERCENT,
    )
    connection = SimpleNamespace(recv_match=lambda **_: message)

    battery_status = smoke_test.BatteryStatus.from_message(connection)

    assert battery_status.voltage_v == EXPECTED_BATTERY_VOLTAGE_V
    assert battery_status.current_a == EXPECTED_BATTERY_CURRENT_A
    assert battery_status.remaining_percent == EXPECTED_BATTERY_REMAINING_PERCENT


def test_battery_status_preserves_zero_current(smoke_test: ModuleType) -> None:
    """Zero battery current is a valid reading, not missing telemetry."""
    message = SimpleNamespace(
        voltages=[RAW_BATTERY_VOLTAGE],
        current_battery=0,
        battery_remaining=0,
    )
    connection = SimpleNamespace(recv_match=lambda **_: message)

    battery_status = smoke_test.BatteryStatus.from_message(connection)

    assert battery_status.voltage_v == EXPECTED_BATTERY_VOLTAGE_V
    assert battery_status.current_a == 0
    assert battery_status.remaining_percent == 0


def test_battery_status_allows_missing_message(smoke_test: ModuleType) -> None:
    """Missing battery telemetry should not fail the basic heartbeat smoke test."""
    connection = SimpleNamespace(recv_match=lambda **_: None)

    battery_status = smoke_test.BatteryStatus.from_message(connection)

    assert battery_status.voltage_v is None
    assert battery_status.current_a is None
    assert battery_status.remaining_percent is None


def test_write_artifact_writes_sorted_pretty_json(smoke_test: ModuleType, tmp_path: pathlib.Path) -> None:
    """Artifact writing should use readable deterministic JSON."""
    output = tmp_path / "artifacts" / "sitl" / "smoke.json"

    smoke_test.write_artifact({"source": "sitl-smoke-test", "schema_version": 1}, output)

    assert output.read_text(encoding="utf-8") == '{\n  "schema_version": 1,\n  "source": "sitl-smoke-test"\n}\n'


def test_create_artifact_includes_capture_timestamp(smoke_test: ModuleType) -> None:
    """Smoke artifacts should record when the observation was captured."""
    summary = smoke_test.HeartbeatSummary(
        system_id=1,
        component_id=0,
        mode="MANUAL",
        armed=False,
        custom_mode=0,
        vehicle_type=1,
        autopilot=3,
        heartbeat_wait_s=EXPECTED_HEARTBEAT_WAIT_S,
        captured_at=EXPECTED_CAPTURED_AT,
        latitude_deg=None,
        longitude_deg=None,
        relative_altitude_m=None,
        battery_voltage_v=None,
        battery_current_a=None,
        battery_remaining_percent=None,
    )

    artifact = smoke_test.create_artifact(summary)

    assert artifact["captured_at"] == EXPECTED_CAPTURED_AT
    assert artifact["heartbeat"]["captured_at"] == EXPECTED_CAPTURED_AT


def test_ensure_unarmed_exits_when_armed(smoke_test: ModuleType) -> None:
    """The smoke test should fail fast if the vehicle starts armed."""
    summary = smoke_test.HeartbeatSummary(
        system_id=1,
        component_id=0,
        mode="MANUAL",
        armed=True,
        custom_mode=0,
        vehicle_type=1,
        autopilot=3,
        heartbeat_wait_s=0.123,
        captured_at=EXPECTED_CAPTURED_AT,
        latitude_deg=None,
        longitude_deg=None,
        relative_altitude_m=None,
        battery_voltage_v=None,
        battery_current_a=None,
        battery_remaining_percent=None,
    )

    with pytest.raises(typer.Exit) as error:
        smoke_test.ensure_unarmed(summary)

    assert error.value.exit_code == 1


def test_ensure_vehicle_type_accepts_expected_vehicle(smoke_test: ModuleType) -> None:
    """Vehicle type validation should allow the selected expected vehicle."""
    if mavutil.mavlink is None:
        raise RuntimeError("pymavlink dialect is not loaded.")

    mavlink = mavutil.mavlink
    summary = smoke_test.HeartbeatSummary(
        system_id=1,
        component_id=0,
        mode="MANUAL",
        armed=False,
        custom_mode=0,
        vehicle_type=mavlink.MAV_TYPE_GROUND_ROVER,
        autopilot=3,
        heartbeat_wait_s=0.123,
        captured_at=EXPECTED_CAPTURED_AT,
        latitude_deg=None,
        longitude_deg=None,
        relative_altitude_m=None,
        battery_voltage_v=None,
        battery_current_a=None,
        battery_remaining_percent=None,
    )

    smoke_test.ensure_vehicle_type(summary, smoke_test.ExpectedVehicle.ROVER)


def test_ensure_vehicle_type_exits_on_unexpected_vehicle(smoke_test: ModuleType) -> None:
    """Vehicle type validation should fail when SITL runs a different vehicle."""
    if mavutil.mavlink is None:
        raise RuntimeError("pymavlink dialect is not loaded.")

    mavlink = mavutil.mavlink
    summary = smoke_test.HeartbeatSummary(
        system_id=1,
        component_id=0,
        mode="MANUAL",
        armed=False,
        custom_mode=0,
        vehicle_type=mavlink.MAV_TYPE_GROUND_ROVER,
        autopilot=3,
        heartbeat_wait_s=0.123,
        captured_at=EXPECTED_CAPTURED_AT,
        latitude_deg=None,
        longitude_deg=None,
        relative_altitude_m=None,
        battery_voltage_v=None,
        battery_current_a=None,
        battery_remaining_percent=None,
    )

    with pytest.raises(typer.Exit) as error:
        smoke_test.ensure_vehicle_type(summary, smoke_test.ExpectedVehicle.FIXED_WING)

    assert error.value.exit_code == 1


def test_ensure_position_available_accepts_complete_position(smoke_test: ModuleType) -> None:
    """Position validation should pass when all basic position fields are present."""
    summary = smoke_test.HeartbeatSummary(
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
        battery_voltage_v=None,
        battery_current_a=None,
        battery_remaining_percent=None,
    )

    smoke_test.ensure_position_available(summary)


def test_ensure_position_available_exits_on_missing_position(smoke_test: ModuleType) -> None:
    """Position validation should fail when strict position telemetry is required but missing."""
    summary = smoke_test.HeartbeatSummary(
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
        longitude_deg=None,
        relative_altitude_m=EXPECTED_RELATIVE_ALTITUDE_M,
        battery_voltage_v=None,
        battery_current_a=None,
        battery_remaining_percent=None,
    )

    with pytest.raises(typer.Exit) as error:
        smoke_test.ensure_position_available(summary)

    assert error.value.exit_code == 1


def test_ensure_battery_available_accepts_complete_battery(smoke_test: ModuleType) -> None:
    """Battery validation should pass when all basic battery fields are present."""
    summary = smoke_test.HeartbeatSummary(
        system_id=1,
        component_id=0,
        mode="MANUAL",
        armed=False,
        custom_mode=0,
        vehicle_type=1,
        autopilot=3,
        heartbeat_wait_s=0.123,
        captured_at=EXPECTED_CAPTURED_AT,
        latitude_deg=None,
        longitude_deg=None,
        relative_altitude_m=None,
        battery_voltage_v=EXPECTED_BATTERY_VOLTAGE_V,
        battery_current_a=0,
        battery_remaining_percent=0,
    )

    smoke_test.ensure_battery_available(summary)


def test_ensure_battery_available_exits_on_missing_battery(smoke_test: ModuleType) -> None:
    """Battery validation should fail when strict battery telemetry is required but missing."""
    summary = smoke_test.HeartbeatSummary(
        system_id=1,
        component_id=0,
        mode="MANUAL",
        armed=False,
        custom_mode=0,
        vehicle_type=1,
        autopilot=3,
        heartbeat_wait_s=0.123,
        captured_at=EXPECTED_CAPTURED_AT,
        latitude_deg=None,
        longitude_deg=None,
        relative_altitude_m=None,
        battery_voltage_v=EXPECTED_BATTERY_VOLTAGE_V,
        battery_current_a=None,
        battery_remaining_percent=EXPECTED_BATTERY_REMAINING_PERCENT,
    )

    with pytest.raises(typer.Exit) as error:
        smoke_test.ensure_battery_available(summary)

    assert error.value.exit_code == 1


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
    monkeypatch.setattr(smoke_test.mavutil, "mavlink_connection", lambda _: connection)

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
    monkeypatch.setattr(smoke_test.mavutil, "mavlink_connection", lambda _: connection)
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
