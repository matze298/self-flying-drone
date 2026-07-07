#!/usr/bin/env python3
"""SITL flight check."""

import pathlib
import time
from typing import TYPE_CHECKING, Annotated

import typer

from tools.sitl import preflight
from tools.sitl.artifacts import create_flight_check_artifact, write_artifact
from tools.sitl.telemetry import (
    DEFAULT_CONNECT,
    BatteryStatus,
    ExpectedVehicle,
    GlobalPosition,
    HeartbeatSummary,
    decode_heartbeat,
    get_mav_connection,
    utc_now,
    verified_mavlink,
)

if TYPE_CHECKING:
    from pymavlink.mavutil import mavfile

DEFAULT_OUTPUT = pathlib.Path("artifacts/sitl/flight-check.json")

TAKEOFF_MODE = "TAKEOFF"
RTL_MODE = "RTL"

type CommandAction = dict[str, object]


def _accepted(action: str, **fields: object) -> CommandAction:
    """Create an accepted command action."""
    return {"action": action, **fields, "result": "accepted"}


def _sent(action: str, **fields: object) -> CommandAction:
    """Create a sent command action."""
    return {"action": action, **fields, "result": "sent"}


def _rejected(action: str, reason: str, **fields: object) -> CommandAction:
    """Create a rejected command action."""
    return {"action": action, **fields, "result": "rejected", "reason": reason}


def ensure_command_opt_in(*, command_opt_in: bool) -> None:
    """Ensure that user verifies flight execution commands."""
    if not command_opt_in:
        typer.echo("Flight check requires --i-understand-this-sends-commands.", err=True)
        raise typer.Exit(1)


def capture_preflight_summary(connection: mavfile, timeout: float) -> HeartbeatSummary:
    """Capture the pre-flight summary."""
    start_time = time.monotonic()
    heartbeat = connection.wait_heartbeat(timeout=timeout)

    if heartbeat is None:
        typer.echo(f"No heartbeat received from {connection} within {timeout:g}s.", err=True)
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


def _observe_takeoff_progress(
    connection: mavfile,
    *,
    baseline_relative_altitude_m: float | None,
    required_gain_m: float,
    sample_timeout_s: float,
    timeout_s: float,
) -> CommandAction:
    """Observe relative-altitude gain after the takeoff command."""
    if baseline_relative_altitude_m is None:
        return _rejected("observe_progress", "missing-baseline-altitude")

    if timeout_s <= 0:
        return _rejected("observe_progress", "progress-timeout")

    deadline = time.monotonic() + timeout_s
    while time.monotonic() <= deadline:
        remaining_s = max(0.0, deadline - time.monotonic())
        sample_timeout = min(sample_timeout_s, remaining_s)
        position = GlobalPosition.from_message(connection, timeout=sample_timeout)
        if position.relative_alt is None:
            continue

        altitude_gain_m = round(position.relative_alt - baseline_relative_altitude_m, 3)
        if altitude_gain_m >= required_gain_m:
            return _accepted("observe_progress", relative_altitude_gain_m=altitude_gain_m)

    return _rejected("observe_progress", "progress-timeout")


def _set_mode_action(connection: mavfile, mode: str) -> CommandAction:
    """Set an ArduPilot mode and record the result."""
    modes: dict[str, int | None] = connection.mode_mapping()
    mode_id = modes.get(mode)
    if mode_id is None:
        return _rejected("set_mode", "mode-unavailable", requested=mode)

    try:
        connection.set_mode(mode_id)
    except:  # noqa: E722 - pymavlink command helpers can raise transport-specific exceptions.
        return _rejected("set_mode", "command-failed", requested=mode)

    return _accepted("set_mode", requested=mode)


def _arm_action(connection: mavfile) -> CommandAction:
    """Arm the vehicle and wait until ArduPilot reports motors armed."""
    try:
        connection.arducopter_arm()
        connection.motors_armed_wait()
    except:  # noqa: E722 - pymavlink command helpers can raise transport-specific exceptions.
        return _rejected("arm", "command-failed")

    return _accepted("arm")


def _takeoff_action(connection: mavfile, *, altitude_m: float) -> CommandAction:
    """Send the MAVLink takeoff command and record the result."""
    try:
        connection.mav.command_long_send(
            connection.target_system,
            connection.target_component,
            verified_mavlink.MAV_CMD_NAV_TAKEOFF,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            altitude_m,
        )
    except:  # noqa: E722 - pymavlink command helpers can raise transport-specific exceptions.
        return _rejected("takeoff", reason="command-failed", altitude_m=altitude_m)

    return _sent("takeoff", altitude_m=altitude_m)


