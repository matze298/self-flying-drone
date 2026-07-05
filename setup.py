#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "typer>=0.20.0",
# ]
# ///
"""Project setup helper for uv-managed local development."""

from __future__ import annotations

import os
import pathlib
import subprocess
from typing import TYPE_CHECKING

import typer

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_VENV = PROJECT_ROOT / ".venv"
VENV_BIN = PROJECT_VENV / "bin"
VENV_PYTHON = VENV_BIN / "python"
DEFAULT_WORKSTREAMS = ("docs",)
ALL_WORKSTREAMS = ("docs", "python", "rust", "ros", "jetson")
WORKSTREAM_GROUPS = {
    "docs": ("docs",),
    "python": ("dev",),
    "rust": (),
    "ros": (),
    "jetson": (),
}
UNIMPLEMENTED_WORKSTREAMS = {
    "rust": "Rust services will use Cargo/rustup, but no Rust workspace exists yet.",
    "ros": "ROS 2 work will use Ubuntu 24.04, ROS 2 Jazzy, colcon, and CMake; no ROS workspace exists yet.",
    "jetson": "Jetson deployment will use JetPack 7 and NVIDIA containers; no target setup exists yet.",
}


def normalize_workstreams(
    requested_workstreams: Sequence[str] | None,
    *,
    include_docs: bool,
    include_all: bool,
) -> list[str]:
    """Return validated workstream names in setup order."""
    workstreams = list(ALL_WORKSTREAMS if include_all else requested_workstreams or ())
    if not workstreams and include_docs:
        workstreams.extend(DEFAULT_WORKSTREAMS)

    unknown_workstreams = sorted({name for name in workstreams if name not in WORKSTREAM_GROUPS})
    if unknown_workstreams:
        known_workstreams = ", ".join(ALL_WORKSTREAMS)
        unknown = ", ".join(unknown_workstreams)
        message = f"Unknown workstream(s): {unknown}. Known workstreams: {known_workstreams}."
        raise typer.BadParameter(message)

    unimplemented = [name for name in workstreams if name in UNIMPLEMENTED_WORKSTREAMS]
    if unimplemented:
        details = "\n".join(f"- {name}: {UNIMPLEMENTED_WORKSTREAMS[name]}" for name in unimplemented)
        message = f"Workstream setup is not implemented yet:\n{details}"
        raise NotImplementedError(message)

    return list(dict.fromkeys(workstreams))


def sync_command(workstreams: Sequence[str]) -> list[str]:
    """Build the uv sync command for the requested dependency groups."""
    command = ["uv", "sync"]
    dependency_groups = dict.fromkeys(group for name in workstreams for group in WORKSTREAM_GROUPS[name])
    for group in dependency_groups:
        command.extend(["--group", group])
    return command


def is_project_venv_active(
    env: Mapping[str, str] | None = None,
) -> bool:
    """Return whether the current shell has the project venv active."""
    env = env or os.environ
    active_venv = env.get("VIRTUAL_ENV")
    if not active_venv:
        return False

    return pathlib.Path(active_venv).resolve() == PROJECT_VENV.resolve()


def activate_shell() -> None:
    """Replace this process with an interactive shell inside the project venv."""
    if is_project_venv_active():
        typer.echo(f"Virtual environment is already active: {PROJECT_VENV}")
        return

    shell = os.environ.get("SHELL", "/bin/bash")
    env = os.environ.copy()
    env["VIRTUAL_ENV"] = os.fspath(PROJECT_VENV)
    env["PATH"] = f"{VENV_BIN}{os.pathsep}{env.get('PATH', '')}"
    env.pop("PYTHONHOME", None)

    typer.echo(f"Entering virtual environment: {PROJECT_VENV}")
    typer.echo("Run `exit` to return to your previous shell.")
    os.execvpe(shell, [shell, "-i"], env)


def setup(
    workstream: list[str] | None = typer.Option(
        None,
        "--workstream",
        "-w",
        help="Development workstream to set up: docs, python, rust, ros, or jetson. Repeat for multiple workstreams.",
    ),
    docs: bool = typer.Option(
        True,
        "--docs/--no-docs",
        help="Include the documentation workstream when no explicit workstream is selected.",
    ),
    all_workstreams: bool = typer.Option(
        False,
        "--all-workstreams",
        help="Set up every known workstream. Unimplemented workstreams fail clearly.",
    ),
    skip_sync: bool = typer.Option(
        False,
        "--skip-sync",
        help="Only report venv activation status.",
    ),
    shell: bool = typer.Option(
        True,
        "--shell/--no-shell",
        help="Open an interactive shell inside the project virtual environment.",
    ),
) -> None:
    """Create/update the uv venv and enter it by default."""
    try:
        selected_workstreams = normalize_workstreams(
            workstream,
            include_docs=docs,
            include_all=all_workstreams,
        )
    except NotImplementedError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error

    if not skip_sync:
        subprocess.run(
            sync_command(selected_workstreams),
            cwd=PROJECT_ROOT,
            check=True,
        )

    if shell:
        activate_shell()
        return

    if is_project_venv_active():
        typer.echo(f"Virtual environment is active: {PROJECT_VENV}")
        return

    typer.echo(f"Virtual environment is ready: {PROJECT_VENV}")


if __name__ == "__main__":
    typer.run(setup)
