"""Tests for project package metadata."""

from __future__ import annotations

import pathlib
import tomllib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SITL_ROOT = PROJECT_ROOT / "sitl"


def test_root_project_declares_sitl_workspace_member() -> None:
    """The root project should orchestrate the SITL package through a uv workspace."""
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["tool"]["uv"]["package"] is False
    assert pyproject["tool"]["uv"]["workspace"]["members"] == ["sitl"]


def test_sitl_package_owns_cli_entry_points_and_runtime_dependencies() -> None:
    """The SITL package should own its Python package metadata and command scripts."""
    pyproject = tomllib.loads((SITL_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["name"] == "sitl"
    assert pyproject["tool"]["uv"]["package"] is True
    assert pyproject["project"]["scripts"] == {
        "sitl-flight-check": "sitl.flight_check:app",
        "sitl-run": "sitl.run:app",
        "sitl-smoke-test": "sitl.smoke_test:app",
    }
    assert set(pyproject["project"]["dependencies"]) == {
        "orjson>=3.11.9",
        "pymavlink>=2.4.49",
        "typer>=0.20.0",
    }
    assert set(pyproject["dependency-groups"]["sim"]) == {
        "aioconsole>=0.8.2",
        "mavsdk>=3.15.3",
    }
