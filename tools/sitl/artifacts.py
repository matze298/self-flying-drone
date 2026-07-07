"""Observation-only SITL smoke test."""

from __future__ import annotations

import pathlib
from dataclasses import asdict
from typing import TYPE_CHECKING

import orjson

if TYPE_CHECKING:
    from tools.sitl.telemetry import HeartbeatSummary

DEFAULT_OUTPUT = pathlib.Path("artifacts/sitl/smoke.json")
BASE_REQUIRED_CHECKS = ("unarmed", "vehicle")
DEFAULT_REQUIRED_CHECKS = (*BASE_REQUIRED_CHECKS, "ardupilot", "position", "battery")


def create_smoke_artifact(summary: HeartbeatSummary, *, required_checks: list[str] | None = None) -> dict[str, object]:
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


def create_flight_check_artifact(
    preflight_summary: HeartbeatSummary,
    commanded_actions: list[dict[str, object]],
    status: str,
    *,
    required_checks: list[str] | None = None,
    final_state: HeartbeatSummary | None = None,
) -> dict[str, object]:
    """Create the JSON-serializable flight check artifact."""
    checks = list(required_checks) if required_checks is not None else [*DEFAULT_REQUIRED_CHECKS]
    if "explicit-command-opt-in" not in checks:
        checks.append("explicit-command-opt-in")

    return {
        "schema_version": 1,
        "source": "sitl-flight-check",
        "connected": True,
        "status": status,
        "required_checks": checks,
        "captured_at": preflight_summary.captured_at,
        "preflight": asdict(preflight_summary),
        "commanded_actions": commanded_actions,
        "final_state": asdict(final_state) if final_state is not None else None,
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
