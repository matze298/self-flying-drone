# First implementation

The first real implementation should be a **fixed-wing software-in-the-loop (SITL) smoke test**. It gives us a working vertical slice before we own a finished aircraft, flight controller, camera mount, or companion computer.

This is step 1 in the [Learning path](../start/learning-path.md), after laptop-only docs/dev setup and before any hardware bench work. If an abbreviation is unfamiliar, check the [glossary](../appendix/glossary.md).

## Why this comes first

The current docs already define a simulation-first direction, a fixed-wing architecture, and a `sim` setup workstream. The next step should turn that into a repeatable command path that proves the development environment can talk Micro Air Vehicle Link (MAVLink) to a virtual ArduPilot Plane instance and record enough telemetry to support later safety checks.

This is intentionally smaller than a full simulator world, Robot Operating System 2 (ROS 2) graph, model pipeline, or onboard deployment. It should make the repo executable without pretending we have solved hardware integration.

## Proposed first deliverable

Build a minimal `SITL smoke test` workflow with these properties:

| Area | Skeleton target |
|---|---|
| Simulator | ArduPilot Plane SITL running from an external checkout |
| Project code | A small Python command-line interface (CLI) or test harness in this repo |
| Connection | MAVLink endpoint configured by CLI option or environment variable |
| Behavior | Connect, wait for heartbeat, subscribe to core telemetry, print/log a short status snapshot |
| Safety posture | Log-only; no mode changes, arming, mission upload, or actuator command path |
| Output | Machine-readable telemetry sample and human-readable smoke-test result |
| Testability | Can run against SITL in CI later, but starts as a documented local workflow |

## What not to implement first

Do not start with onboard inference, ROS 2 orchestration, Jetson deployment, autonomous mission response, object geolocation, or hardware-specific wiring automation. Those are valuable later, but they multiply unknowns before the basic simulator and MAVLink interface contract is proven.

## Documentation growth path

As each part becomes real, expand the docs in place:

| When it exists | Update |
|---|---|
| First CLI command | Add exact command examples and expected output |
| First telemetry sample | Add schema and example JSON |
| First SITL parameter set | Add parameter export location and reset instructions |
| First failure drill | Add radio control (RC) loss, low battery, fence, and reconnect observations |
| First CI job | Add continuous integration (CI) requirements and known simulator limitations |

## Acceptance criteria

The first implementation is useful when a developer can:

```text
[ ] install the sim workstream
[ ] start ArduPilot Plane SITL from documented commands
[ ] run one repo command that connects to SITL
[ ] see heartbeat, mode, position/altitude, battery, and link status
[ ] save a small telemetry artifact for review
[ ] confirm the repo code did not arm, change mode, upload a mission, or command actuators
```

The next implementation after this should be a replay-friendly telemetry/event log format. That keeps later vision work grounded in data we can test repeatedly.
