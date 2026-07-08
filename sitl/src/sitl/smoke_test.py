#!/usr/bin/env python3
"""Observation-only SITL smoke test."""

from __future__ import annotations

import pathlib  # noqa: TC003 - required by typer
import time
from typing import Annotated

import typer

from sitl.artifacts import (
    DEFAULT_OUTPUT,
    build_required_checks,
    create_smoke_artifact,
    write_artifact,
)
from sitl.preflight import (
    ensure_ardupilot,
    ensure_battery_available,
    ensure_position_available,
    ensure_unarmed,
    ensure_vehicle_type,
)
from sitl.telemetry import (
    DEFAULT_CONNECT,
    BatteryStatus,
    ExpectedVehicle,
    GlobalPosition,
    HeartbeatSummary,
    decode_heartbeat,
    get_mav_connection,
    utc_now,
)

BASE_REQUIRED_CHECKS = ("unarmed", "vehicle")
DEFAULT_REQUIRED_CHECKS = (*BASE_REQUIRED_CHECKS, "ardupilot", "position", "battery")


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
    connection = get_mav_connection(connect)
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

    artifact = create_smoke_artifact(
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
            help="MAVLink endpoint exposed by sitl-run.",
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


app = typer.Typer()
app.command()(main)


if __name__ == "__main__":
    app()
