# Learning path

This is the red thread through the guide. Start cheap, prove one interface at a time, and only buy or install the next layer when the previous one produces useful evidence.

```mermaid
flowchart LR
  L0[0. Docs + dev setup] --> L1[1. SITL smoke test]
  L1 --> L2[2. Hardware bench core]
  L2 --> L3[3. Manual aircraft]
  L3 --> L4[4. Autopilot safety]
  L4 --> L5[5. Ground inference]
  L5 --> L6[6. Onboard events]
  L6 --> L7[7. Bounded response]
```

## The path in one table

| Step | Goal | Minimum cost / hardware | Main docs |
|---|---|---|---|
| 0. Docs + dev setup | Read the system model, install only docs/sim tooling, understand safety boundaries | Laptop only | [Development stack](../software/development-stack.md), [Simulation and test tooling](../software/simulation-testing.md) |
| 1. SITL smoke test | Run a virtual ArduPilot Plane and prove repo-owned MAVLink observation | Laptop + external ArduPilot checkout | [First implementation](../implementation/index.md), [SITL smoke test](../implementation/sitl-smoke-test.md) |
| 2. Hardware bench core | Buy the smallest set that proves power, FC, RC, GNSS, and telemetry on the bench | Reference core only; no Jetson required | [Procurement checklist](../buy/procurement-checklist.md), [Power and wiring](../buy/power-wiring.md) |
| 3. Manual aircraft | Build and fly a stable fixed-wing aircraft without vision influence | Airframe, propulsion, FC, RC, GNSS, battery, telemetry | [Mechanical integration](../build/mechanical-integration.md), [Assembly and calibration](../build/assembly-calibration.md) |
| 4. Autopilot safety | Test RTL, geofence, battery, RC loss, and telemetry behavior | Same aircraft; no companion requirement | [Flight control and navigation](../buy/flight-control-navigation.md), [Failsafe design](../operations/failsafe-design.md) |
| 5. Ground inference | Record/replay video and telemetry, then run laptop-side detection as log-only | Camera/storage; laptop inference first | [Ground-side inference](../software/ground-inference.md), [Interface contracts](../appendix/interface-contracts.md) |
| 6. Onboard events | Move stable log-only perception onto protected onboard compute | Companion compute only after measured need | [Onboard inference](../software/onboard-inference.md), [Compute and cameras](../buy/compute-cameras.md) |
| 7. Bounded response | Allow only reviewed, reversible mission-level requests | Fully tested safety gates and operator override | [Test gates](../operations/test-gates.md), [Safety, legal, and ethics](../operations/safety-legal.md) |

## Cheap entry point

The cheapest meaningful start is **laptop-only**:

```bash
./setup.py --workstream docs --no-shell
./setup.py --workstream sim --no-shell
```

That is enough to read the handbook, build the docs, install the Python-side MAVLink client tools, and prepare for ArduPilot software-in-the-loop work. The first physical purchases should wait until the SITL path and interface choices are understood.

## Expansion rule

Each step must leave a useful artifact before the next step starts:

```text
SITL log -> bench power record -> manual flight log -> failsafe test record -> video/replay dataset -> onboard health log -> bounded action review
```

If a step does not produce an artifact that can be reviewed later, it is not finished.
