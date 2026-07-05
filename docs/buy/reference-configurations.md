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

Use this as the first-pass German/EU shopping list. Each row names a concrete default option per subsystem, gives a rough current street-price indicator, and explains whether to buy it now. The bias is toward hardware we can customize through open or standard software interfaces: ArduPilot, MAVLink, ELRS/CRSF, Linux, V4L2, OpenCV, GStreamer, ROS 2, and TensorRT.

!!! tip "Zero-hardware entry point"
    Do not start by buying the full aircraft. First follow the [Learning path](../start/learning-path.md): build the docs, install the `sim` workstream, and run toward the SITL smoke test. Buy the reference core when you are ready for bench integration and can explain why each interface is needed.

!!! note "Prices are rough indicators"
    The price bands are planning numbers for Germany/EU shopping, not a promise of the cheapest live offer. Check at least one specialist RC/autopilot shop and one general electronics shop before ordering. Good recurring sources are FPV24, Globe-Flight, n-Factory, Drotek, Welectron, BerryBase, Reichelt, Modellbau Berlinski, direct manufacturer pages, and Google Shopping. Use Geizhals only when it has a useful listing for the exact part.

### Why start plane-like

Start with a fixed-wing, plane-like platform for this project unless the first mission explicitly requires hovering, indoor flight, or vertical takeoff. Our early goals are simulation, navigation, camera data collection, mapping/survey-style routes, and eventually onboard perception. A pusher fixed-wing gives better endurance, more internal volume, lower cruise power, cleaner forward-looking camera geometry, and more time to recover from mistakes than a quadcopter.

The tradeoff is that a fixed-wing aircraft needs more space, has harder launch and landing phases, cannot hover, and has less precise low-speed positioning. A quadcopter is the better first platform for hover inspection, confined areas, payload pickup, or close-range obstacle work. For this repository's current learning path, fixed-wing makes the software and integration work more useful earlier while keeping the aircraft modular enough to add heavier compute later.

### Buy for the bench core

These parts define the aircraft layout, wiring, safety path, and first useful data collection workflow. Buy them when moving from SITL to bench integration, before optimizing onboard AI compute.

