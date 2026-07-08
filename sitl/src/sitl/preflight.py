"""Reusable SITL preflight checks."""

from __future__ import annotations

import typer
from pymavlink import mavutil

from sitl.telemetry import ExpectedVehicle, HeartbeatSummary

if mavutil.mavlink is None:
    raise RuntimeError("pymavlink dialect is not loaded.")

mavlink = mavutil.mavlink


def ensure_unarmed(summary: HeartbeatSummary) -> None:
    """Abort when the vehicle starts armed."""
    if summary.armed:
        typer.echo("Smoke test expected the vehicle to start unarmed.", err=True)
        raise typer.Exit(1)


def ensure_vehicle_type(summary: HeartbeatSummary, expected_vehicle: ExpectedVehicle) -> None:
    """Abort when the observed vehicle type differs from the expected one."""
    expected_vehicle_types = {
        ExpectedVehicle.FIXED_WING: mavlink.MAV_TYPE_FIXED_WING,
        ExpectedVehicle.COPTER: mavlink.MAV_TYPE_QUADROTOR,
        ExpectedVehicle.ROVER: mavlink.MAV_TYPE_GROUND_ROVER,
        ExpectedVehicle.HELICOPTER: mavlink.MAV_TYPE_HELICOPTER,
    }

    if summary.vehicle_type != expected_vehicle_types[expected_vehicle]:
        typer.echo(f"Smoke test expected a {expected_vehicle} aircraft, but got a {summary.vehicle_type}.", err=True)
        raise typer.Exit(1)


def ensure_ardupilot(summary: HeartbeatSummary) -> None:
    """Abort when the heartbeat is not from ArduPilot."""
    if summary.autopilot != mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA:
        typer.echo(f"Smoke test expected ArduPilot autopilot, but got {summary.autopilot}.", err=True)
        raise typer.Exit(1)


def ensure_position_available(summary: HeartbeatSummary) -> None:
    """Abort when required position telemetry is incomplete."""
    if summary.latitude_deg is None or summary.longitude_deg is None or summary.relative_altitude_m is None:
        typer.echo("Smoke test expected position telemetry.", err=True)
        raise typer.Exit(1)


def ensure_battery_available(summary: HeartbeatSummary) -> None:
    """Abort when required battery telemetry is incomplete."""
    if (
        summary.battery_voltage_v is None
        or summary.battery_current_a is None
        or summary.battery_remaining_percent is None
    ):
        typer.echo("Smoke test expected battery telemetry.", err=True)
        raise typer.Exit(1)


def run_strict_preflight(summary: HeartbeatSummary, *, expected_vehicle: ExpectedVehicle) -> None:
    """Run the strict safety baseline used before any command-sending workflow."""
    ensure_unarmed(summary)
    ensure_vehicle_type(summary, expected_vehicle=expected_vehicle)
    ensure_ardupilot(summary)
    ensure_position_available(summary)
    ensure_battery_available(summary)
