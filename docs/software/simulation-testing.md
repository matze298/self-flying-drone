# Simulation and test tooling

## Simulate the interfaces, not just the airframe

| Layer | Tool | Goal |
|---|---|---|
| Aircraft/autopilot | ArduPilot SITL | Validate modes, missions, fence and failure behavior |
| MAVLink client | MAVSDK-Python / pymavlink | Test subscriptions and command policy |
| Video | Recorded MP4 / GStreamer test source | Repeat detector behavior without flight |
| Vision | Unit tests + replay harness | Verify thresholds/debounce on known clips |
| Service failure | systemd / Docker restart tests | Confirm compute failures do not affect flight control |

## Replay harness

A replay test should consume the same interfaces as live operation:

```text
recorded video → capture interface → detector → event validator → log
recorded MAVLink → telemetry interface ────────────────────────┘
```

This makes every model update testable against the same flight data.

## SITL release checks

```text
[ ] Manual/stabilized/auto mode transitions understood
[ ] RTL route and altitude configured
[ ] RC loss action observed
[ ] Low-battery action observed
[ ] Fence action observed
[ ] Companion MAVLink reconnect does not change mode
[ ] Event request rejected when any safety precondition is false
[ ] No command path exists from detector directly to actuator output
```
