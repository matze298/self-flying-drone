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
    from collections.abc import Mapping


PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_VENV = PROJECT_ROOT / ".venv"
VENV_BIN = PROJECT_VENV / "bin"
VENV_PYTHON = VENV_BIN / "python"


def sync_command(*, include_docs: bool = True) -> list[str]:
    """Build the uv sync command for the requested dependency groups."""
    command = ["uv", "sync"]
    if include_docs:
        command.extend(["--group", "docs"])
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
    docs: bool = typer.Option(
        True,
        "--docs/--no-docs",
        help="Install the documentation dependency group.",
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
    if not skip_sync:
        subprocess.run(
            sync_command(include_docs=docs),
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
