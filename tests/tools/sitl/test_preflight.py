"""Tests for reusable SITL preflight checks."""

from __future__ import annotations

import pytest
import typer
from pymavlink import mavutil

from tools.sitl import preflight, telemetry


def summary(**overrides: object) -> telemetry.HeartbeatSummary:
    """Build a valid summary and allow focused overrides per test."""
    if mavutil.mavlink is None:
        raise RuntimeError("pymavlink dialect is not loaded.")

    values = {
        "system_id": 1,
        "component_id": 0,
        "mode": "MANUAL",
        "armed": False,
        "custom_mode": 0,
        "vehicle_type": mavutil.mavlink.MAV_TYPE_FIXED_WING,
        "autopilot": mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA,
        "heartbeat_wait_s": 0.123,
        "captured_at": "2026-07-06T12:34:56Z",
        "latitude_deg": 47.397742,
        "longitude_deg": 8.545594,
        "relative_altitude_m": 12.3,
        "battery_voltage_v": 12.6,
        "battery_current_a": 0.0,
        "battery_remaining_percent": 100,
    }
    values.update(overrides)
    return telemetry.HeartbeatSummary(**values)


def test_run_strict_preflight_accepts_safe_fixed_wing_ardupilot_state() -> None:
    """Strict preflight should accept the baseline smoke-test state."""
    preflight.run_strict_preflight(summary(), expected_vehicle=telemetry.ExpectedVehicle.FIXED_WING)


def test_run_strict_preflight_rejects_armed_vehicle_before_commands() -> None:
    """Strict preflight should fail before any command-sending path when armed."""
    with pytest.raises(typer.Exit) as error:
        preflight.run_strict_preflight(summary(armed=True), expected_vehicle=telemetry.ExpectedVehicle.FIXED_WING)

    assert error.value.exit_code == 1


def test_ensure_vehicle_type_accepts_expected_vehicle() -> None:
    """Vehicle type validation should allow the selected expected vehicle."""
    if mavutil.mavlink is None:
        raise RuntimeError("pymavlink dialect is not loaded.")

    preflight.ensure_vehicle_type(
        summary(vehicle_type=mavutil.mavlink.MAV_TYPE_GROUND_ROVER),
        telemetry.ExpectedVehicle.ROVER,
    )


def test_ensure_vehicle_type_exits_on_unexpected_vehicle() -> None:
    """Vehicle type validation should fail when SITL runs a different vehicle."""
    if mavutil.mavlink is None:
        raise RuntimeError("pymavlink dialect is not loaded.")

    with pytest.raises(typer.Exit) as error:
        preflight.ensure_vehicle_type(
            summary(vehicle_type=mavutil.mavlink.MAV_TYPE_GROUND_ROVER),
            telemetry.ExpectedVehicle.FIXED_WING,
        )

    assert error.value.exit_code == 1


def test_ensure_ardupilot_accepts_ardupilot_heartbeat() -> None:
    """Autopilot validation should accept ArduPilot heartbeats."""
    if mavutil.mavlink is None:
        raise RuntimeError("pymavlink dialect is not loaded.")

    preflight.ensure_ardupilot(
        summary(autopilot=mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA),
    )


def test_ensure_ardupilot_exits_on_unexpected_autopilot() -> None:
    """Autopilot validation should fail when the heartbeat is not from ArduPilot."""
    with pytest.raises(typer.Exit) as error:
        preflight.ensure_ardupilot(summary(autopilot=0))

    assert error.value.exit_code == 1


def test_ensure_position_available_accepts_complete_position() -> None:
    """Position validation should pass when all basic position fields are present."""
    preflight.ensure_position_available(summary())


def test_ensure_position_available_exits_on_missing_position() -> None:
    """Position validation should fail when strict position telemetry is required but missing."""
    with pytest.raises(typer.Exit) as error:
        preflight.ensure_position_available(summary(longitude_deg=None))

    assert error.value.exit_code == 1


def test_ensure_battery_available_accepts_complete_battery() -> None:
    """Battery validation should pass when all basic battery fields are present."""
    preflight.ensure_battery_available(summary(battery_current_a=0.0, battery_remaining_percent=0))


def test_ensure_battery_available_exits_on_missing_battery() -> None:
    """Battery validation should fail when strict battery telemetry is required but missing."""
    with pytest.raises(typer.Exit) as error:
        preflight.ensure_battery_available(summary(battery_current_a=None))

    assert error.value.exit_code == 1
