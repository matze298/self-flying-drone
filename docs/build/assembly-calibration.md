# Assembly and calibration

## Assembly order

1. Build the airframe and validate control geometry with **no propeller fitted**.
2. Install flight controller, receiver, GNSS and power module.
3. Configure ArduPilot Plane and the transmitter mode switch.
4. Bench-test outputs, sensor orientation and power/current monitoring.
5. Install telemetry and validate MAVLink on the ground.
6. Fly manual and stabilized modes until repeatable.
7. Configure and test RTL, fence, battery failsafe and RC loss behavior.
8. Add camera/video only after the basic aircraft is trustworthy.
9. Add companion compute only after the ground inference workflow is useful.

## Calibration discipline

| Calibration | When | Record |
|---|---|---|
| Accelerometer / board orientation | Every FC remount | Screenshot and parameter export |
| Compass | After relocation or wiring changes | Interference check with motor system |
| Radio endpoints / mode switch | After transmitter change | Channel map and switch labels |
| Power/current | Before battery failsafe tuning | Meter comparison and parameters |
| Camera intrinsics | After lens/resolution change | Calibration dataset + resulting matrix |
| Camera-to-body pose | After mount change | Measured yaw/pitch/roll offset |

## First autonomous mission

```text
Manual launch
→ establish safe altitude
→ one simple waypoint loop in empty approved area
→ record telemetry and video
→ manual or pre-tested RTL recovery
→ post-flight log review
```

No computer vision decision belongs in this mission.
