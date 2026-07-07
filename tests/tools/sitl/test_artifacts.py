"""Tests for SITL artifact helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from tools.sitl import artifacts, telemetry

if TYPE_CHECKING:
    import pathlib


def test_write_artifact_writes_sorted_pretty_json(tmp_path: pathlib.Path) -> None:
    """Artifact writing should use readable deterministic JSON."""
    output = tmp_path / "artifacts" / "sitl" / "smoke.json"

    artifacts.write_artifact({"source": "sitl-smoke-test", "schema_version": 1}, output)

    assert output.read_text(encoding="utf-8") == '{\n  "schema_version": 1,\n  "source": "sitl-smoke-test"\n}\n'


def test_create_smoke_artifact_keeps_empty_command_log() -> None:
    """Smoke artifacts should keep the observation-only command log empty."""
    summary = telemetry.HeartbeatSummary(
        system_id=1,
        component_id=0,
        mode="MANUAL",
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

    artifact = artifacts.create_smoke_artifact(summary)
    heartbeat = cast("dict[str, object]", artifact["heartbeat"])

    assert artifact["source"] == "sitl-smoke-test"
    assert artifact["commanded_actions"] == []
    assert artifact["captured_at"] == "2026-07-06T12:34:56Z"
    assert heartbeat["captured_at"] == "2026-07-06T12:34:56Z"
    assert artifact["required_checks"] == ["unarmed", "vehicle", "ardupilot", "position", "battery"]


def test_build_required_checks_reflects_opt_outs() -> None:
    """Required checks should describe the checks enforced for the current run."""
    required_checks = artifacts.build_required_checks(
        require_ardupilot=False,
        require_position=False,
        require_battery=True,
    )

    assert required_checks == ["unarmed", "vehicle", "battery"]
