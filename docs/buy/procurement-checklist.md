# Procurement checklist

For concrete Germany/EU model choices and rough current price bands, use the [reference configuration buying advice](reference-configurations.md#buying-advice-for-germany) next to this checklist.

This checklist starts at the **hardware bench core** step in the [Learning path](../start/learning-path.md). The cheaper entry point is still docs + SITL; do not buy this whole list just to begin software work.

## Buy now: the reference core

| Item | Specification to put on purchase request | Why now |
|---|---|---|
| Airframe | 1.6–2.0 m pusher, serviceable bay, removable wings, spare parts availability | Determines all mechanical constraints |
| Radio | Reliable transmitter + ELRS receiver + mode switch plan | Essential manual safety path |
| Flight controller | H7 ArduPilot Plane-supported board; interfaces documented | Avoids later rewiring |
| GNSS | External compass; DroneCAN-capable if budget permits | Navigation/RTL/fence foundation |
| Power system | Battery, charger, power module, reliable regulator branches, connectors, spares | Enables safe bench and flight test |
| Telemetry | Independent MAVLink link | Needed to validate vehicle health and missions |
| Camera + storage | UVC camera, local storage, mounting materials | Enables data collection immediately |
| Tools/spares | Props, hardware, adhesives, connectors, heat shrink, fuses | Prevents a missing €2 item from blocking work |

## Reserve but defer

| Item | Reserve in design now | Purchase when |
|---|---|---|
| Jetson Orin Nano module/carrier | Tray, fuse, ventilation, camera/serial route | Ground-side workflow produces useful detections |
| Airspeed sensor | Pitot route, UART/CAN capacity | Before more advanced auto flight or wind-sensitive missions |
| Second camera | Mounting point, USB/CSI capacity | Single camera workflow is stable |
| RTK GNSS | DroneCAN/u-blox path and antenna plan | You have a real localization requirement |
| Payload release/actuator | Spare PWM output and mechanical mount | It becomes a defined, reviewed requirement |

## Do not buy yet

```text
VTOL conversion kit
Obstacle-avoidance sensor suite
Autonomous landing hardware
Multiple camera types “just in case”
A second autopilot for redundancy before you can operate the first one safely
Large AI compute without a measured model, frame rate, power, and thermal need
```