def run_command_plan(
    connection: mavfile,
    summary: HeartbeatSummary,
    *,
    takeoff_altitude_m: float = 30,
    end_mode: str = RTL_MODE,
    progress_required_gain_m: float = 5.0,
    progress_timeout_s: float = 20.0,
    progress_sample_timeout_s: float = 1.0,
) -> list[CommandAction]:
    """Runs a list of commands."""
    actions: list[CommandAction] = []

    set_mode_action = _set_mode_action(connection, TAKEOFF_MODE)
    actions.append(set_mode_action)
    if set_mode_action["result"] == "rejected":
        return actions

    arm_action = _arm_action(connection)
    actions.append(arm_action)
    if arm_action["result"] == "rejected":
        return actions

    takeoff_action = _takeoff_action(connection, altitude_m=takeoff_altitude_m)
    actions.append(takeoff_action)
    if takeoff_action["result"] == "rejected":
        return actions

    progress_action = _observe_takeoff_progress(
        connection,
        baseline_relative_altitude_m=summary.relative_altitude_m,
        required_gain_m=progress_required_gain_m,
        timeout_s=progress_timeout_s,
        sample_timeout_s=progress_sample_timeout_s,
    )
    actions.append(progress_action)
    if progress_action["result"] == "rejected":
        return actions

    actions.append(_set_mode_action(connection, end_mode))
    return actions


def final_state_matches_end_mode(final_state: HeartbeatSummary | None, *, end_mode: str) -> bool:
    """Return whether the observed final state matches the requested end mode."""
    return final_state is not None and final_state.mode == end_mode


def run_flight_check(
    connect: str,
    timeout: float,
    output: pathlib.Path,
    *,
    command_opt_in: bool,
    takeoff_altitude_m: float = 30,
    end_mode: str = RTL_MODE,
    progress_required_gain_m: float = 5.0,
    progress_timeout_s: float = 20.0,
    progress_sample_timeout_s: float = 1.0,
) -> HeartbeatSummary:
    """Execute the flight check."""
    ensure_command_opt_in(command_opt_in=command_opt_in)

    connection = get_mav_connection(connect)
    preflight_summary = capture_preflight_summary(connection, timeout)
    preflight.run_strict_preflight(preflight_summary, expected_vehicle=ExpectedVehicle.FIXED_WING)

    commanded_actions = run_command_plan(
        connection,
        preflight_summary,
        takeoff_altitude_m=takeoff_altitude_m,
        end_mode=end_mode,
        progress_required_gain_m=progress_required_gain_m,
        progress_timeout_s=progress_timeout_s,
        progress_sample_timeout_s=progress_sample_timeout_s,
    )

    rejected = any(a["result"] == "rejected" for a in commanded_actions)
    status = "failed" if rejected else "ok"
    try:
        final_state = None if rejected else capture_preflight_summary(connection, timeout)
    except typer.Exit:
        final_state = None
        status = "failed"
    if status == "ok" and not final_state_matches_end_mode(final_state, end_mode=end_mode):
        status = "failed"

    artifact = create_flight_check_artifact(
        preflight_summary,
        commanded_actions=commanded_actions,
        status=status,
        final_state=final_state,
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
    takeoff_altitude_m: Annotated[
        float,
        typer.Option(
            "--takeoff-altitude",
            help="Target altitude in meters for MAV_CMD_NAV_TAKEOFF.",
            min=1.0,
        ),
    ] = 30,
    end_mode: Annotated[
        str,
        typer.Option(
            "--end-mode",
            help="ArduPilot mode requested after takeoff progress is observed.",
        ),
    ] = RTL_MODE,
    progress_required_gain_m: Annotated[
        float,
        typer.Option(
            "--progress-gain",
            help="Required relative-altitude gain in meters after takeoff.",
            min=0.1,
        ),
    ] = 5.0,
    progress_timeout_s: Annotated[
        float,
        typer.Option(
            "--progress-timeout",
            help="Maximum seconds to wait for takeoff progress.",
            min=0.0,
        ),
    ] = 20.0,
    progress_sample_timeout_s: Annotated[
        float,
        typer.Option(
            "--progress-sample-timeout",
            help="Seconds to wait for each progress telemetry sample.",
            min=0.0,
        ),
    ] = 1.0,
) -> None:
    """Connect to SITL, observe one heartbeat, and print the safe baseline state."""
    summary = run_flight_check(
        connect,
        timeout,
        output,
        command_opt_in=command_opt_in,
        takeoff_altitude_m=takeoff_altitude_m,
        end_mode=end_mode,
        progress_required_gain_m=progress_required_gain_m,
        progress_timeout_s=progress_timeout_s,
        progress_sample_timeout_s=progress_sample_timeout_s,
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
