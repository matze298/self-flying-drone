# Flight control and navigation

## Flight-control selection

Pick an **H7-class board with documented ArduPilot Plane support**. The critical resource is not only CPU performance—it is the number of clean, available interfaces after the first build.

| Feature | Minimum | Reference build target |
|---|---|---|
| Firmware | Current ArduPilot Plane target | Same; confirm build target before purchase |
| Processor | STM32H7 class | H7 plus external storage/logging where appropriate |
| Outputs | 6 PWM minimum | 8+ PWM for flaps, future payload, or redundant control layout |
| Serial ports | 4 practical ports after RC | 6+ practical ports or a carrier system |
| CAN | Optional | At least one DroneCAN port |
| Power monitoring | Voltage/current support | Dedicated power module and verified calibration |
| IMU / vibration | Basic | Good isolation plan; board selection does not replace mechanical discipline |

### Shortlist strategy

| Type | Advantages | Trade-off | Good use |
|---|---|---|---|
| **Dedicated H7 wing FC** | Compact, lower cost, integrated distribution/OSD on some boards | More board-specific connectors, less service separation | Reference build with 1.6–2.0 m pusher |
| **Carrier-based Pixhawk/Cube** | Modular, clean connectors, less rework when vehicle grows | Larger and more expensive | Long-life system with Jetson NX or multiple sensors |
| **Racing-oriented FC** | Cheap and small | Fewer clean expansion interfaces; integration compromises | Not recommended as the long-life baseline |

## Navigation sensors

| Sensor | Start now? | Why |
|---|---|---|
| GNSS + external compass | Yes | Required for GPS navigation, fence, RTL behavior |
| Barometer | Normally part of FC | Altitude reference; protect it from direct prop wash |
| Airspeed sensor | Reserve space now; add before demanding fixed-wing automation | Improves fixed-wing energy/airspeed awareness |
| DroneCAN GNSS | Preferred when budget allows | Keeps UART capacity available and provides a clean expansion path |
| Rangefinder / lidar | Later | Helpful for specialized tasks, not a substitute for safe landing development |

## Required safety configuration before autonomous missions

```text
Manual / stabilized mode on transmitter switch
Return-to-Launch (RTL) configured and field-tested
RC loss action configured and tested
Battery failsafe configured and tested
Geofence configured and tested
GPS / EKF health check reviewed before takeoff
Audible locator / buzzer installed
```

ArduPilot’s Plane geofencing supports cylindrical and inclusion/exclusion fences, and Plane failsafe behavior is built around RTL. See the linked primary documentation in [References](../appendix/references.md).
