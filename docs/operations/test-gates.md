# Test gates

Each gate is a documented release. A “pass” includes a log, configuration version, test location and observed outcome.

| Gate | Scope | Pass criterion | Exit action |
|---|---|---|---|
| **G-1 — SITL smoke** | Virtual ArduPilot Plane, MAVLink observation | Repo command observes heartbeat/telemetry without commanding the vehicle | Start hardware bench planning |
| **G0 — Bench power** | Power, wiring, smoke check | No overheating, correct voltage rails, current sensor plausible | Install prop only after all later electrical steps are complete |
| **G1 — Sensor/RC** | FC orientation, receiver, GNSS, switches | Correct movement and mode labels; no prop fitted | Configure failsafes |
| **G2 — Manual airframe** | Launch, trim, landing, CG | Repeatable flights and no unexplained behavior | Add/validate autopilot modes |
| **G3 — Autopilot safety** | RTL, geofence, RC loss, battery behavior | Each recovery behavior observed in safe field | Fly small waypoint mission |
| **G4 — Video observation** | Camera, stream, recording, telemetry association | Video and logs remain usable; no influence on flight | Run offline then live inference |
| **G5 — Detection log-only** | Model, confidence policy, replay | Detections reviewed against video; errors understood | Consider onboard deployment |
| **G6 — Onboard events** | Compute, power, thermal, watchdog | Companion failures do not affect aircraft safety | Optional bounded mission request |
| **G7 — Bounded response** | Preconfigured action | Action is reversible, limited and pilot-overridable | Keep repeated evaluation and change control |

## Flight-day checklist

```text
Before: regulatory/site check, weather, airframe inspection, CG, controls, prop, batteries, GNSS, RC modes, fence, RTL, storage, model version.
During: people/airspace awareness, battery reserve, link quality, mode awareness, no unplanned maneuver requests.
After: inspect airframe, save logs, label anomalies, archive configuration, recharge/store batteries safely.
```
