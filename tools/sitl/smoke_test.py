#!/usr/bin/env python3
"""Observation-only SITL smoke test."""

from __future__ import annotations

import pathlib
import time
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Annotated, Protocol

import orjson
import typer
from pymavlink import mavutil

if TYPE_CHECKING:
    from pymavlink.mavutil import mavserial

DEFAULT_CONNECT = "udp:127.0.0.1:14550"
DEFAULT_OUTPUT = pathlib.Path("artifacts/sitl/smoke.json")

if mavutil.mavlink is None:
    raise RuntimeError("pymavlink dialect is not loaded.")

mavlink = mavutil.mavlink


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
    latitude_deg: float | None
    longitude_deg: float | None
    relative_altitude_m: float | None


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


def decode_heartbeat(
    connection: mavserial, heartbeat: HeartbeatLike, *, position: GlobalPosition, heartbeat_wait_s: float = 0
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
    )


def create_artifact(summary: HeartbeatSummary) -> dict[str, object]:
    """Create the JSON-serializable smoke-test artifact."""
    return {
        "schema_version": 1,
        "source": "sitl-smoke-test",
        "connected": True,
        "commanded_actions": [],
        "heartbeat": asdict(summary),
    }


def write_artifact(artifact: dict[str, object], output: pathlib.Path) -> None:
    """Write the smoke-test artifact as pretty JSON."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(orjson.dumps(artifact, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS) + b"\n")


def ensure_unarmed(summary: HeartbeatSummary) -> None:
    """Abort the smoke test if the vehicle starts armed."""
    if summary.armed:
        typer.echo("Smoke test expected the vehicle to start unarmed.", err=True)
        raise typer.Exit(1)


def ensure_fixed_wing(summary: HeartbeatSummary) -> None:
    """Abort the smoke test if the vehicle is not a fixed-wing aircraft."""
    if summary.vehicle_type != mavlink.MAV_TYPE_FIXED_WING:
        typer.echo("Smoke test expected a fixed-wing aircraft.", err=True)
        raise typer.Exit(1)


def run_smoke_test(connect: str, timeout: float, output: pathlib.Path) -> HeartbeatSummary:
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
        heartbeat_wait_s=heartbeat_wait_s,
    )
    ensure_unarmed(summary)
    ensure_fixed_wing(summary)

    artifact = create_artifact(summary)
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
) -> None:
    """Connect to SITL, observe one heartbeat, and print the safe baseline state."""
    summary = run_smoke_test(connect, timeout, output)

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
