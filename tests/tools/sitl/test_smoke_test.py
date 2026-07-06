"""Tests for the SITL smoke-test script."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest
import typer
from pymavlink import mavutil

if TYPE_CHECKING:
    from types import ModuleType


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
SMOKE_TEST_PATH = PROJECT_ROOT / "tools" / "sitl" / "smoke_test.py"
EXPECTED_HEARTBEAT_WAIT_S = 0.123
EXPECTED_LATITUDE_DEG = 47.397742
EXPECTED_LONGITUDE_DEG = 8.545594
EXPECTED_RELATIVE_ALTITUDE_M = 12.3
RAW_LATITUDE = 473977420
RAW_LONGITUDE = 85455940
RAW_RELATIVE_ALTITUDE = 12300


@pytest.fixture
def smoke_test() -> ModuleType:
    """Load the standalone smoke-test script as a test module."""
    spec = importlib.util.spec_from_file_location("sitl_smoke_test", SMOKE_TEST_PATH)
    if spec is None or spec.loader is None:
        pytest.fail("Could not load SITL smoke-test module.")

    module = importlib.util.module_from_spec(spec)
    sys.modules["sitl_smoke_test"] = module
    previous_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous_dont_write_bytecode
    return module


def test_decode_heartbeat_reports_manual_unarmed(smoke_test: ModuleType) -> None:
    """Heartbeat decoding should expose the safe baseline state."""
    connection = SimpleNamespace(target_system=1, target_component=0)
    if mavutil.mavlink is None:
        raise RuntimeError("pymavlink dialect is not loaded.")

    mavlink = mavutil.mavlink
    heartbeat = mavlink.MAVLink_heartbeat_message(
        type=mavlink.MAV_TYPE_FIXED_WING,
        autopilot=mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA,
        base_mode=81,
        custom_mode=0,
        system_status=mavlink.MAV_STATE_STANDBY,
        mavlink_version=3,
    )

    position = smoke_test.GlobalPosition(
        lat=EXPECTED_LATITUDE_DEG,
        lon=EXPECTED_LONGITUDE_DEG,
        relative_alt=EXPECTED_RELATIVE_ALTITUDE_M,
    )
    summary = smoke_test.decode_heartbeat(
        connection,
        heartbeat,
        position=position,
        heartbeat_wait_s=EXPECTED_HEARTBEAT_WAIT_S,
    )

    assert summary.system_id == 1
    assert summary.component_id == 0
    assert summary.mode == "MANUAL"
    assert summary.armed is False
    assert summary.custom_mode == 0
    assert summary.vehicle_type == mavlink.MAV_TYPE_FIXED_WING
    assert summary.autopilot == mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA
    assert summary.heartbeat_wait_s == EXPECTED_HEARTBEAT_WAIT_S
    assert summary.latitude_deg == EXPECTED_LATITUDE_DEG
    assert summary.longitude_deg == EXPECTED_LONGITUDE_DEG
    assert summary.relative_altitude_m == EXPECTED_RELATIVE_ALTITUDE_M


def test_global_position_scales_message_fields(smoke_test: ModuleType) -> None:
    """GLOBAL_POSITION_INT should be scaled to degrees and meters."""
    message = SimpleNamespace(lat=RAW_LATITUDE, lon=RAW_LONGITUDE, relative_alt=RAW_RELATIVE_ALTITUDE)
    connection = SimpleNamespace(recv_match=lambda **_: message)

    position = smoke_test.GlobalPosition.from_message(connection)

    assert position.lat == EXPECTED_LATITUDE_DEG
    assert position.lon == EXPECTED_LONGITUDE_DEG
    assert position.relative_alt == EXPECTED_RELATIVE_ALTITUDE_M


def test_global_position_allows_missing_message(smoke_test: ModuleType) -> None:
    """Missing position telemetry should not fail the basic heartbeat smoke test."""
    connection = SimpleNamespace(recv_match=lambda **_: None)

    position = smoke_test.GlobalPosition.from_message(connection)

    assert position.lat is None
    assert position.lon is None
    assert position.relative_alt is None


def test_write_artifact_writes_sorted_pretty_json(smoke_test: ModuleType, tmp_path: pathlib.Path) -> None:
    """Artifact writing should use readable deterministic JSON."""
    output = tmp_path / "artifacts" / "sitl" / "smoke.json"

    smoke_test.write_artifact({"source": "sitl-smoke-test", "schema_version": 1}, output)

    assert output.read_text(encoding="utf-8") == '{\n  "schema_version": 1,\n  "source": "sitl-smoke-test"\n}\n'


def test_ensure_unarmed_exits_when_armed(smoke_test: ModuleType) -> None:
    """The smoke test should fail fast if the vehicle starts armed."""
    summary = smoke_test.HeartbeatSummary(
        system_id=1,
        component_id=0,
        mode="MANUAL",
        armed=True,
        custom_mode=0,
        vehicle_type=1,
        autopilot=3,
        heartbeat_wait_s=0.123,
        latitude_deg=None,
        longitude_deg=None,
        relative_altitude_m=None,
    )

    with pytest.raises(typer.Exit) as error:
        smoke_test.ensure_unarmed(summary)

    assert error.value.exit_code == 1
