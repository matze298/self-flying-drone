"""Tests for the command-sending SITL flight check."""

from __future__ import annotations

import json
import pathlib
from types import SimpleNamespace
from typing import Any, cast

import pytest
import typer
from pymavlink import mavutil
from typer.testing import CliRunner

from sitl import flight_check, telemetry

RUNNER = CliRunner()


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
        fail_set_mode_ids: set[int] | None = None,
        progress_altitudes_m: list[float | None] | None = None,
    ) -> None:
        """Initialize a fake connection with configurable mode mapping."""
        self.modes = modes if modes is not None else {"TAKEOFF": 13, "RTL": 11}
        self.mav = FakeMav(fail_takeoff=fail_takeoff)
        self.fail_arm = fail_arm
        self.fail_set_mode_ids = fail_set_mode_ids if fail_set_mode_ids is not None else set()
        self.progress_altitudes_m = progress_altitudes_m if progress_altitudes_m is not None else [18.0]
        self.calls: list[tuple[str, object]] = []

    def mode_mapping(self) -> dict[str, int]:
        """Return available ArduPilot mode names."""
        return self.modes

    def set_mode(self, mode_id: int) -> None:
        """Record mode changes."""
        if mode_id in self.fail_set_mode_ids:
            raise RuntimeError("set mode failed")
        self.calls.append(("set_mode", mode_id))

    def arducopter_arm(self) -> None:
        """Record the generic pymavlink arm command."""
        if self.fail_arm:
            raise RuntimeError("arm command failed")
        self.calls.append(("arm", True))

    def motors_armed_wait(self) -> None:
        """Record that the plan waited for the armed state."""
        self.calls.append(("wait_armed", True))

    def recv_match(self, **_kwargs: object) -> object | None:
        """Return fake position telemetry for progress observation."""
        if not self.progress_altitudes_m:
            return None
        altitude_m = self.progress_altitudes_m.pop(0)
        if altitude_m is None:
            return None
        return SimpleNamespace(lat=473977420, lon=85455940, relative_alt=int(altitude_m * 1000))


def safe_summary(*, mode: str = "MANUAL") -> telemetry.HeartbeatSummary:
    """Build a preflight-safe heartbeat summary for flight-check tests."""
    if mavutil.mavlink is None:
        raise RuntimeError("pymavlink dialect is not loaded.")

    return telemetry.HeartbeatSummary(
        system_id=1,
        component_id=0,
        mode=mode,
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
    captures = 0

    def fake_capture(*_args: object, **_kwargs: object) -> telemetry.HeartbeatSummary:
        nonlocal captures
        captures += 1
        return safe_summary(mode="MANUAL" if captures == 1 else "RTL")

    monkeypatch.setattr(flight_check, "capture_preflight_summary", fake_capture)
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
    captures = 0

    def fake_capture(*_args: object, **_kwargs: object) -> telemetry.HeartbeatSummary:
        nonlocal captures
        captures += 1
        return safe_summary(mode="MANUAL" if captures == 1 else "RTL")

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
        "mode": "RTL",
        "relative_altitude_m": 12.3,
        "system_id": 1,
        "vehicle_type": telemetry.verified_mavlink.MAV_TYPE_FIXED_WING,
    }


def test_run_flight_check_marks_failed_when_final_state_is_not_end_mode(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    """The flight check should fail when final telemetry is not in the requested end mode."""
    commanded_actions = [
        {"action": "set_mode", "requested": "TAKEOFF", "result": "accepted"},
        {"action": "arm", "result": "accepted"},
        {"action": "takeoff", "altitude_m": 30, "result": "sent"},
        {"action": "observe_progress", "relative_altitude_gain_m": 5.7, "result": "accepted"},
        {"action": "set_mode", "requested": "RTL", "result": "accepted"},
    ]
    connection = FakeCommandConnection()
    captures = 0

    def fake_capture(*_args: object, **_kwargs: object) -> telemetry.HeartbeatSummary:
        nonlocal captures
        captures += 1
        return safe_summary(mode="MANUAL" if captures == 1 else "TAKEOFF")

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
    assert cast("dict[str, object]", artifact["final_state"])["mode"] == "TAKEOFF"


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
        {"action": "observe_progress", "relative_altitude_gain_m": 5.7, "result": "accepted"},
        {"action": "set_mode", "requested": "RTL", "result": "accepted"},
    ]
    assert connection.calls == [("set_mode", 13), ("arm", True), ("wait_armed", True), ("set_mode", 11)]
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


