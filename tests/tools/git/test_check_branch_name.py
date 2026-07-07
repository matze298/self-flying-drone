"""Tests for the branch-name pre-commit hook."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
HOOK_PATH = PROJECT_ROOT / "tools" / "git" / "check_branch_name.py"


@pytest.fixture
def hook() -> ModuleType:
    """Load the standalone branch-name hook as a test module."""
    spec = importlib.util.spec_from_file_location("check_branch_name", HOOK_PATH)
    if spec is None or spec.loader is None:
        pytest.fail("Could not load branch-name hook module.")

    module = importlib.util.module_from_spec(spec)
    sys.modules["check_branch_name"] = module
    previous_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous_dont_write_bytecode
    return module


@pytest.mark.parametrize(
    "branch_name",
    [
        "feature/branch-naming-policy",
        "fix/setup-error-message",
        "cleanup/remove-dead-helper",
        "docs/update-buyer-guide",
        "test/add-sitl-smoke-coverage",
        "ci/update-prek-hooks",
        "deps/weekly-uv-refresh",
        "release/v0.2.0",
        "spike/sitl-command-options",
    ],
)
def test_allows_documented_work_branch_prefixes(hook: ModuleType, branch_name: str) -> None:
    """Documented work branch prefixes should be accepted."""
    assert hook.validate_branch_name(branch_name) is None


@pytest.mark.parametrize("branch_name", ["main", "master", "develop", ""])
def test_skips_non_work_branch_states(hook: ModuleType, branch_name: str) -> None:
    """Default branches and detached HEAD should be left to other checks."""
    assert hook.validate_branch_name(branch_name) is None


@pytest.mark.parametrize(
    "branch_name",
    [
        "codex/branch-naming-policy",
        "agent/branch-naming-policy",
        "branch-naming-policy",
        "feature/",
        "Feature/branch-naming-policy",
        "feature/branch naming policy",
    ],
)
def test_rejects_undocumented_or_malformed_work_branch_names(hook: ModuleType, branch_name: str) -> None:
    """Undocumented prefixes and malformed slugs should be rejected."""
    message = hook.validate_branch_name(branch_name)

    assert message is not None
    assert branch_name in message
