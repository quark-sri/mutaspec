import json
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from mutaspec.cli import main

REPO_ROOT = Path(__file__).resolve().parent.parent
SHOP = REPO_ROOT / "examples" / "shop"


@dataclass
class Result:
    code: int
    out: str
    err: str

    def json(self) -> dict:
        return json.loads(self.out)


@pytest.fixture
def run_cli(capsys, monkeypatch):
    """Run mutaspec in-process in a directory; return exit code and output."""

    def _run(cwd: Path, *argv: str) -> Result:
        monkeypatch.chdir(cwd)
        code = main(list(argv))
        captured = capsys.readouterr()
        return Result(code, captured.out, captured.err)

    return _run


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


def commit_all(repo: Path) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "--allow-empty", "-m", "fixture")


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """An empty git repo with one commit."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "test")
    commit_all(repo)
    return repo


def write(root: Path, rel: str, text: str = "") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


@pytest.fixture
def shop_repo(git_repo: Path) -> Path:
    """A copy of examples/shop, without its golden mutaspec.toml, in its own git repo."""
    shutil.copytree(
        SHOP,
        git_repo,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("target", ".mutaspec", "mutaspec.toml"),
    )
    commit_all(git_repo)
    return git_repo


TOOL = Path(__file__).with_name("suite_tool.py")


def tool(*args: object) -> str:
    """A shell command that runs tests/suite_tool.py (no Java needed)."""
    return shlex.join([sys.executable, str(TOOL), *map(str, args)])


def _toml(value: object) -> str:
    return json.dumps(value) if isinstance(value, str) else str(value).lower()


@pytest.fixture
def make_project(git_repo: Path):
    """Write and commit a project whose Suites are given as dicts; return its root."""

    def _make(*suites: dict, project: str = "") -> Path:
        lines = ["[project]", 'source = ["src/**"]', 'tests = ["tests/**"]', project]
        for suite in suites:
            lines += ["", "[[suites]]"]
            lines += [f"{key} = {_toml(value)}" for key, value in suite.items()]
        write(git_repo, "mutaspec.toml", "\n".join(lines) + "\n")
        write(git_repo, "src/app.txt", "app\n")
        write(git_repo, "tests/app_test.txt", "test\n")
        commit_all(git_repo)
        return git_repo

    return _make
