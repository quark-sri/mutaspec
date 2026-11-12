"""The git facts mutaspec needs about the project root."""

import subprocess
from pathlib import Path

from mutaspec.errors import ENVIRONMENT, MutaspecError

GIT = "git"

NEEDS_GIT = "mutaspec needs a git repository."


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run([GIT, *args], cwd=cwd, capture_output=True, text=True)
    except FileNotFoundError:
        raise MutaspecError(
            ENVIRONMENT, f"{NEEDS_GIT} git not found.", hint="Install git and try again."
        ) from None


def require_work_tree(root: Path) -> None:
    """Stop unless `root` is inside a git work tree (spec AC10)."""
    result = _git(root, "rev-parse", "--is-inside-work-tree")
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise MutaspecError(
            ENVIRONMENT,
            NEEDS_GIT,
            where=str(root),
            hint="Run mutaspec inside a git repository (git init).",
        )


def list_files(root: Path) -> list[str]:
    """Tracked and untracked, not ignored files under `root`, as POSIX paths relative to it."""
    result = _git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z", ".")
    if result.returncode != 0:
        raise MutaspecError(
            ENVIRONMENT,
            f"git ls-files failed: {result.stderr.strip()}",
            where=str(root),
            hint="Check that 'git status' works in this folder.",
        )
    return sorted({p for p in result.stdout.split("\0") if p})
