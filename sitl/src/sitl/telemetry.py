"""Contains telemetry functionality for SITL."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol

from pymavlink import mavutil

if TYPE_CHECKING:
    from pymavlink.mavutil import mavfile

DEFAULT_CONNECT = "udp:127.0.0.1:14550"

if mavutil.mavlink is None:
    raise RuntimeError("pymavlink dialect is not loaded.")

verified_mavlink = mavutil.mavlink


def get_mav_connection(connect: str) -> mavfile:
    """Return the mavlink_connection."""
    return mavutil.mavlink_connection(connect)


def utc_now() -> str:
    """Returns the current UTC time as a string."""
    return datetime.now(tz=UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


class ExpectedVehicle(StrEnum):
    """Vehicle types supported by the smoke-test expectation."""

    FIXED_WING = "fixed-wing"
    COPTER = "copter"
    ROVER = "rover"
    HELICOPTER = "helicopter"


@dataclass(frozen=True)
class HeartbeatSummary:
    """Decoded heartbeat fields for the smoke test."""

    system_id: int
    component_id: int
    mode: str
    armed: bool
    custom_mode: int
    vehicle_type: int
    autopilot: int
    heartbeat_wait_s: float
    captured_at: str
    latitude_deg: float | None
    longitude_deg: float | None
    relative_altitude_m: float | None
    battery_voltage_v: float | None
    battery_current_a: float | None
    battery_remaining_percent: int | None


class HeartbeatLike(Protocol):
    """MAVLink heartbeat fields used by the smoke test."""

    base_mode: int
    custom_mode: int
    type: int
    autopilot: int


@dataclass
class GlobalPosition:
    """Scale GLOBAL_POSITION_INT fields into human units."""

    lat: float | None
    lon: float | None
    relative_alt: float | None

    @staticmethod
    def from_message(connection: mavfile, timeout: float = 5.0) -> GlobalPosition:
        """Initialize GlobalPosition from a mavserial connection using GLOBAL_POSITION_INT."""
        message = connection.recv_match(type="GLOBAL_POSITION_INT", blocking=True, timeout=timeout)

        if message is None:
            return GlobalPosition(None, None, None)

        latitude = getattr(message, "lat", None)
        longitude = getattr(message, "lon", None)
        relative_altitude = getattr(message, "relative_alt", None)

        return GlobalPosition(
            latitude / 1e7 if latitude is not None else None,
            longitude / 1e7 if longitude is not None else None,
            relative_altitude / 1000 if relative_altitude is not None else None,
        )


@dataclass(frozen=True)
class BatteryStatus:
    """Decoded BATTERY_STATUS fields for the smoke test."""

    voltage_v: float | None
    current_a: float | None
    remaining_percent: int | None

    @staticmethod
    def from_message(connection: mavfile, timeout: float = 5.0) -> BatteryStatus:
        """Initialize BatteryStatus from a mavserial connection using BATTERY_STATUS."""
        message = connection.recv_match(type="BATTERY_STATUS", blocking=True, timeout=timeout)

        if message is None:
            return BatteryStatus(None, None, None)

        voltages = getattr(message, "voltages", None)
        current_battery = getattr(message, "current_battery", None)
        battery_remaining = getattr(message, "battery_remaining", None)

        return BatteryStatus(
            voltage_v=voltages[0] / 1000 if voltages and voltages[0] != 2**16 - 1 else None,
            current_a=current_battery / 100 if current_battery is not None and current_battery != -1 else None,
            remaining_percent=battery_remaining if battery_remaining is not None and battery_remaining != -1 else None,
        )


def decode_heartbeat(
    connection: mavfile,
    heartbeat: HeartbeatLike,
    *,
    position: GlobalPosition,
    battery_status: BatteryStatus,
    captured_at: str,
    heartbeat_wait_s: float = 0,
) -> HeartbeatSummary:
    """Decode the heartbeat fields we care about without sending commands."""
    armed = bool(heartbeat.base_mode & verified_mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
    mode = mavutil.mode_string_v10(heartbeat)
    return HeartbeatSummary(
        system_id=connection.target_system,
        component_id=connection.target_component,
        mode=mode,
        armed=armed,
        custom_mode=heartbeat.custom_mode,
        vehicle_type=heartbeat.type,
        autopilot=heartbeat.autopilot,
        heartbeat_wait_s=heartbeat_wait_s,
        latitude_deg=position.lat,
        longitude_deg=position.lon,
        relative_altitude_m=position.relative_alt,
        captured_at=captured_at,
        battery_voltage_v=battery_status.voltage_v,
        battery_current_a=battery_status.current_a,
        battery_remaining_percent=battery_status.remaining_percent,
    )