def test_run_command_plan_records_mode_change_failure() -> None:
    """The command plan should record mode change command failures."""
    connection = FakeCommandConnection(fail_set_mode_ids={13})

    actions = flight_check.run_command_plan(cast("Any", connection), safe_summary())

    assert actions == [
        {
            "action": "set_mode",
            "requested": "TAKEOFF",
            "result": "rejected",
            "reason": "command-failed",
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


def test_run_command_plan_rejects_when_progress_is_not_observed() -> None:
    """The command plan should fail when takeoff progress is not observed."""
    connection = FakeCommandConnection(progress_altitudes_m=[])

    actions = flight_check.run_command_plan(cast("Any", connection), safe_summary(), progress_timeout_s=0.0)

    assert actions == [
        {"action": "set_mode", "requested": "TAKEOFF", "result": "accepted"},
        {"action": "arm", "result": "accepted"},
        {"action": "takeoff", "altitude_m": 30, "result": "sent"},
        {"action": "observe_progress", "result": "rejected", "reason": "progress-timeout"},
    ]


def test_run_command_plan_uses_configurable_takeoff_and_progress_values() -> None:
    """The command plan should allow flight-check tuning through arguments."""
    connection = FakeCommandConnection(progress_altitudes_m=[15.0])

    actions = flight_check.run_command_plan(
        cast("Any", connection),
        safe_summary(),
        takeoff_altitude_m=42.0,
        progress_required_gain_m=2.5,
        progress_timeout_s=1.0,
        progress_sample_timeout_s=0.1,
    )

    assert actions == [
        {"action": "set_mode", "requested": "TAKEOFF", "result": "accepted"},
        {"action": "arm", "result": "accepted"},
        {"action": "takeoff", "altitude_m": 42.0, "result": "sent"},
        {"action": "observe_progress", "relative_altitude_gain_m": 2.7, "result": "accepted"},
        {"action": "set_mode", "requested": "RTL", "result": "accepted"},
    ]


def test_run_command_plan_rejects_when_rtl_mode_is_unavailable() -> None:
    """The command plan should fail when the safe ending mode is unavailable."""
    connection = FakeCommandConnection(modes={"TAKEOFF": 13})

    actions = flight_check.run_command_plan(cast("Any", connection), safe_summary())

    assert actions == [
        {"action": "set_mode", "requested": "TAKEOFF", "result": "accepted"},
        {"action": "arm", "result": "accepted"},
        {"action": "takeoff", "altitude_m": 30, "result": "sent"},
        {"action": "observe_progress", "relative_altitude_gain_m": 5.7, "result": "accepted"},
        {"action": "set_mode", "requested": "RTL", "result": "rejected", "reason": "mode-unavailable"},
    ]


def test_main_wires_cli_tuning_options_to_flight_check(monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI should pass flight-check tuning options into the runner."""
    captured_options: dict[str, object] = {}

    def fake_run_flight_check(
        connect: str,
        timeout: float,
        output: pathlib.Path,
        *,
        command_opt_in: bool,
        takeoff_altitude_m: float,
        end_mode: str,
        progress_required_gain_m: float,
        progress_timeout_s: float,
        progress_sample_timeout_s: float,
    ) -> telemetry.HeartbeatSummary:
        captured_options.update(
            {
                "connect": connect,
                "timeout": timeout,
                "output": output,
                "command_opt_in": command_opt_in,
                "takeoff_altitude_m": takeoff_altitude_m,
                "end_mode": end_mode,
                "progress_required_gain_m": progress_required_gain_m,
                "progress_timeout_s": progress_timeout_s,
                "progress_sample_timeout_s": progress_sample_timeout_s,
            }
        )
        return safe_summary(mode="RTL")

    app = typer.Typer()
    app.command()(flight_check.main)
    monkeypatch.setattr(flight_check, "run_flight_check", fake_run_flight_check)

    result = RUNNER.invoke(
        app,
        [
            "--connect",
            "udp:127.0.0.1:14551",
            "--timeout",
            "3",
            "--output",
            "artifacts/sitl/custom-flight.json",
            "--i-understand-this-sends-commands",
            "--takeoff-altitude",
            "42",
            "--end-mode",
            "LOITER",
            "--progress-gain",
            "7.5",
            "--progress-timeout",
            "12",
            "--progress-sample-timeout",
            "0.5",
        ],
    )

    assert result.exit_code == 0
    assert captured_options == {
        "connect": "udp:127.0.0.1:14551",
        "timeout": 3.0,
        "output": pathlib.Path("artifacts/sitl/custom-flight.json"),
        "command_opt_in": True,
        "takeoff_altitude_m": 42.0,
        "end_mode": "LOITER",
        "progress_required_gain_m": 7.5,
        "progress_timeout_s": 12.0,
        "progress_sample_timeout_s": 0.5,
    }
