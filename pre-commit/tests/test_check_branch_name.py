"""Tests for the branch-name pre-commit hook."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pre_commit import check_branch_name

if TYPE_CHECKING:
    from types import ModuleType


@pytest.fixture
def hook() -> ModuleType:
    """Return the packaged branch-name hook module."""
    return check_branch_name


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
