# Interface contracts

## MAVLink companion contract

| Contract | Project rule |
|---|---|
| Transport | UART/USB from FC to companion; MAVLink router exposes local endpoints |
| Ownership | FC owns attitude, navigation, failsafe and actuator outputs |
| Companion read access | State, position, attitude, battery, mode, mission progress, health |
| Companion write access | Initially none; later only whitelisted high-level requests |
| Timeout | Stale telemetry invalidates detection/location association |
| Logging | Every request/action receives an ID and UTC timestamp |

## Video contract

| Contract | Project rule |
|---|---|
| Preview | Low-resolution H.264, independently reconnectable |
| Archive | Local recording whenever storage and power allow |
| Frame identity | Monotonic frame ID + UTC/monotonic timestamp |
| Camera metadata | Lens, resolution, crop, exposure mode, mount pose recorded |
| Failure | No video must not change flight behavior |

## Power contract

| Contract | Project rule |
|---|---|
| Flight rail | Remains operational if companion/video branch is absent |
| Compute rail | Fused, regulated and measured; restart permitted |
| Ground | Common reference where electrically required, documented wiring path |
| Brownout | Companion brownout must not reset FC/receiver/GNSS |

## Change-control contract

Every flight-changing change receives:

```text
change ID
reason
parts/firmware/software version
parameter diff
bench test record
simulation/replay result where applicable
flight test gate
rollback method
```