| System | Default option | Rough price / direct source | Buy now? | Why / checks before ordering |
|---|---|---|---|---|
| Airframe | Volantex Ranger 1600 / Ranger 2000 class pusher airframe | about 180-350 EUR, e.g. [Modellbau Berlinski search](https://www.modellbau-berlinski.de/search?sSearch=Volantex+Ranger) | Yes | This is the first choice to buy because it fixes bay volume, CG, wiring paths, camera placement, and payload margin. Choose a pusher with a real electronics bay, spare parts availability, and enough room for an autopilot, GNSS mast, battery, and later companion tray. |
| Flight controller | Matek H743-WING V3 | about 90-130 EUR, e.g. [n-Factory search](https://n-factory.de/search?sSearch=Matek+H743+Wing) | Yes | Cost-effective H7 fixed-wing baseline with enough IO for ArduPilot Plane. Verify the exact revision, ArduPilot target, connector pinout, spare UART/CAN budget, and soldering comfort before ordering. |
| RC transmitter | RadioMaster Boxer ELRS 2.4 GHz | about 150-190 EUR, e.g. [FPV24 search](https://www.fpv24.com/en/search?sSearch=RadioMaster+Boxer+ELRS) | Yes | Manual override is non-negotiable. ELRS gives a modern, open, scriptable RC ecosystem with CRSF telemetry and enough switches for mode, arm/disarm, and failsafe drills. |
| RC receiver | RadioMaster RP3 ELRS 2.4 GHz | about 20-35 EUR, e.g. [FPV24 search](https://www.fpv24.com/en/search?sSearch=RadioMaster+RP3+ELRS) | Yes | Keeps the control link compatible with the transmitter. Confirm antenna placement, CRSF wiring, and telemetry settings before closing the fuselage. |
| GNSS + compass | Holybro DroneCAN M10 GPS | about 90-140 EUR, e.g. [Drotek search](https://drotek.com/shop/en/search?controller=search&s=Holybro+DroneCAN+M10) | Yes | DroneCAN keeps sensor expansion off scarce UARTs and is worth buying early if budget allows. If unavailable, use a Matek M10Q-5883 class UART GNSS and preserve CAN wiring space. |
| Telemetry radio | Holybro SiK Telemetry Radio V3 868 MHz pair | about 70-120 EUR, e.g. [Drotek search](https://drotek.com/shop/en/search?controller=search&s=Holybro+SiK+868) | Yes | Gives an independent MAVLink health and mission link. Use the EU 868 MHz variant in Germany and keep it separate from RC and video experiments. |
| Power sensing | Holybro PM02D or Matek fixed-wing power module | about 25-60 EUR, e.g. [Drotek search](https://drotek.com/shop/en/search?controller=search&s=PM02D) | Yes | Current and voltage telemetry are required for safe bench and flight testing. Confirm connector style, current rating, battery voltage, and ArduPilot calibration path. |
| Regulated power | Matek 5V/12V BEC class regulator | about 10-30 EUR, e.g. [n-Factory search](https://n-factory.de/search?sSearch=Matek+BEC) | Yes | Keep flight controller, servos, camera, and companion power isolated enough that one noisy load does not reset the autopilot. Size final regulators after the exact airframe electronics are known. |
| Battery | 4S LiPo 5000 mAh class pack | about 50-100 EUR, e.g. [Globe-Flight search](https://www.globe-flight.de/search?sSearch=4S+5000) | Yes | A common 4S pack is enough for bench tests and early flights, but final capacity depends on the airframe, motor, CG, and legal weight target. |
| Charger | SkyRC B6 Neo | about 35-60 EUR, e.g. [Reichelt search](https://www.reichelt.de/de/en/index.html?ACTION=446&SEARCH=SkyRC%20B6%20Neo) | Yes | The charger blocks every real bench and field session. Buy a known current charger, a safe power supply if required, and a LiPo bag or storage box. |
| Camera | Logitech C920s/C922 USB camera | about 60-110 EUR, e.g. [Reichelt search](https://www.reichelt.de/de/en/index.html?ACTION=446&SEARCH=Logitech%20C920s) | Yes | UVC keeps the first data collection path simple across Linux laptops, Raspberry Pi, and Jetson via V4L2/OpenCV/GStreamer. It is not the final flight camera if latency, optics, or mounting become limiting. |
| Storage | Samsung PRO Plus microSDXC 128 GB | about 15-30 EUR, e.g. [Reichelt search](https://www.reichelt.de/de/en/index.html?ACTION=446&SEARCH=Samsung%20PRO%20Plus%20128GB%20microSD) | Yes | Local logs and video are the first useful artifacts. Buy enough reliable storage before adding complex downlinks. |
| Tools + spares | XT60 parts, servo extensions, heat shrink, fuses, threadlocker, glue, spare props | about 100-200 EUR starter reserve, source by basket from RC/electronics shops | Yes | Small parts routinely block builds. Treat this as a consumable kit and replenish it instead of waiting for individual missing pieces. |

### Buy after the ground workflow works

These parts are useful, but buying them before logs, camera capture, and simulation are working tends to hide integration problems behind hardware churn.

| System | Default option | Rough price / direct source | Buy now? | Why / checks before ordering |
|---|---|---|---|---|
| Companion compute, light | Raspberry Pi 5 8 GB | about 120-170 EUR in the current inflated Pi market, e.g. [BerryBase](https://www.berrybase.de/) | Usually defer | Buy when the task is logging, streaming, orchestration, or light OpenCV. Do not buy it as the default AI accelerator. |
| Companion compute, AI bench | NVIDIA Jetson Orin Nano Super Developer Kit | about 260-350 EUR, e.g. [Welectron search](https://www.welectron.com/search?sSearch=Jetson+Orin+Nano+Super) | Defer unless AI work starts now | Best first NVIDIA/TensorRT bench system. For the aircraft, plan a production module plus compact carrier once the model, frame rate, power, cooling, and mount are measured. |
| Video downlink | OpenHD/WFB-ng capable USB Wi-Fi adapter, e.g. Alfa AWUS036ACHM class | about 25-60 EUR per adapter, e.g. [Reichelt search](https://www.reichelt.de/de/en/index.html?ACTION=446&SEARCH=Alfa%20AWUS036ACHM) | Defer | Local recording is enough for early flights. Buy video hardware only when you know whether you need low-latency pilot video, low-rate monitoring, or just post-flight evidence. |
| Airspeed | Matek ASPD-4525 or MS4525DO sensor | about 25-50 EUR, e.g. [n-Factory search](https://n-factory.de/search?sSearch=Matek+ASPD) | Defer | Reserve tubing and a port now, but buy after basic manual and assisted flight is stable or before wind-sensitive auto missions. |

### Reserve space, do not buy yet

These choices should influence layout and connectors, but they are poor first purchases for the reference build.

| System | Default option | Rough price / direct source | Buy now? | Why / checks before ordering |
|---|---|---|---|---|
| RTK GNSS | Holybro H-RTK F9P DroneCAN kit | about 250-450 EUR, e.g. [Drotek search](https://drotek.com/shop/en/search?controller=search&s=H-RTK+F9P+DroneCAN) | No | Reserve CAN, antenna placement, and ground-station support. Buy only when centimeter-class positioning is a real requirement. |
| Companion compute, final aircraft | Jetson Orin Nano 8 GB module + compact carrier | about 350-600 EUR combined, e.g. [Welectron search](https://www.welectron.com/search?sSearch=Jetson+Orin+Nano+module+carrier) | No | The dev kit is for software bring-up. The flight unit should be selected after thermal, power, camera, storage, and enclosure needs are measured. |
| Second camera | Raspberry Pi Camera Module 3 or selected UVC/CSI camera | about 35-90 EUR, e.g. [BerryBase search](https://www.berrybase.de/search?sSearch=Raspberry+Pi+Camera+Module+3) | No | Keep physical space and USB/CSI budget, but add a second camera only after one-camera capture, timestamps, storage, and review workflows are boring. |
| Payload actuator | Metal-gear micro servo, release mechanism, and fuse path | about 10-40 EUR for servo parts before mechanism work, e.g. [Globe-Flight search](https://www.globe-flight.de/search?sSearch=Metallgetriebe+Micro+Servo) | No | Reserve PWM and mechanical mounting. Do not buy or test payload release hardware until the requirement and safety review exist. |

### Viable fallback options

Use fallbacks when the default is unavailable, the chosen airframe changes the physical constraints, or a subsystem budget needs to move up or down. Do not mix alternatives blindly; re-check connector types, voltage domains, ArduPilot target support, and mounting space after any substitution.

| System | Default | Fallbacks | When the fallback makes sense |
|---|---|---|---|
| Airframe | Volantex Ranger 1600 / Ranger 2000 class pusher | Heewing T1 Ranger class; Sonicmodell AR Wing Pro; Skywalker X8 / large EPO wing; Multiplex EasyStar 3 as a smaller trainer-only fallback | Pick a larger pusher/cargo airframe when bay volume and payload margin matter. Pick an AR-wing style platform when transport and ruggedness matter more than internal space. Pick EasyStar only for cheap fixed-wing learning, not as the long-life avionics carrier. |
| Flight controller | Matek H743-WING V3 | Holybro Kakute H7 Wing; Pixhawk 6C; Cube Orange+ carrier system | Use Kakute H7 Wing for a cleaner fixed-wing board if available. Move to Pixhawk/Cube when carrier-style connectors, serviceability, and expansion headroom are worth the cost and weight. |
| RC transmitter + receiver | RadioMaster Boxer ELRS + RP3 | RadioMaster TX16S MKII ELRS; RadioMaster Pocket ELRS for budget/compact use; another ELRS receiver with CRSF telemetry and suitable antennas | Stay in ELRS unless there is a strong reason not to. TX16S is better for a full ground station, Pocket is cheaper for bench and trainer work, and receiver choice should follow antenna placement and range needs. |
| GNSS + compass | Holybro DroneCAN M10 GPS | Matek M10Q-5883 UART; Holybro M10 UART; Here4 / HerePro DroneCAN | Use UART GNSS to save money or when CAN parts are unavailable. Use Here-class DroneCAN modules when packaging, casing, and long-term serviceability matter more than cost. |
| Telemetry | Holybro SiK 868 MHz pair | mRo SiK 868 MHz pair; RFD868x pair; Wi-Fi MAVLink only for bench/local tests | Use another SiK pair for equivalent low-rate MAVLink telemetry. Use RFD868x when range and link budget become real requirements. Do not treat Wi-Fi as the primary field safety telemetry link. |
| Power sensing and distribution | Holybro PM02D / Matek fixed-wing power module | Mauch current sensor; Holybro PM07/Pixhawk power module; Matek FCHUB/PDB class board | Use Mauch for higher-quality current sensing on larger builds. Use Pixhawk-style modules when the FC ecosystem expects that connector path. Use PDB-style boards only when the current rating and cooling fit the airframe. |
| Companion compute | Raspberry Pi 5 for light Linux work; Jetson Orin Nano Super kit for AI bench | Jetson Orin Nano module + compact carrier; Jetson Orin NX; small x86/N100 mini PC for bench-only workflows | Use Pi for logging and orchestration, Jetson Nano for TensorRT development, Orin NX only after measured model needs justify it, and x86 only on the bench or ground station. |
| Camera | Logitech C920s/C922 UVC | ELP UVC camera module; Arducam/Raspberry Pi Camera Module 3; selected CSI camera for Jetson | Use UVC while software is still changing. Move to CSI only when latency, size, optics, or synchronization justify extra platform-specific integration. |
| Video downlink | Local recording first, OpenHD/WFB-ng later | Wi-Fi MAVLink video for lab only; analog FPV for pilot awareness only; Jetson/GStreamer H.264 stream | Keep local recording as the evidence source. Add downlink only after deciding whether the use case is pilot awareness, live monitoring, or machine-vision debugging. |

The short version is: start with docs and SITL, then buy airframe, FC, RC, GNSS, telemetry, power, battery/charger, camera/storage, and tools for the bench core. Defer Jetson, video downlink, airspeed, RTK, second camera, and payload hardware until the simulator, ground-side camera workflow, and basic aircraft integration are working.
