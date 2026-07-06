# SITL

This is the minimal local setup for running ArduPilot Plane in software-in-the-loop (SITL). It follows the upstream ArduPilot Linux setup and keeps the ArduPilot checkout outside this repository.

References:

- [ArduPilot build environment on Linux/Ubuntu](https://ardupilot.org/dev/docs/building-setup-linux.html#building-setup-linux)
- [ArduPilot SITL setup on Linux](https://ardupilot.org/dev/docs/setting-up-sitl-on-linux.html#setting-up-sitl-on-linux)

## Setup

Run this once per development machine. Setup keeps ArduPilot as an explicit external checkout, installs only this repo's MAVLink client tooling in uv, and leaves native simulator dependencies to ArduPilot's upstream installer.

### 1. Configure the ArduPilot checkout path

Create or update `.env` in this repository:

```bash
ARDUPILOT_REPO=~/ws/ardupilot
```

The helper also accepts `--ardupilot-repo PATH` when you want to override `.env` for one run.

### 2. Install this repo's simulator client tools

From this repository:

```bash
./setup.py --workstream sim --no-shell
uv run --group sim python -c "import mavsdk, pymavlink; print('mavlink clients ok')"
```

This installs the Python-side tools used by this repo to talk MAVLink to a running simulator. It does not install or vendor ArduPilot itself.

If `uv` prints a warning about `VIRTUAL_ENV` not matching `.venv`, it is usually harmless for this command. `setup.py` itself is a uv script, and uv may ignore that temporary script environment while still syncing the project `.venv`.

### 3. Create or reuse the ArduPilot checkout

The helper clones ArduPilot when the configured path does not exist:

```bash
uv run tools/sitl/run.py --setup-only
```

Use `--no-clone` when you want the command to fail instead of creating the checkout.

### 4. Install ArduPilot prerequisites when needed

ArduPilot's Ubuntu prerequisite installer installs native build tools and simulator dependencies. It may use `sudo` and ask for your password. The helper prints a warning before running it:

```bash
uv run tools/sitl/run.py --install-prereqs --setup-only
```

If `sim_vehicle.py` is not found after prerequisite installation, reopen the shell or run:

```bash
. ~/.profile
```

## Usage

Run this whenever you want a local virtual aircraft. Usage creates a repeatable ArduPilot simulator process, defaults to the fixed-wing vehicle used by this repo, and publishes a stable MAVLink endpoint for repo smoke-test clients.

### Start SITL

```bash
uv run tools/sitl/run.py
```

The helper starts ArduPilot tools outside uv's isolated script environment so `sim_vehicle.py` can use the Python packages installed by ArduPilot's prerequisite script.

By default this starts:

```bash
Tools/autotest/sim_vehicle.py -v ArduPlane --map --console -w --out=udp:127.0.0.1:14550
```

Plane is the default because this repository is organized around a fixed-wing reference build. Other ArduPilot vehicles are available when you need them:

```bash
uv run tools/sitl/run.py --vehicle copter
uv run tools/sitl/run.py --vehicle rover
```

Use `--no-wipe` after the first successful run when you want to keep simulated parameter changes between sessions.

ArduPilot rebuilds before starting by default. After the first successful build, skip that rebuild during normal repeated runs by passing `-N` through to `sim_vehicle.py`:

```bash
uv run tools/sitl/run.py --no-wipe -- -N
```

The helper also exposes a stable MAVLink output endpoint for repo smoke-test clients:

```bash
uv run tools/sitl/run.py --mavlink-out udp:127.0.0.1:14550
```

Use `--mavlink-out ""` only when you intentionally do not want MAVProxy to publish a client endpoint.

### Expected result

MAVProxy should open a console and map, build ArduPlane if needed, and start a virtual aircraft. Keep this first workflow log-only: observe heartbeats, mode, armed state, and position before adding any repo command that sends MAVLink commands.

Typical windows after launch:

| Window | Purpose |
|---|---|
| Launch terminal | MAVProxy prompt and parent command output; type commands such as `mode`, `status`, or `param show SYSID_THISMAV` here |
| `console` | MAVProxy status/log display window |
| `ArduPlane` | Simulator process window |
| `Map` | MAVProxy map view |

Use the launch terminal for manual MAVProxy interaction. If the prompt is hidden by log output, press `Enter` once and look for a prompt such as `MANUAL>` or `STABILIZE>`.

Quick MAVProxy checks:

```text
mode
status
```

## Smoke test

The first repo-owned validation proves connectivity and observability without changing vehicle state. It gives us a safe baseline for later automated checks.

Start SITL first, then run the smoke test from a second terminal:

```bash
uv run --group sim python tools/sitl/smoke_test.py --connect udp:127.0.0.1:14550
cat artifacts/sitl/smoke.json
```

The smoke test records when the observation was captured, heartbeat identity, mode, armed state, vehicle type, autopilot type, the first position sample when available, and battery telemetry when SITL publishes it. It exits nonzero if no heartbeat arrives, if the vehicle is armed, or if the heartbeat does not describe the expected vehicle type. It writes no MAVLink commands and records `commanded_actions: []` in the artifact.

Position telemetry is optional by default so a newly started simulator can still produce a basic heartbeat artifact. Once SITL has settled, require the first `GLOBAL_POSITION_INT` sample explicitly:

```bash
uv run --group sim python tools/sitl/smoke_test.py --require-position
```

Battery telemetry is also optional by default because different SITL vehicles publish it at different points during startup. Require voltage, current, and remaining percentage once the vehicle publishes stable `BATTERY_STATUS` messages:

```bash
uv run --group sim python tools/sitl/smoke_test.py --require-battery
```

The default expected vehicle is `fixed-wing`, matching this repo's learning path:

```bash
uv run --group sim python tools/sitl/smoke_test.py --expected-vehicle fixed-wing
```

When you intentionally start another SITL vehicle, make the expectation explicit:

```bash
uv run tools/sitl/run.py --vehicle rover
uv run --group sim python tools/sitl/smoke_test.py --expected-vehicle rover
```

For example, launch the ArduPilot helicopter SITL variant in one terminal:

```bash
uv run tools/sitl/run.py --vehicle heli
```

The helper launches this as ArduCopter with the `heli` frame because ArduPilot does not have a top-level `Helicopter/` vehicle directory.

Then run the smoke test from a second terminal with the matching MAVLink heartbeat expectation:

```bash
uv run --group sim python tools/sitl/smoke_test.py --expected-vehicle helicopter
```

## Troubleshooting

Most early SITL failures are environment-boundary issues between this repo's uv environment, ArduPilot's system dependencies, and MAVProxy's windows/ports. Capture them here instead of rediscovering them during setup.

### `ModuleNotFoundError: No module named 'pexpect'`

ArduPilot's `sim_vehicle.py` must use the Python environment prepared by ArduPilot's prerequisite installer, not this repo's `.venv`. The helper strips this repo's virtual environment from the child process before launching ArduPilot tools.

If the error still appears, check the system Python directly:

```bash
/usr/bin/python3 -c "import pexpect; print(pexpect.__file__)"
```

Expected output is usually under `/usr/lib/python3/dist-packages/pexpect/`.

### `VIRTUAL_ENV` warning from uv

When running `./setup.py --workstream sim --no-shell`, uv may warn that a temporary script environment does not match `.venv`. This is expected for the self-executable setup script as long as the command finishes and prints `Simulation Python tools are installed.`

### Prompt hidden by log output

If logs obscure the MAVProxy prompt, focus the launch terminal and press `Enter` once.

### Keeping parameters between runs

The helper defaults to `--wipe` for repeatable first runs. Use this after the first successful launch when you want to keep simulated parameter changes:

```bash
uv run tools/sitl/run.py --no-wipe
```

### Rebuild on every launch

ArduPilot's `sim_vehicle.py` rebuilds by default. That is useful while the ArduPilot checkout changes, but it is unnecessary for most repeated smoke-test runs after the first successful build. Pass `-N` through to `sim_vehicle.py` to skip rebuilding:

```bash
uv run tools/sitl/run.py --no-wipe -- -N
```

## Raw upstream commands

The helper should be the normal path, but the raw commands make it clear what it wraps and provide a fallback when debugging upstream ArduPilot behavior.

If you need to bypass the helper, the equivalent manual flow is:

```bash
cd ..
git clone --recurse-submodules https://github.com/ArduPilot/ardupilot.git
cd ardupilot
Tools/environment_install/install-prereqs-ubuntu.sh -y
. ~/.profile
Tools/autotest/sim_vehicle.py -v ArduPlane --map --console -w --out=udp:127.0.0.1:14550
```
