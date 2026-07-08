#!/usr/bin/env -S uv run --script
"""Run ArduPilot Plane SITL from an external checkout."""

from __future__ import annotations

import enum
import os
import pathlib
import subprocess
from typing import TYPE_CHECKING, Annotated

import typer

if TYPE_CHECKING:
    from collections.abc import Mapping

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"
ARDUPILOT_REPO_ENV = "ARDUPILOT_REPO"
DEFAULT_ARDUPILOT_REPO = pathlib.Path("~/ws/ardupilot")
ARDUPILOT_GIT_URL = "https://github.com/ArduPilot/ardupilot.git"
SIM_VEHICLE = pathlib.Path("Tools/autotest/sim_vehicle.py")
PREREQ_SCRIPT = pathlib.Path("Tools/environment_install/install-prereqs-ubuntu.sh")
UV_ENV_KEYS = ("UV", "UV_PROJECT_ENVIRONMENT", "VIRTUAL_ENV", "PYTHONHOME", "PYTHONPATH")
DEFAULT_MAVLINK_OUT = "udp:127.0.0.1:14550"


class Vehicle(enum.StrEnum):
    """Supported ArduPilot SITL vehicle types."""

    plane = "plane"
    copter = "copter"
    rover = "rover"
    sub = "sub"
    heli = "heli"
    blimp = "blimp"


VEHICLE_TARGETS = {
    Vehicle.plane: "ArduPlane",
    Vehicle.copter: "ArduCopter",
    Vehicle.rover: "Rover",
    Vehicle.sub: "ArduSub",
    Vehicle.heli: "ArduCopter",
    Vehicle.blimp: "Blimp",
}


def read_env_file(env_file: pathlib.Path) -> dict[str, str]:
    """Read simple KEY=VALUE entries from a dotenv-style file."""
    if not env_file.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", maxsplit=1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key:
            values[key] = value

    return values


def resolve_ardupilot_repo(
    ardupilot_repo: str | pathlib.Path | None,
    *,
    project_root: pathlib.Path = PROJECT_ROOT,
) -> pathlib.Path:
    """Resolve the ArduPilot checkout path from CLI, .env, or default."""
    if ardupilot_repo is not None:
        raw_path = os.fspath(ardupilot_repo)
    else:
        env_values = read_env_file(project_root / ".env")
        raw_path = env_values.get(ARDUPILOT_REPO_ENV, os.fspath(DEFAULT_ARDUPILOT_REPO))

    return pathlib.Path(os.path.expandvars(raw_path)).expanduser()


def is_ardupilot_checkout(repo_path: pathlib.Path) -> bool:
    """Return whether the path looks like an ArduPilot checkout."""
    return (repo_path / SIM_VEHICLE).is_file()


def build_sim_vehicle_command(
    repo_path: pathlib.Path,
    *,
    vehicle: Vehicle,
    wipe: bool,
    mavlink_out: str | None,
    map_window: bool = True,
    console: bool = True,
    extra_args: list[str] | None = None,
) -> list[str]:
    """Build the ArduPilot SITL command."""
    command = [os.fspath(repo_path / SIM_VEHICLE), "-v", VEHICLE_TARGETS[vehicle]]
    if vehicle is Vehicle.heli:
        command.extend(("-f", "heli"))
    if map_window:
        command.append("--map")
    if console:
        command.append("--console")
    if wipe:
        command.append("-w")
    if mavlink_out:
        command.append(f"--out={mavlink_out}")
    command.extend(extra_args or [])
    return command


def external_tool_env(env: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return an environment suitable for ArduPilot's system-Python tools."""
    clean_env = dict(env or os.environ)
    active_venv = clean_env.get("VIRTUAL_ENV")
    blocked_path_entries = {os.fspath(PROJECT_ROOT / ".venv" / "bin")}
    if active_venv:
        blocked_path_entries.add(os.fspath(pathlib.Path(active_venv) / "bin"))

    path_entries = clean_env.get("PATH", "").split(os.pathsep)
    clean_env["PATH"] = os.pathsep.join(entry for entry in path_entries if entry not in blocked_path_entries)

    for key in UV_ENV_KEYS:
        clean_env.pop(key, None)

    return clean_env


def clone_ardupilot(repo_path: pathlib.Path) -> None:
    """Clone ArduPilot with submodules into the requested path."""
    repo_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--recurse-submodules", ARDUPILOT_GIT_URL, os.fspath(repo_path)],
        check=True,
        env=external_tool_env(),
    )


