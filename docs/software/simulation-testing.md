# Simulation and test tooling

## Simulation-first workflow

You do **not** need a drone or a flight controller to start useful software work. Start with a virtual fixed-wing aircraft and the same MAVLink-facing process boundaries planned for the real system.

The first concrete implementation milestone is the [SITL smoke test](../implementation/sitl-smoke-test.md): connect to ArduPilot Plane SITL, observe telemetry, and write a small log-only artifact without commanding the vehicle.

```bash
./setup.py --workstream sim --no-shell
```

This installs the Python-side client tools used by this repository:

| Tool | Why it is in the sim workstream |
|---|---|
| MAVSDK-Python | High-level async client for experiments against a running simulator |
| pymavlink | Low-level MAVLink inspection, decoding, and edge-case testing |
| aioconsole | Convenient interactive async REPL while exploring MAVSDK calls |

ArduPilot SITL itself is intentionally treated as an **external checkout**. It builds native autopilot code and uses system packages, so `uv` should not manage it. Use the repo helper in `tools/sitl/README.md` to create or reuse the checkout and launch a fixed-wing simulator:

```bash
uv run tools/sitl/run.py
```

After SITL is running, connect project tools to the simulator over MAVLink and keep the first behavior log-only.

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

## What simulation can and cannot prove

Simulation can prove interface behavior: MAVLink subscriptions, stale-data handling, event validation, mission-request rejection, replay determinism, and failure behavior when a software service restarts.

Simulation cannot prove airframe stability, CG, vibration, RF behavior, launch/landing handling, camera exposure, power integrity, or real flight-controller wiring. Those require bench tests, hardware-in-the-loop tests, and eventually conservative flight tests.

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
