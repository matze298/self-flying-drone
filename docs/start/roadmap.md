# Roadmap

## Milestone map

```mermaid
flowchart LR
  M0[0. Docs + dev setup<br/>laptop only] --> M1[1. Simulator<br/>SITL smoke test]
  M1 --> M2[2. Hardware bench<br/>power + FC + RC]
  M2 --> M3[3. Manual aircraft<br/>reliable launch/landing]
  M3 --> M4[4. Autopilot safety<br/>RTL + geofence + waypoint]
  M4 --> M5[5. Ground inference<br/>observe only]
  M5 --> M6[6. Onboard events<br/>log/status only]
  M6 --> M7[7. Bounded response<br/>prevalidated loiter/camera action]
```

Use the [Learning path](learning-path.md) as the chapter-by-chapter reading order. The first implementation target is the [SITL smoke test](../implementation/sitl-smoke-test.md), which turns milestone M1 into a small repo-owned workflow before any aircraft hardware is required.

## Stop/go criteria

| Milestone | “Go” only when | Never proceed when |
|---|---|---|
| M0 | Docs build locally and the intended workstream setup is clear | You are about to install every toolchain just to read or edit docs |
| M1 | You can observe ArduPilot Plane SITL and understand simulated mode/failsafe behavior | You cannot explain the active simulated flight mode or recovery action |
| M2 | Bench power, FC, RC, GNSS, and telemetry are labeled and smoke-tested with no prop fitted | Wiring is undocumented or the FC depends on companion/video power |
| M3 | Ten incident-free manual flights with repeatable center of gravity and landing behavior | You are still changing propulsion or control geometry each flight |
| M4 | RTL, mode switch, geofence and telemetry-loss behavior have been tested in a safe field | Failsafe is only configured on a laptop, not tested in the air |
| M5 | Detections are timestamped, logged and visually reviewable after flight | A model output changes flight control |
| M6 | Companion restart, camera disconnect and compute brownout do not destabilize the vehicle | Flight controller or RC receiver shares a fragile power path with compute |
| M7 | Every requested action has bounds, timeout, cancel path and manual override | The behavior depends on a single unvalidated confidence score |
