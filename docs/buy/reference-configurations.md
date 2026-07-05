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

## Buying advice for Germany

These are the parts that are worth buying first if you are shopping in Germany right now. For fast-moving parts, the link goes to a live German price search instead of a fixed retailer.

| Part | Buy this when | Cheapest current Germany link | Advice |
|---|---|---|---|
| Jetson Orin Nano Super Developer Kit | You want the quickest JetPack/TensorRT bench setup and accept that the kit is for development, not the final airframe | [Geizhals search](https://www.geizhals.de/?fs=Jetson+Orin+Nano+Super+Developer+Kit) | Buy the dev kit only for bring-up and software work. For the aircraft, plan on a module plus a compact carrier. |
| Raspberry Pi 5 8GB | You only need recording, stream encoding, or light OpenCV | [Geizhals search](https://www.geizhals.de/?fs=Raspberry+Pi+5+8GB) | This is the sensible low-cost Linux node. In the current market, do not buy it as a cheap AI box. |
| Raspberry Pi 5 16GB | You need more local memory for models, buffering, or multi-process work | [Geizhals search](https://www.geizhals.de/?fs=Raspberry+Pi+5+16GB) | Buy only if the extra RAM is already justified. The 16 GB model is no longer a casual upgrade. |
| Matek H743 Wing | You want the cheapest H7 fixed-wing baseline and can verify the exact board revision | [Geizhals search](https://www.geizhals.de/?fs=Matek+H743+Wing) | Good value when you know the connector layout fits. Verify ArduPilot support and UART count before ordering. |
| Holybro Kakute H7 Wing | You want a cleaner long-life wing FC and are willing to pay more | [Geizhals search](https://www.geizhals.de/?fs=Holybro+Kakute+H7+Wing) | Better choice than a racing-style FC when the airframe is meant to grow. |
| Pixhawk 6C | You want carrier-style modularity and cleaner integration | [Geizhals search](https://www.geizhals.de/?fs=Pixhawk+6C) | Usually the better long-life buy if you expect later expansion and do not want to rewire the aircraft. |
| Cube Orange+ | You want the most modular carrier-based path and accept the highest cost | [Geizhals search](https://www.geizhals.de/?fs=Cube+Orange%2B) | Only buy this when the carrier-based path is a real requirement. It is hard to justify for a first, simple build. |

The short version is:

- buy the Pi 5 only for non-heavy compute or recording;
- buy the Jetson Orin Nano kit only if you need the NVIDIA software stack immediately;
- buy the cheapest H7 wing FC that still has the interfaces you need, but move to Pixhawk/Cube-class hardware if you want the aircraft to stay flexible for years.
