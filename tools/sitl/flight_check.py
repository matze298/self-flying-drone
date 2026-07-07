#!/usr/bin/env python3
"""SITL flight check."""

import pathlib
import time
from typing import Annotated

import typer
from pymavlink import mavutil

from tools.sitl import preflight
from tools.sitl.artifacts import create_flight_check_artifact, write_artifact
from tools.sitl.telemetry import (
    DEFAULT_CONNECT,
    BatteryStatus,
    ExpectedVehicle,
    GlobalPosition,
    HeartbeatSummary,
    decode_heartbeat,
    utc_now,
)

DEFAULT_OUTPUT = pathlib.Path("artifacts/sitl/flight-check.json")


def ensure_command_opt_in(*, command_opt_in: bool) -> None:
    """Ensure that user verifies flight execution commands."""
    if not command_opt_in:
        typer.echo("Flight check requires --i-understand-this-sends-commands.", err=True)
        raise typer.Exit(1)


def capture_preflight_summary(connect: str, timeout: float) -> HeartbeatSummary:
    """Capture the pre-flight summary."""
    connection = mavutil.mavlink_connection(connect)
    start_time = time.monotonic()
    heartbeat = connection.wait_heartbeat(timeout=timeout)

    if heartbeat is None:
        typer.echo(f"No heartbeat received from {connect} within {timeout:g}s.", err=True)
        raise typer.Exit(1)

    heartbeat_wait_s = round(time.monotonic() - start_time, 3)

    return decode_heartbeat(
        connection,
        heartbeat,
        position=GlobalPosition.from_message(connection, timeout=timeout),
        battery_status=BatteryStatus.from_message(connection, timeout=timeout),
        heartbeat_wait_s=heartbeat_wait_s,
        captured_at=utc_now(),
    )


def run_command_plan(connection: object, summary: HeartbeatSummary) -> list[dict[str, object]]:  # noqa: ARG001
    """Runs a list of commands."""
    return []


def run_flight_check(connect: str, timeout: float, output: pathlib.Path, *, command_opt_in: bool) -> HeartbeatSummary:
    """Execute the flight check."""
    ensure_command_opt_in(command_opt_in=command_opt_in)
    preflight_summary = capture_preflight_summary(connect, timeout)
    preflight.run_strict_preflight(preflight_summary, expected_vehicle=ExpectedVehicle.FIXED_WING)
    commanded_actions = run_command_plan(None, preflight_summary)

    artifact: dict[str, object] = create_flight_check_artifact(
        preflight_summary, commanded_actions=commanded_actions, status="ok"
    )
    write_artifact(artifact, output)

    return preflight_summary


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
    command_opt_in: Annotated[
        bool,
        typer.Option(
            "--i-understand-this-sends-commands/--no-i-understand-this-sends-commands",
        ),
    ] = False,
) -> None:
    """Connect to SITL, observe one heartbeat, and print the safe baseline state."""
    summary = run_flight_check(connect, timeout, output, command_opt_in=command_opt_in)

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
