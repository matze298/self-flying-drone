# Fixed-Wing Autonomy Lab — Buyers & Developers Guide

A modular, safety-first documentation site for a fixed-wing RC aircraft with ArduPilot, a companion computer, live video, and staged computer-vision experiments.

## Local preview

Install `uv` first. The official install guide is at
<https://docs.astral.sh/uv/getting-started/installation/>.

Create/update the local environment:

```bash
./setup.py
```

Activate the environment when you want an interactive local development shell:

```bash
source .venv/bin/activate
```

Set up a specific development workstream without installing unrelated toolchains:

```bash
./setup.py --workstream docs
./setup.py --workstream python
./setup.py --workstream sim
```

Available workstreams are `docs`, `python`, `sim`, `rust`, `ros`, and `jetson`. Workstreams that need a future Rust, ROS 2, or Jetson installer fail clearly until the repository contains those packages. The `sim` workstream installs Python-side MAVLink/software-in-the-loop (SITL) client tooling; ArduPilot SITL itself remains an external checkout with system dependencies.

Serve the documentation site:

```bash
uv run --group docs mkdocs serve
```

Open `http://127.0.0.1:8000`.

## Software-in-the-loop (SITL)

The cheapest useful software entry point is ArduPilot Plane SITL. It proves this repo can observe and command a virtual fixed-wing aircraft over MAVLink before any hardware is required.

The SITL tooling is a standalone Python workspace package under `sitl/`, with one root `uv.lock` for the Python workspace. Its command entry points are `sitl-run`, `sitl-smoke-test`, and `sitl-flight-check`.

Set up the repo-side simulator tools:

```bash
./setup.py --workstream sim
```

Create or reuse the external ArduPilot checkout and install upstream prerequisites when needed:

```bash
uv run --project sitl --group sim sitl-run --setup-only
uv run --project sitl --group sim sitl-run --install-prereqs --setup-only
```

Start ArduPlane SITL with a stable MAVLink output for repo tools:

```bash
uv run --project sitl --group sim sitl-run --mavlink-out udp:127.0.0.1:14550
```

After the first successful build, repeated local runs can usually skip ArduPilot's rebuild:

```bash
uv run --project sitl --group sim sitl-run --no-wipe -- -N
```

Run the observation-only smoke test from a second terminal:

```bash
uv run --project sitl --group sim sitl-smoke-test --connect udp:127.0.0.1:14550
cat artifacts/sitl/smoke.json
```

The smoke test writes a JSON artifact, verifies the vehicle is fixed-wing, verifies it is unarmed, and records no commanded actions.

The command-sending flight check has been validated against live ArduPlane SITL. The successful run recorded `TAKEOFF -> arm -> takeoff -> observe_progress -> RTL`, `relative_altitude_gain_m: 6.583`, final `mode: "RTL"`, and `status: "ok"`.

Full setup notes are in `sitl/README.md`, and the implementation milestone is documented in `docs/implementation/sitl-flight-check.md`.

Run formatting, linting, and type checks:

```bash
uv run --group dev prek run --all-files
```

Run unit tests:

```bash
uv run --group dev --group sim pytest
```

Install the Git hooks locally:

```bash
uv run --group dev prek install
```

Local hook implementations live in the `pre-commit/` workspace package; `prek.toml` wires them into the repo hook runner.

## Development stack

The project should stay in a **polyglot monorepo** for now. Documentation, ArduPilot configuration, Python tools, Rust services, ROS packages, deployment manifests, model manifests, and replay tests belong together because they describe one aircraft system and share interface contracts. Keep large raw datasets, videos, and model weights out of normal Git history.

Use a slim environment per workstream:

| Workstream | Default tools | Use it for | Why |
|---|---|---|---|
| Documentation and project tooling | Markdown, MkDocs Material, `uv`, `prek`, Ruff, ty | This guide, checks, small repo automation | Fast local setup and reproducible Python tooling |
| Python tools | Python, `uv`, MAVSDK-Python, OpenCV, ONNX Runtime | Ground-side inference, replay, evaluation, logs, CLIs | Fast iteration and the strongest robotics/ML scripting ecosystem |
| Simulation | ArduPilot SITL, MAVSDK-Python, pymavlink, recorded video/GStreamer sources | Virtual aircraft testing, MAVLink policy checks, replay before hardware | Lets software work start without an aircraft or flight controller |
| Rust services | Rust, Cargo | Standalone telemetry, logging, policy, or stream-supervision daemons | Memory safety and robust long-running services without forcing C++ everywhere |
| ROS 2 integration | Ubuntu 24.04, ROS 2 Jazzy, `colcon`, CMake, `rclcpp` | Multi-process robotics integration, simulation, ROS-native nodes | Best-supported ROS 2 path on the same Ubuntu generation as JetPack 7 |
| Jetson deployment | JetPack 7, TensorRT, GStreamer, Isaac ROS/DeepStream only when needed | Onboard accelerated perception and production deployment | Uses NVIDIA-supported acceleration and deployment paths |

`uv` manages Python environments and Python dependency groups. It does **not** manage C++, Rust, ROS, CUDA, TensorRT, or system packages. Use Cargo for Rust packages and `colcon`/CMake for ROS 2 or C++ packages.

Rust is preferred over new C++ where it can remain a standalone service with clean message/file/socket boundaries. C++ remains the fallback for first-class ROS 2 and NVIDIA/vendor integration, where upstream support, examples, and debugging tools still assume C++.

## Publish with GitHub Pages

1. Create a GitHub repository and push this directory.
2. In **Settings → Pages**, set **Source** to **GitHub Actions**.
3. Push to `main`. The included workflow builds and deploys the site.
4. Optionally set `site_url` and a custom domain in `mkdocs.yml`.

## Editorial policy

- Hardware recommendations are interface-first, not vendor-locked.
- Never let experimental vision code command control surfaces directly.
- Treat all cost bands as planning estimates, not live price quotes.
- Keep the Open-category EU operation model in mind: automatic missions are distinct from autonomous operation and a pilot intervention path remains essential.

## License

Documentation: CC BY 4.0. Source code snippets: MIT unless a file says otherwise.
