"""Tests for reusable SITL telemetry helpers."""

from __future__ import annotations

from types import SimpleNamespace

from pymavlink import mavutil

from tools.sitl import telemetry

EXPECTED_CAPTURED_AT = "2026-07-06T12:34:56Z"
EXPECTED_HEARTBEAT_WAIT_S = 0.123
EXPECTED_LATITUDE_DEG = 47.397742
EXPECTED_LONGITUDE_DEG = 8.545594
EXPECTED_RELATIVE_ALTITUDE_M = 12.3
EXPECTED_BATTERY_VOLTAGE_V = 12.6
EXPECTED_BATTERY_CURRENT_A = 1.23
EXPECTED_BATTERY_REMAINING_PERCENT = 98


def test_decode_heartbeat_reports_manual_unarmed() -> None:
    """Heartbeat decoding should expose the safe baseline state."""
    if mavutil.mavlink is None:
        raise RuntimeError("pymavlink dialect is not loaded.")

    mavlink = mavutil.mavlink
    connection = SimpleNamespace(target_system=1, target_component=0)
    heartbeat = mavlink.MAVLink_heartbeat_message(
        type=mavlink.MAV_TYPE_FIXED_WING,
        autopilot=mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA,
        base_mode=81,
        custom_mode=0,
        system_status=mavlink.MAV_STATE_STANDBY,
        mavlink_version=3,
    )

    summary = telemetry.decode_heartbeat(
        connection,
        heartbeat,
        position=telemetry.GlobalPosition(
            lat=EXPECTED_LATITUDE_DEG,
            lon=EXPECTED_LONGITUDE_DEG,
            relative_alt=EXPECTED_RELATIVE_ALTITUDE_M,
        ),
        battery_status=telemetry.BatteryStatus(
            voltage_v=EXPECTED_BATTERY_VOLTAGE_V,
            current_a=EXPECTED_BATTERY_CURRENT_A,
            remaining_percent=EXPECTED_BATTERY_REMAINING_PERCENT,
        ),
        heartbeat_wait_s=EXPECTED_HEARTBEAT_WAIT_S,
        captured_at=EXPECTED_CAPTURED_AT,
    )

    assert summary.system_id == 1
    assert summary.component_id == 0
    assert summary.mode == "MANUAL"
    assert summary.armed is False
    assert summary.vehicle_type == mavlink.MAV_TYPE_FIXED_WING
    assert summary.autopilot == mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA
    assert summary.latitude_deg == EXPECTED_LATITUDE_DEG
    assert summary.longitude_deg == EXPECTED_LONGITUDE_DEG
    assert summary.relative_altitude_m == EXPECTED_RELATIVE_ALTITUDE_M
    assert summary.battery_voltage_v == EXPECTED_BATTERY_VOLTAGE_V
    assert summary.battery_current_a == EXPECTED_BATTERY_CURRENT_A
    assert summary.battery_remaining_percent == EXPECTED_BATTERY_REMAINING_PERCENT
