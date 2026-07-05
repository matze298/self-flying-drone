# Development stack

## Guiding choice

Use one repository with several intentionally small development environments. The aircraft, its configuration, its data contracts, and its software services are one system, so splitting them into separate repositories too early would make interface drift more likely. The repository should still avoid one mandatory mega-environment: developers install only the workstream they need.

## Platform baseline

Use **Ubuntu 24.04** as the developer and deployment baseline where practical. It aligns with the current Jetson software direction and keeps the ROS 2 target on the same Ubuntu generation. Use **ROS 2 Jazzy** for ROS work because it is the stable Ubuntu 24.04-aligned choice.

## Framework choices by project phase

| Phase | Primary tools | Why these choices fit |
|---|---|---|
| Documentation and project control | Markdown, MkDocs Material, `uv`, `prek`, Ruff, ty | The project starts as an engineering handbook. Markdown keeps design decisions reviewable, MkDocs publishes cheaply, and `uv` gives a reproducible Python tool environment. |
| Ground-side experiments | Python, `uv`, MAVSDK-Python, OpenCV, ONNX Runtime | The first useful loop is fast iteration on laptop-side capture, telemetry association, replay, and evaluation. Python has the strongest library coverage and easiest debugging path here. |
| Simulation-only development | ArduPilot SITL, MAVSDK-Python, pymavlink, recorded video or GStreamer test sources | A physical aircraft and flight controller should not block software work. SITL gives a virtual fixed-wing autopilot, while Python MAVLink clients exercise the same interface shape used later. |
| Standalone support services | Rust, Cargo | Rust is a good fit for long-running telemetry, logging, validation, and stream-supervision services where memory safety and explicit error handling matter. Keep these services behind files, sockets, or message interfaces so they do not depend on unstable ROS Rust bindings. |
| ROS integration | ROS 2 Jazzy, `colcon`, CMake, `rclcpp` | Use ROS where it solves a real robotics integration problem: nodes, topics, services, simulation, visualization, launch files, and hardware abstraction. C++ is still the most supported ROS path. |
| Onboard accelerated perception | JetPack 7, TensorRT, GStreamer, optional Isaac ROS or DeepStream | Jetson deployment should follow NVIDIA-supported APIs and containers. TensorRT and GStreamer are the relevant acceleration and video primitives; Isaac ROS or DeepStream should be added only when their packaged nodes reduce custom code. |

## Language policy

| Language | Default use | Avoid using it for |
|---|---|---|
| Python | Tooling, CLIs, replay, evaluation, ground-side inference, notebooks, MAVSDK experiments | Hard real-time loops, high-rate video internals, services that must survive messy input for months |
| Rust | New standalone daemons, telemetry/event processing, log tools, robust local services | Core ROS graph code until `rclrs` is stable enough for this project |
| C++ | ROS-native packages, vendor SDK integration, TensorRT/GStreamer code paths that need first-class upstream support | General application logic that can be simpler in Python or safer in Rust |

Rust is not excluded from ROS permanently. The current rule is narrower: do not put critical ROS 2 paths on Rust until the project explicitly accepts the integration risk. The Rust ROS ecosystem is active, but C++ remains the lowest-friction path for supported ROS 2 and NVIDIA examples.

## Monorepo layout

Keep the monorepo, but split build roots by toolchain:

```text
docs/                  # MkDocs handbook
src/                   # Python package and docs helper code
tools/python/          # Future Python CLIs and replay utilities
tools/sim/             # Future simulation launchers and SITL helpers
services/rust/         # Future Cargo workspace for standalone services
ros_ws/src/            # Future ROS 2 packages built with colcon
aircraft/              # Future parameters, missions, wiring records
deploy/                # Future systemd, container, and Jetson deployment config
models/                # Manifests only; keep large weights outside normal Git history
data/                  # Manifests only; keep raw videos/datasets outside normal Git history
```

This keeps one source of truth while allowing a developer to enter only the relevant environment.

Treat this as the canonical target layout. Individual implementation pages may introduce one subdirectory at a time, but they should not invent a second root structure.

## Slim setup model

| Need | Setup path |
|---|---|
| Read or edit docs | `./setup.py --workstream docs --no-shell` |
| Work on Python checks and tooling | `./setup.py --workstream python --no-shell` |
| Work with virtual aircraft and MAVLink clients | `./setup.py --workstream sim --no-shell` |
| Work on ground-side vision | Use `sim` now for MAVLink; add a future `vision`/`ground` group when the first CLI exists |
| Work on Rust services | Future Cargo/rustup setup; currently intentionally not implemented |
| Work on ROS/C++ packages | Future ROS 2 Jazzy and `colcon` setup; currently intentionally not implemented |
| Work on Jetson deployment | Future JetPack/container setup on target hardware; currently intentionally not implemented |

The setup script should fail clearly for unimplemented workstreams. A failed explicit request is better than silently installing a partial robotics toolchain.

Primary sources for these choices are collected in [References](../appendix/references.md).