def install_prerequisites(repo_path: pathlib.Path) -> None:
    """Run ArduPilot's Ubuntu prerequisite installer."""
    prereq_script = repo_path / PREREQ_SCRIPT
    if not prereq_script.is_file():
        message = f"ArduPilot prerequisite script not found: {prereq_script}"
        raise typer.BadParameter(message)

    typer.secho(
        "ArduPilot's prerequisite installer may use sudo and can ask for your password.",
        fg=typer.colors.YELLOW,
        err=True,
    )
    subprocess.run([os.fspath(prereq_script), "-y"], cwd=repo_path, check=True, env=external_tool_env())


def ensure_checkout(repo_path: pathlib.Path, *, clone_if_missing: bool) -> None:
    """Ensure the ArduPilot checkout exists and has the SITL launcher."""
    if not repo_path.exists():
        if not clone_if_missing:
            message = f"ArduPilot checkout does not exist: {repo_path}"
            raise typer.BadParameter(message)

        typer.echo(f"Cloning ArduPilot into {repo_path}")
        clone_ardupilot(repo_path)

    if not is_ardupilot_checkout(repo_path):
        message = f"Path does not look like an ArduPilot checkout: {repo_path}"
        raise typer.BadParameter(message)


def main(
    ardupilot_repo: Annotated[
        pathlib.Path | None,
        typer.Option(
            "--ardupilot-repo",
            "-a",
            help=f"Path to the ArduPilot checkout. Defaults to {ARDUPILOT_REPO_ENV} in .env or ~/ws/ardupilot.",
        ),
    ] = None,
    clone: Annotated[
        bool,
        typer.Option(
            "--clone/--no-clone",
            help="Clone ArduPilot when the checkout path does not exist.",
        ),
    ] = True,
    install_prereqs: Annotated[
        bool,
        typer.Option(
            "--install-prereqs/--no-install-prereqs",
            help="Run ArduPilot's Ubuntu prerequisite installer before SITL. This may use sudo.",
        ),
    ] = False,
    setup_only: Annotated[
        bool,
        typer.Option(
            "--setup-only/--run",
            help="Create or validate the checkout, optionally install prerequisites, then exit without starting SITL.",
        ),
    ] = False,
    vehicle: Annotated[
        Vehicle,
        typer.Option(
            "--vehicle",
            "-v",
            case_sensitive=False,
            help="ArduPilot vehicle to simulate.",
        ),
    ] = Vehicle.plane,
    wipe: Annotated[
        bool,
        typer.Option(
            "--wipe/--no-wipe",
            help="Reset simulated parameter storage before starting SITL.",
        ),
    ] = True,
    map_window: Annotated[
        bool,
        typer.Option("--map/--no-map", help="Open the simulator map window."),
    ] = True,
    console: Annotated[
        bool,
        typer.Option("--console/--no-console", help="Open the MAVProxy console."),
    ] = True,
    mavlink_out: Annotated[
        str | None,
        typer.Option(
            "--mavlink-out",
            help="MAVProxy output endpoint for repo smoke-test clients. Use an empty value to disable.",
        ),
    ] = DEFAULT_MAVLINK_OUT,
    extra_args: Annotated[
        list[str] | None,
        typer.Argument(help="Extra arguments passed to sim_vehicle.py."),
    ] = None,
) -> None:
    """Create or use an ArduPilot checkout and run SITL."""
    repo_path = resolve_ardupilot_repo(ardupilot_repo)
    ensure_checkout(repo_path, clone_if_missing=clone)

    if install_prereqs:
        install_prerequisites(repo_path)

    if setup_only:
        typer.echo(f"ArduPilot checkout is ready: {repo_path}")
        return

    command = build_sim_vehicle_command(
        repo_path,
        vehicle=vehicle,
        wipe=wipe,
        mavlink_out=mavlink_out,
        map_window=map_window,
        console=console,
        extra_args=extra_args,
    )
    typer.echo(f"Starting {VEHICLE_TARGETS[vehicle]} SITL from {repo_path}")
    subprocess.run(command, cwd=repo_path, check=True, env=external_tool_env())


app = typer.Typer()
app.command()(main)


if __name__ == "__main__":
    app()
