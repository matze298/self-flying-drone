"""Tests for SITL artifact helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from tools.sitl import artifacts, telemetry

if TYPE_CHECKING:
    import pathlib


def heartbeat_summary(*, mode: str = "MANUAL") -> telemetry.HeartbeatSummary:
    """Build a small heartbeat summary for artifact tests."""
    return telemetry.HeartbeatSummary(
        system_id=1,
        component_id=0,
        mode=mode,
        armed=False,
        custom_mode=0,
        vehicle_type=1,
        autopilot=3,
        heartbeat_wait_s=0.123,
        captured_at="2026-07-06T12:34:56Z",
        latitude_deg=None,
        longitude_deg=None,
        relative_altitude_m=None,
        battery_voltage_v=None,
        battery_current_a=None,
        battery_remaining_percent=None,
    )


def test_write_artifact_writes_sorted_pretty_json(tmp_path: pathlib.Path) -> None:
    """Artifact writing should use readable deterministic JSON."""
    output = tmp_path / "artifacts" / "sitl" / "smoke.json"

    artifacts.write_artifact({"source": "sitl-smoke-test", "schema_version": 1}, output)

    assert output.read_text(encoding="utf-8") == '{\n  "schema_version": 1,\n  "source": "sitl-smoke-test"\n}\n'


def test_create_smoke_artifact_keeps_empty_command_log() -> None:
    """Smoke artifacts should keep the observation-only command log empty."""
    summary = heartbeat_summary()

    artifact = artifacts.create_smoke_artifact(summary)
    heartbeat = cast("dict[str, object]", artifact["heartbeat"])

    assert artifact["source"] == "sitl-smoke-test"
    assert artifact["commanded_actions"] == []
    assert artifact["captured_at"] == "2026-07-06T12:34:56Z"
    assert heartbeat["captured_at"] == "2026-07-06T12:34:56Z"
    assert artifact["required_checks"] == ["unarmed", "vehicle", "ardupilot", "position", "battery"]


def test_create_flight_check_artifact_serializes_final_state() -> None:
    """Flight-check artifacts should include the observed post-command state."""
    preflight = heartbeat_summary()
    final_state = heartbeat_summary(mode="TAKEOFF")

    artifact = artifacts.create_flight_check_artifact(
        preflight,
        [{"action": "arm", "result": "accepted"}],
        "ok",
        final_state=final_state,
    )
    serialized_final_state = cast("dict[str, object]", artifact["final_state"])

    assert artifact["source"] == "sitl-flight-check"
    assert artifact["status"] == "ok"
    assert artifact["commanded_actions"] == [{"action": "arm", "result": "accepted"}]
    assert artifact["required_checks"] == [
        "unarmed",
        "vehicle",
        "ardupilot",
        "position",
        "battery",
        "explicit-command-opt-in",
    ]
    assert serialized_final_state["mode"] == "TAKEOFF"


def test_create_flight_check_artifact_allows_missing_final_state() -> None:
    """Failed flight-check artifacts may omit final state after a rejected command."""
    artifact = artifacts.create_flight_check_artifact(
        heartbeat_summary(),
        [{"action": "set_mode", "result": "rejected"}],
        "failed",
    )

    assert artifact["status"] == "failed"
    assert artifact["final_state"] is None


def test_build_required_checks_reflects_opt_outs() -> None:
    """Required checks should describe the checks enforced for the current run."""
    required_checks = artifacts.build_required_checks(
        require_ardupilot=False,
        require_position=False,
        require_battery=True,
    )

    assert required_checks == ["unarmed", "vehicle", "battery"]
