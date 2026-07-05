# Bill of materials template

Copy this table into your issue tracker or CSV. Add the exact supplier, revision, firmware, delivery date and test result before fitting hardware.

| ID | Module | Exact model/revision | Interfaces | Voltage / max current | Mass | Firmware / driver | Test status | Spare? | Notes |
|---|---|---|---|---|---:|---|---|---|---|
| AIR-01 | Airframe |  |  |  |  |  |  |  |  |
| FC-01 | Flight controller |  | UART/CAN/PWM |  |  | ArduPilot target |  |  |  |
| GNSS-01 | GNSS/compass |  | CAN/UART |  |  |  |  |  |  |
| RC-01 | Receiver |  | CRSF/UART |  |  |  |  |  |  |
| TEL-01 | Telemetry radio |  | UART |  |  |  |  |  |  |
| CAM-01 | Camera |  | USB/CSI |  |  |  |  |  |  |
| CMP-01 | Companion computer |  | UART/USB/Ethernet |  |  | OS image hash |  |  |  |
| PWR-01 | Compute regulator |  |  |  |  |  |  |  |  |
| PWR-02 | FC power module |  |  |  |  |  |  |  |  |
| ACT-01 | Motor/ESC |  | PWM/DShot |  |  |  |  |  |  |
| ACT-02 | Servos |  | PWM |  |  |  |  |  |  |

## Cost model

Track four cost types separately:

```text
core aircraft   — parts that remain in all configurations
experiment      — sensors/compute specific to one research question
consumables     — props, foam, cables, batteries, adhesives
risk reserve    — spare FC, receiver, servo, props, field-repair kit
```
