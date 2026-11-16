"""The Baseline worktree: a clean checkout of the `baseline` ref (spec 0002 FR2, AC15-AC18).

Suites never run in the user's working tree. Git commands here only read the user's
repository, or add and remove worktrees under `.mutaspec/worktrees/`.
"""

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from mutaspec import gitrepo
from mutaspec.config import Config
from mutaspec.errors import ENVIRONMENT, USAGE, MutaspecError

BASE = Path(".mutaspec") / "worktrees" / "base"
# mutaspec's own output is never a user change (D43).
_OWN = (".mutaspec/worktrees/", ".mutaspec/runs/")
SHOWN = 10


@dataclass(frozen=True)
class Base:
    path: Path  # the worktree folder (top of the repository copy)
    project_dir: Path  # the project root inside it; Suites run here (D37)
    ref: str
    commit: str
    uncommitted: bool
    left_out: list[str] = field(default_factory=list)  # uncommitted files not used (AC16)


def _git(cwd: Path, *args: str, what: str) -> str:
    result = gitrepo._git(cwd, *args)
    if result.returncode != 0:
        raise MutaspecError(
            ENVIRONMENT,
            f"{what} failed: {result.stderr.strip()}",
            where=str(cwd),
            hint="Check that 'git status' works in this folder.",
        )
    return result.stdout


def _resolve(root: Path, ref: str) -> str:
    result = gitrepo._git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    if result.returncode != 0:
        raise MutaspecError(
            USAGE,
            f"the baseline ref {ref!r} does not exist.",
            where="mutaspec.toml, [project], field 'baseline'",
            hint='Use a branch, tag or commit of this repository, for example "HEAD".',
        )
    return result.stdout.strip()


def uncommitted_files(root: Path) -> list[str]:
    """Tracked files changed since HEAD and untracked, not ignored files, under `root` (D43)."""
    changed = _git(
        root, "diff", "--name-only", "--relative", "-z", "HEAD", "--", ".", what="git diff"
    )
    untracked = _git(
        root, "ls-files", "--others", "--exclude-standard", "-z", "--", ".", what="git ls-files"
    )
    paths = {p for p in (changed + untracked).split("\0") if p}
    return sorted(p for p in paths if not p.startswith(_OWN))


def left_out_warning(files: list[str]) -> str:
    """AC16: name the first 10 left-out files, then 'and N more'."""
    more = f", and {len(files) - SHOWN} more" if len(files) > SHOWN else ""
    return (
        f"warning: {len(files)} uncommitted file(s) are not used: "
        f"{', '.join(files[:SHOWN])}{more}. "
        "Commit them, or run with --include-uncommitted."
    )


def own_folder(path: Path) -> Path:
    """Create a mutaspec output folder that git always ignores, with or without init (D46).

    A `.gitignore` of `*` ignores the folder and itself, so `git status` never changes (AC15).
    """
    path.mkdir(parents=True, exist_ok=True)
    marker = path / ".gitignore"
    if not marker.exists():
        marker.write_text("# Written by mutaspec. Everything here is temporary.\n*\n")
    return path


def _remove(root: Path, path: Path) -> None:
    if path.exists():
        result = gitrepo._git(root, "worktree", "remove", "--force", str(path))
        if result.returncode != 0 and path.exists():
            shutil.rmtree(path)
    gitrepo._git(root, "worktree", "prune")


def _copy_uncommitted(root: Path, project_dir: Path, files: list[str]) -> None:
    for rel in files:
        src, dst = root / rel, project_dir / rel
        if src.is_symlink() or src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.is_symlink() or dst.exists():
                dst.unlink()
            shutil.copy2(src, dst, follow_symlinks=False)
        elif dst.is_symlink() or dst.exists():
            dst.unlink()


def create_base(config: Config, include_uncommitted: bool) -> Base:
    """Create `.mutaspec/worktrees/base` again at the `baseline` ref (FR2, D25)."""
    root = config.root.resolve()
    ref = config.project.baseline
    commit = _resolve(root, ref)
    if include_uncommitted and commit != _resolve(root, "HEAD"):
        raise MutaspecError(
            USAGE,
            f"--include-uncommitted needs the baseline ref to be HEAD, not {ref!r}.",
            where="mutaspec.toml, [project], field 'baseline'",
            hint='Uncommitted changes sit on HEAD. Drop the flag, or set baseline = "HEAD".',
        )

    top = Path(_git(root, "rev-parse", "--show-toplevel", what="git rev-parse").strip())
    path = root / BASE
    _remove(root, path)
    own_folder(path.parent)
    _git(root, "worktree", "add", "--detach", "--quiet", str(path), commit, what="git worktree add")
    project_dir = path / root.relative_to(top.resolve())

    files = uncommitted_files(root)
    if include_uncommitted:
        _copy_uncommitted(root, project_dir, files)
        return Base(path, project_dir, ref, commit, uncommitted=True)
    return Base(path, project_dir, ref, commit, uncommitted=False, left_out=files)
