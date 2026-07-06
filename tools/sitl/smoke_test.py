#!/usr/bin/env python3
"""Observation-only SITL smoke test."""

from __future__ import annotations

import pathlib
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Protocol

import orjson
import typer
from pymavlink import mavutil

if TYPE_CHECKING:
    from pymavlink.mavutil import mavserial

DEFAULT_CONNECT = "udp:127.0.0.1:14550"
DEFAULT_OUTPUT = pathlib.Path("artifacts/sitl/smoke.json")
BASE_REQUIRED_CHECKS = ("unarmed", "vehicle")
DEFAULT_REQUIRED_CHECKS = (*BASE_REQUIRED_CHECKS, "ardupilot", "position", "battery")

if mavutil.mavlink is None:
    raise RuntimeError("pymavlink dialect is not loaded.")

mavlink = mavutil.mavlink


def utc_now() -> str:
    """Returns the current UTC time as a string."""
    return datetime.now(tz=UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


class ExpectedVehicle(StrEnum):
    """Vehicle types supported by the smoke-test expectation."""

    FIXED_WING = "fixed-wing"
    COPTER = "copter"
    ROVER = "rover"
    HELICOPTER = "helicopter"


@dataclass(frozen=True)
class HeartbeatSummary:
    """Decoded heartbeat fields for the smoke test."""

    system_id: int
    component_id: int
    mode: str
    armed: bool
    custom_mode: int
    vehicle_type: int
    autopilot: int
    heartbeat_wait_s: float
    captured_at: str
    latitude_deg: float | None
    longitude_deg: float | None
    relative_altitude_m: float | None
    battery_voltage_v: float | None
    battery_current_a: float | None
    battery_remaining_percent: int | None


class HeartbeatLike(Protocol):
    """MAVLink heartbeat fields used by the smoke test."""

    base_mode: int
    custom_mode: int
    type: int
    autopilot: int


@dataclass
class GlobalPosition:
    """Scale GLOBAL_POSITION_INT fields into human units."""

    lat: float | None
    lon: float | None
    relative_alt: float | None

    @staticmethod
    def from_message(connection: mavserial, timeout: float = 5.0) -> GlobalPosition:
        """Initialize GlobalPosition from a mavserial connection using GLOBAL_POSITION_INT."""
        message = connection.recv_match(type="GLOBAL_POSITION_INT", blocking=True, timeout=timeout)

        if message is None:
            return GlobalPosition(None, None, None)

        latitude = getattr(message, "lat", None)
        longitude = getattr(message, "lon", None)
        relative_altitude = getattr(message, "relative_alt", None)

        return GlobalPosition(
            latitude / 1e7 if latitude is not None else None,
            longitude / 1e7 if longitude is not None else None,
            relative_altitude / 1000 if relative_altitude is not None else None,
        )


@dataclass(frozen=True)
class BatteryStatus:
    """Decoded BATTERY_STATUS fields for the smoke test."""

    voltage_v: float | None
    current_a: float | None
    remaining_percent: int | None

    @staticmethod
    def from_message(connection: mavserial, timeout: float = 5.0) -> BatteryStatus:
        """Initialize BatteryStatus from a mavserial connection using BATTERY_STATUS."""
        message = connection.recv_match(type="BATTERY_STATUS", blocking=True, timeout=timeout)

        if message is None:
            return BatteryStatus(None, None, None)

        voltages = getattr(message, "voltages", None)
        current_battery = getattr(message, "current_battery", None)
        battery_remaining = getattr(message, "battery_remaining", None)

        return BatteryStatus(
            voltage_v=voltages[0] / 1000 if voltages and voltages[0] != 2**16 - 1 else None,
            current_a=current_battery / 100 if current_battery is not None and current_battery != -1 else None,
            remaining_percent=battery_remaining if battery_remaining is not None and battery_remaining != -1 else None,
        )


def decode_heartbeat(
    connection: mavserial,
    heartbeat: HeartbeatLike,
    *,
    position: GlobalPosition,
    battery_status: BatteryStatus,
    captured_at: str,
    heartbeat_wait_s: float = 0,
) -> HeartbeatSummary:
    """Decode the heartbeat fields we care about without sending commands."""
    armed = bool(heartbeat.base_mode & mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
    mode = mavutil.mode_string_v10(heartbeat)
    return HeartbeatSummary(
        system_id=connection.target_system,
        component_id=connection.target_component,
        mode=mode,
        armed=armed,
        custom_mode=heartbeat.custom_mode,
        vehicle_type=heartbeat.type,
        autopilot=heartbeat.autopilot,
        heartbeat_wait_s=heartbeat_wait_s,
        latitude_deg=position.lat,
        longitude_deg=position.lon,
        relative_altitude_m=position.relative_alt,
        captured_at=captured_at,
        battery_voltage_v=battery_status.voltage_v,
        battery_current_a=battery_status.current_a,
        battery_remaining_percent=battery_status.remaining_percent,
    )


def create_artifact(summary: HeartbeatSummary, *, required_checks: list[str] | None = None) -> dict[str, object]:
    """Create the JSON-serializable smoke-test artifact."""
    return {
        "schema_version": 1,
        "source": "sitl-smoke-test",
        "connected": True,
        "commanded_actions": [],
        "required_checks": required_checks if required_checks is not None else list(DEFAULT_REQUIRED_CHECKS),
        "captured_at": summary.captured_at,
        "heartbeat": asdict(summary),
    }


def build_required_checks(*, require_ardupilot: bool, require_position: bool, require_battery: bool) -> list[str]:
    """Return the checks enforced for this smoke-test run."""
    required_checks = list(BASE_REQUIRED_CHECKS)
    if require_ardupilot:
        required_checks.append("ardupilot")
    if require_position:
        required_checks.append("position")
    if require_battery:
        required_checks.append("battery")
    return required_checks


def write_artifact(artifact: dict[str, object], output: pathlib.Path) -> None:
    """Write the smoke-test artifact as pretty JSON."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(orjson.dumps(artifact, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS) + b"\n")


def ensure_unarmed(summary: HeartbeatSummary) -> None:
    """Abort the smoke test if the vehicle starts armed."""
    if summary.armed:
        typer.echo("Smoke test expected the vehicle to start unarmed.", err=True)
        raise typer.Exit(1)


def ensure_vehicle_type(summary: HeartbeatSummary, expected_vehicle: ExpectedVehicle) -> None:
    """Abort the smoke test if the vehicle type does not match the expectation."""
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
    """Abort the smoke test if the heartbeat is not from ArduPilot."""
    if summary.autopilot != mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA:
        typer.echo(f"Smoke test expected ArduPilot autopilot, but got {summary.autopilot}.", err=True)
        raise typer.Exit(1)


def ensure_position_available(summary: HeartbeatSummary) -> None:
    """Abort the smoke test if required position telemetry is incomplete."""
    if summary.latitude_deg is None or summary.longitude_deg is None or summary.relative_altitude_m is None:
        typer.echo("Smoke test expected position telemetry.", err=True)
        raise typer.Exit(1)


def ensure_battery_available(summary: HeartbeatSummary) -> None:
    """Abort the smoke test if required battery telemetry is incomplete."""
    if (
        summary.battery_voltage_v is None
        or summary.battery_current_a is None
        or summary.battery_remaining_percent is None
    ):
        typer.echo("Smoke test expected battery telemetry.", err=True)
        raise typer.Exit(1)


def run_smoke_test(
    connect: str,
    timeout: float,
    output: pathlib.Path,
    expected_vehicle: ExpectedVehicle = ExpectedVehicle.FIXED_WING,
    *,
    require_ardupilot: bool = True,
    require_position: bool = True,
    require_battery: bool = True,
) -> HeartbeatSummary:
    """Execute the smoke test."""
    connection = mavutil.mavlink_connection(connect)
    start_time = time.monotonic()
    heartbeat = connection.wait_heartbeat(timeout=timeout)

    if heartbeat is None:
        typer.echo(f"No heartbeat received from {connect} within {timeout:g}s.", err=True)
        raise typer.Exit(1)

    heartbeat_wait_s = round(time.monotonic() - start_time, 3)
    summary = decode_heartbeat(
        connection,
        heartbeat,
        position=GlobalPosition.from_message(connection, timeout=timeout),
        battery_status=BatteryStatus.from_message(connection, timeout=timeout),
        heartbeat_wait_s=heartbeat_wait_s,
        captured_at=utc_now(),
    )
    ensure_unarmed(summary)
    ensure_vehicle_type(summary, expected_vehicle=expected_vehicle)
    if require_ardupilot:
        ensure_ardupilot(summary)
    if require_position:
        ensure_position_available(summary)
    if require_battery:
        ensure_battery_available(summary)

    artifact = create_artifact(
        summary,
        required_checks=build_required_checks(
            require_ardupilot=require_ardupilot,
            require_position=require_position,
            require_battery=require_battery,
        ),
    )
    write_artifact(artifact, output)

    return summary


def main(
    connect: Annotated[
        str,
        typer.Option(
            "--connect",
            "-c",
            help="MAVLink endpoint exposed by tools/sitl/run.py.",
        ),
    ] = DEFAULT_CONNECT,
    timeout: Annotated[
        float,
        typer.Option(
            "--timeout",
            help="Heartbeat wait timeout in seconds.",
            min=1.0,
        ),
    ] = 10.0,
    output: Annotated[
        pathlib.Path,
        typer.Option(
            "--output",
            "-o",
            help="Path for the JSON smoke-test artifact.",
        ),
    ] = DEFAULT_OUTPUT,
    *,
    expected_vehicle: Annotated[
        ExpectedVehicle,
        typer.Option(
            "--expected-vehicle",
            help="Vehicle type expected in the heartbeat.",
        ),
    ] = ExpectedVehicle.FIXED_WING,
    require_position: Annotated[
        bool,
        typer.Option(
            "--require-position/--no-require-position",
            help="Fail when latitude, longitude, or relative altitude telemetry is missing.",
        ),
    ] = True,
    require_battery: Annotated[
        bool,
        typer.Option(
            "--require-battery/--no-require-battery",
            help="Fail when voltage, current, or remaining battery telemetry is missing.",
        ),
    ] = True,
    require_ardupilot: Annotated[
        bool,
        typer.Option(
            "--require-ardupilot/--no-require-ardupilot",
            help="Fail when the heartbeat is not from ArduPilot.",
        ),
    ] = True,
) -> None:
    """Connect to SITL, observe one heartbeat, and print the safe baseline state."""
    summary = run_smoke_test(
        connect,
        timeout,
        output,
        expected_vehicle=expected_vehicle,
        require_ardupilot=require_ardupilot,
        require_position=require_position,
        require_battery=require_battery,
    )

    typer.echo("connected: True")
    typer.echo(f"heartbeat_wait_s: {summary.heartbeat_wait_s}")
    typer.echo(f"latitude_deg: {summary.latitude_deg}")
    typer.echo(f"longitude_deg: {summary.longitude_deg}")
    typer.echo(f"relative_altitude_m: {summary.relative_altitude_m}")
    typer.echo(f"system_id: {summary.system_id}")
    typer.echo(f"component_id: {summary.component_id}")
    typer.echo(f"mode: {summary.mode}")
    typer.echo(f"armed: {summary.armed}")
    typer.echo(f"custom_mode: {summary.custom_mode}")
    typer.echo(f"vehicle_type: {summary.vehicle_type}")
    typer.echo(f"autopilot: {summary.autopilot}")
    typer.echo(f"output: {output}")


if __name__ == "__main__":
    typer.run(main)
