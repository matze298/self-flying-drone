"""Tests for the command-sending SITL flight check."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast

import pytest
import typer
from pymavlink import mavutil

from tools.sitl import flight_check, telemetry

if TYPE_CHECKING:
    import pathlib


class FakeMav:
    """Capture MAVLink command calls without requiring a simulator."""

    def __init__(self, *, fail_takeoff: bool = False) -> None:
        """Initialize an empty MAVLink command call log."""
        self.command_long_calls: list[tuple[object, ...]] = []
        self.fail_takeoff = fail_takeoff

    def command_long_send(self, *args: object) -> None:
        """Record command_long_send arguments."""
        if self.fail_takeoff:
            raise RuntimeError("takeoff command failed")
        self.command_long_calls.append(args)


class FakeCommandConnection:
    """Small fake for the command-plan boundary."""

    target_system = 1
    target_component = 1

    def __init__(
        self,
        *,
        modes: dict[str, int] | None = None,
        fail_arm: bool = False,
        fail_takeoff: bool = False,
    ) -> None:
        """Initialize a fake connection with configurable mode mapping."""
        self.modes = modes if modes is not None else {"TAKEOFF": 13}
        self.mav = FakeMav(fail_takeoff=fail_takeoff)
        self.fail_arm = fail_arm
        self.calls: list[tuple[str, object]] = []

    def mode_mapping(self) -> dict[str, int]:
        """Return available ArduPilot mode names."""
        return self.modes

    def set_mode(self, mode_id: int) -> None:
        """Record mode changes."""
        self.calls.append(("set_mode", mode_id))

    def arducopter_arm(self) -> None:
        """Record the generic pymavlink arm command."""
        if self.fail_arm:
            raise RuntimeError("arm command failed")
        self.calls.append(("arm", True))

    def motors_armed_wait(self) -> None:
        """Record that the plan waited for the armed state."""
        self.calls.append(("wait_armed", True))


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
    connection = FakeCommandConnection()

    monkeypatch.setattr(flight_check, "get_mav_connection", lambda _: connection)
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
    connection = FakeCommandConnection()

    monkeypatch.setattr(flight_check, "get_mav_connection", lambda _: connection)
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
    assert artifact["status"] == "ok"
    assert artifact["required_checks"].count("explicit-command-opt-in") == 1
    assert artifact["commanded_actions"] == commanded_actions
    assert artifact["final_state"] == {
        "armed": False,
        "autopilot": telemetry.verified_mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA,
        "battery_current_a": 0.0,
        "battery_remaining_percent": 100,
        "battery_voltage_v": 12.6,
        "captured_at": "2026-07-06T12:34:56Z",
        "component_id": 0,
        "custom_mode": 0,
        "heartbeat_wait_s": 0.123,
        "latitude_deg": 47.397742,
        "longitude_deg": 8.545594,
        "mode": "MANUAL",
        "relative_altitude_m": 12.3,
        "system_id": 1,
        "vehicle_type": telemetry.verified_mavlink.MAV_TYPE_FIXED_WING,
    }


def test_run_flight_check_marks_artifact_failed_when_command_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    """Rejected command actions should be visible in the flight-check status."""
    commanded_actions = [
        {
            "action": "set_mode",
            "requested": "TAKEOFF",
            "result": "rejected",
            "reason": "mode-unavailable",
        },
    ]
    connection = FakeCommandConnection(modes={})

    monkeypatch.setattr(flight_check, "get_mav_connection", lambda _: connection)
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

    assert artifact["status"] == "failed"
    assert artifact["commanded_actions"] == commanded_actions
    assert artifact["final_state"] is None


def test_run_flight_check_preserves_command_log_when_final_state_capture_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    """Final-state failures should still write a failed artifact with the command log."""
    commanded_actions = [
        {"action": "set_mode", "requested": "TAKEOFF", "result": "accepted"},
        {"action": "arm", "result": "accepted"},
        {"action": "takeoff", "altitude_m": 30, "result": "sent"},
    ]
    connection = FakeCommandConnection()
    captures = 0

    def fake_capture(*_args: object, **_kwargs: object) -> telemetry.HeartbeatSummary:
        nonlocal captures
        captures += 1
        if captures == 1:
            return safe_summary()
        raise typer.Exit(1)

    monkeypatch.setattr(flight_check, "get_mav_connection", lambda _: connection)
    monkeypatch.setattr(flight_check, "capture_preflight_summary", fake_capture)
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

    assert artifact["status"] == "failed"
    assert artifact["commanded_actions"] == commanded_actions
    assert artifact["final_state"] is None


def test_run_command_plan_records_mode_arm_and_takeoff() -> None:
    """The first command plan should record the virtual flight sequence."""
    connection = FakeCommandConnection()

    actions = flight_check.run_command_plan(cast("Any", connection), safe_summary())

    assert actions == [
        {"action": "set_mode", "requested": "TAKEOFF", "result": "accepted"},
        {"action": "arm", "result": "accepted"},
        {"action": "takeoff", "altitude_m": 30, "result": "sent"},
    ]
    assert connection.calls == [("set_mode", 13), ("arm", True), ("wait_armed", True)]
    assert len(connection.mav.command_long_calls) == 1


def test_run_command_plan_stops_after_unavailable_mode() -> None:
    """The command plan should fail closed when the selected Plane mode is unavailable."""
    connection = FakeCommandConnection(modes={})

    actions = flight_check.run_command_plan(cast("Any", connection), safe_summary())

    assert actions == [
        {
            "action": "set_mode",
            "requested": "TAKEOFF",
            "result": "rejected",
            "reason": "mode-unavailable",
        },
    ]
    assert connection.calls == []
    assert connection.mav.command_long_calls == []


def test_run_command_plan_stops_after_arm_failure() -> None:
    """The command plan should record arm failures and skip takeoff."""
    connection = FakeCommandConnection(fail_arm=True)

    actions = flight_check.run_command_plan(cast("Any", connection), safe_summary())

    assert actions == [
        {"action": "set_mode", "requested": "TAKEOFF", "result": "accepted"},
        {"action": "arm", "result": "rejected", "reason": "command-failed"},
    ]
    assert connection.calls == [("set_mode", 13)]
    assert connection.mav.command_long_calls == []


def test_run_command_plan_records_takeoff_failure() -> None:
    """The command plan should record takeoff command failures after arming."""
    connection = FakeCommandConnection(fail_takeoff=True)

    actions = flight_check.run_command_plan(cast("Any", connection), safe_summary())

    assert actions == [
        {"action": "set_mode", "requested": "TAKEOFF", "result": "accepted"},
        {"action": "arm", "result": "accepted"},
        {"action": "takeoff", "altitude_m": 30, "result": "rejected", "reason": "command-failed"},
    ]
    assert connection.calls == [("set_mode", 13), ("arm", True), ("wait_armed", True)]
    assert connection.mav.command_long_calls == []
