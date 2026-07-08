#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "typer>=0.20.0",
# ]
# ///
"""Project setup helper for uv-managed local development."""

from __future__ import annotations

import pathlib
import subprocess
from typing import TYPE_CHECKING

import typer

if TYPE_CHECKING:
    from collections.abc import Sequence


PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_VENV = PROJECT_ROOT / ".venv"
DEFAULT_WORKSTREAMS = ("docs",)
ALL_WORKSTREAMS = ("docs", "python", "sim", "rust", "ros", "jetson")
WORKSTREAM_GROUPS = {
    "docs": ("docs",),
    "python": ("dev",),
    "sim": ("sim",),
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


def report_workstream_notes(workstreams: Sequence[str]) -> None:
    """Print setup notes for workstreams that need external tools."""
    if "sim" not in workstreams:
        return

    typer.echo("Simulation Python tools are installed.")
    typer.echo("ArduPilot SITL is an external checkout with system dependencies; follow the docs workflow.")


def sync_command(workstreams: Sequence[str]) -> list[str]:
    """Build the uv sync command for the requested dependency groups."""
    command = ["uv", "sync"]
    if "sim" in workstreams:
        command.append("--all-packages")
    dependency_groups = dict.fromkeys(group for name in workstreams for group in WORKSTREAM_GROUPS[name])
    for group in dependency_groups:
        command.extend(["--group", group])
    return command


def setup(
    workstream: list[str] | None = typer.Option(
        None,
        "--workstream",
        "-w",
        help=(
            "Development workstream to set up: docs, python, sim, rust, ros, or jetson. "
            "Repeat for multiple workstreams."
        ),
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
) -> None:
    """Create/update the uv venv and return to the caller."""
    try:
        selected_workstreams = normalize_workstreams(
            workstream,
            include_docs=docs,
            include_all=all_workstreams,
        )
    except NotImplementedError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error

    subprocess.run(
        sync_command(selected_workstreams),
        cwd=PROJECT_ROOT,
        check=True,
    )

    report_workstream_notes(selected_workstreams)

    typer.echo(f"Virtual environment is ready: {PROJECT_VENV}")


if __name__ == "__main__":
    typer.run(setup)
