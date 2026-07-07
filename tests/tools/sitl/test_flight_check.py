"""Tests for the command-sending SITL flight check."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
import typer
from pymavlink import mavutil

from tools.sitl import flight_check, telemetry

if TYPE_CHECKING:
    import pathlib


def safe_summary() -> telemetry.HeartbeatSummary:
    """Build a preflight-safe heartbeat summary for flight-check tests."""
    if mavutil.mavlink is None:
        raise RuntimeError("pymavlink dialect is not loaded.")

    return telemetry.HeartbeatSummary(
        system_id=1,
        component_id=0,
        mode="MANUAL",
        armed=False,
        custom_mode=0,
        vehicle_type=mavutil.mavlink.MAV_TYPE_FIXED_WING,
        autopilot=mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA,
        heartbeat_wait_s=0.123,
        captured_at="2026-07-06T12:34:56Z",
        latitude_deg=47.397742,
        longitude_deg=8.545594,
        relative_altitude_m=12.3,
        battery_voltage_v=12.6,
        battery_current_a=0.0,
        battery_remaining_percent=100,
    )


def test_run_flight_check_refuses_missing_command_opt_in(tmp_path: pathlib.Path) -> None:
    """The flight check should refuse to run without explicit command opt-in."""
    with pytest.raises(typer.Exit) as error:
        flight_check.run_flight_check(
            "udp:127.0.0.1:14550",
            1.0,
            tmp_path / "flight.json",
            command_opt_in=False,
        )

    assert error.value.exit_code == 1


def test_run_flight_check_runs_preflight_before_commands(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    """Strict preflight should run before any command plan execution."""
    events: list[str] = []

    monkeypatch.setattr(flight_check, "capture_preflight_summary", lambda *_args, **_kwargs: safe_summary())
    monkeypatch.setattr(
        flight_check.preflight, "run_strict_preflight", lambda *_args, **_kwargs: events.append("preflight")
    )
    monkeypatch.setattr(flight_check, "run_command_plan", lambda *_args, **_kwargs: events.append("commands") or [])

    flight_check.run_flight_check(
        "udp:127.0.0.1:14550",
        1.0,
        tmp_path / "flight.json",
        command_opt_in=True,
    )

    assert events == ["preflight", "commands"]


def test_run_flight_check_writes_expected_artifact(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    """The flight-check safety shell should write the expected artifact contract."""
    commanded_actions = [
        {"action": "set_mode", "requested": "FBWA", "result": "accepted"},
        {"action": "arm", "result": "accepted"},
    ]

    monkeypatch.setattr(flight_check, "capture_preflight_summary", lambda *_args, **_kwargs: safe_summary())
    monkeypatch.setattr(flight_check.preflight, "run_strict_preflight", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(flight_check, "run_command_plan", lambda *_args, **_kwargs: commanded_actions)

    output = tmp_path / "flight.json"
    flight_check.run_flight_check(
        "udp:127.0.0.1:14550",
        1.0,
        output,
        command_opt_in=True,
    )

    artifact = json.loads(output.read_text(encoding="utf-8"))

    assert artifact["source"] == "sitl-flight-check"
    assert artifact["required_checks"].count("explicit-command-opt-in") == 1
    assert artifact["commanded_actions"] == commanded_actions
    assert artifact["final_state"] is None
