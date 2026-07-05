# Reference configurations

These are **architectures**, not all-in-one kits. They keep the project modular and make upgrades deliberate.

| | Ground-first lab | Upgradeable reference **(recommended)** | Compute-forward field lab |
|---|---|---|---|
| Airframe | 1.4–1.6 m pusher | 1.6–2.0 m pusher cargo platform | 1.8–2.2 m pusher cargo platform |
| Flight controller | H7 wing FC | H7 wing FC or carrier-based Pixhawk | Carrier-based Pixhawk/Cube class |
| GNSS | UART GNSS + compass | DroneCAN-ready GNSS | DroneCAN GNSS, optional RTK later |
| Compute at first | Laptop | Laptop, prepared Jetson mount | Jetson Orin Nano/NX |
| Video | Low-res digital link + local recording | Same, with dual-stream option | Jetson encode + low-res downlink + local high-res |
| Suitable task | Marker detection, offline data collection | Survey/marker workflow, onboard events later | Multi-camera / more demanding models |
| Planning budget* | €900–€1,600 | €1,500–€2,800 | €2,700–€5,000+ |

\*Planning ranges, not live quotations. Battery charger, transmitter, tools, spares and compliance costs vary materially.

## Reference build: recommended shopping logic

| Module | Minimum acceptable | Preferred long-life choice | Why it is future-friendly |
|---|---|---|---|
| Airframe | Repairable pusher with room for battery | 1.6–2.0 m pusher cargo airframe with removable wing and a true avionics bay | Supports power, cooling, camera, and CG adjustment later |
| Flight controller | H7 processor; at least 4 free UART-equivalents after basic wiring | Dedicated fixed-wing H7 board or carrier-based Pixhawk/Cube system | Enough ports for GNSS, RC, telemetry, companion, airspeed, and expansion |
| GNSS | Modern GNSS + external compass | DroneCAN-capable GNSS | Moves sensor expansion off the UART budget |
| RC link | ELRS receiver with serial protocol | ELRS with a reliable transmitter and explicit mode switch | High-quality manual override without ecosystem lock-in |
| Telemetry | MAVLink radio link | Independent long-range telemetry plus local Wi-Fi service link | Telemetry and video can fail independently |
| Compute | None on airframe at first | Jetson Orin Nano module + compact carrier; development kit only for bench | Supports TensorRT and future vision workloads |
| Camera | UVC USB camera | UVC USB camera for interchangeability; CSI only when connector/latency benefits are proven | Avoids camera lock-in at the beginning |
| Video | Local recording | Local high-res recording + bounded low-res H.264 stream | Keeps evidence even when downlink is weak |

## Example component families

| Function | Compact / cost-aware | Long-life modular | Carrier-based / maximum headroom |
|---|---|---|---|
| Flight controller | Matek H743 Wing family | Holybro Kakute H7 Wing or Matek H7 wing family | Cube Orange+ or Pixhawk 6C-class system with carrier |
| Companion | Raspberry Pi 5 + external accelerator | Jetson Orin Nano 8 GB | Jetson Orin NX 16 GB |
| Vision runtime | OpenCV + ONNX Runtime | TensorRT + ONNX Runtime + OpenCV | TensorRT + ROS 2 / GStreamer + OpenCV |
| Video transport | Simple RTSP/UDP lab link | OpenHD or WFB-ng class digital link | Jetson-based encode + redundant local recording |

!!! note "Use representative families, not blind substitutions"
    Check the current ArduPilot target, connector pinout, firmware support and voltage domains before purchasing any exact board revision. Interface changes between revisions can be material.
