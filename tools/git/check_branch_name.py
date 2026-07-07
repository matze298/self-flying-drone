"""Pre-commit hook that checks local work branch names."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys

ALLOWED_PREFIXES = ("feature", "fix", "cleanup", "docs", "test", "ci", "deps", "release", "spike")
SKIPPED_BRANCH_NAMES = frozenset(("", "main", "master", "develop"))
SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*(/[a-z0-9][a-z0-9._-]*)*$")


def current_branch_name() -> str:
    """Return the current git branch name, or an empty string for detached HEAD."""
    git_path = shutil.which("git")
    if git_path is None:
        message = "Could not find the git executable."
        raise RuntimeError(message)

    completed_process = subprocess.run(  # noqa: S603 - fixed git args read local branch state for this hook.
        [git_path, "branch", "--show-current"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed_process.stdout.strip()


def validate_branch_name(branch_name: str) -> str | None:
    """Return a validation error when a work branch does not follow the project strategy."""
    if branch_name in SKIPPED_BRANCH_NAMES:
        return None

    prefix, separator, slug = branch_name.partition("/")
    if separator != "/" or prefix not in ALLOWED_PREFIXES or not SLUG_PATTERN.fullmatch(slug):
        prefixes = ", ".join(f"{allowed_prefix}/" for allowed_prefix in ALLOWED_PREFIXES)
        return (
            f"Branch name '{branch_name}' does not follow the project branch strategy. "
            f"Use one of: {prefixes} followed by a lowercase slug."
        )

    return None


def main(argv: list[str] | None = None) -> int:
    """Check the current branch name."""
    argv = argv if argv is not None else sys.argv[1:]
    branch_name = argv[0] if argv else current_branch_name()
    message = validate_branch_name(branch_name)
    if message is None:
        return 0

    sys.stderr.write(f"{message}\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
