"""Ctrl-C during a baseline (spec 0002 AC12, AC15, SC3; D40, D44).

mutaspec runs as a real process here, so SIGINT arrives the way Ctrl-C sends it.
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest
from conftest import git, tool
from test_baseline import RESULT, all_gone, started_pids, suite

INTERRUPTED = 130


def wait_for(path: Path, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while not (path.exists() and path.read_text().strip()):
        assert time.monotonic() < deadline, f"{path.name} was never written"
        time.sleep(0.05)


def user_state(root: Path) -> tuple[str, str, str]:
    return (
        git(root, "rev-parse", "HEAD"),
        git(root, "branch", "--show-current"),
        git(root, "status", "--porcelain"),
    )


def start_mutaspec(root: Path) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-m", "mutaspec", "baseline"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def service(tmp_path: Path, kind: str) -> dict:
    """A Suite with a service; `kind` says where the run is when it ends."""
    marks = tmp_path / "marks"
    ready = {
        "in_run": tool("probe", "{port}"),
        "in_ready": f"{tool('record', marks, 'ready')}; exit 1",
        "ready_timeout": tool("exit", 1),
    }[kind]
    run = f"{tool('record', marks, 'run')} && {tool('sleep', 30)}"
    return suite(
        "api",
        run,
        level="api",
        start=tool("serve", tmp_path / "pids", "{port}"),
        ready=ready,
        ready_timeout="1s" if kind == "ready_timeout" else "30s",
        teardown=tool("record", tmp_path / "teardown", "teardown"),
    )


def interrupt_or_wait(proc: subprocess.Popen, tmp_path: Path, kind: str) -> int:
    if kind != "ready_timeout":
        wait_for(tmp_path / "marks")
        os.kill(proc.pid, signal.SIGINT)
    proc.communicate(timeout=60)
    return proc.returncode


def test_ac12_ctrl_c_stops_processes_runs_teardown_and_exits_130(make_project, tmp_path):
    root = make_project(service(tmp_path, "in_run"))
    before = user_state(root)
    proc = start_mutaspec(root)

    code = interrupt_or_wait(proc, tmp_path, "in_run")

    assert code == INTERRUPTED
    assert all_gone(started_pids(tmp_path / "pids"))
    assert (tmp_path / "teardown").read_text().count("teardown") == 1
    assert not (root / RESULT).exists()  # D40
    assert user_state(root) == before  # AC15


def test_ac12_ctrl_c_while_waiting_for_ready(make_project, tmp_path):
    root = make_project(service(tmp_path, "in_ready"))
    proc = start_mutaspec(root)

    code = interrupt_or_wait(proc, tmp_path, "in_ready")

    assert code == INTERRUPTED
    assert all_gone(started_pids(tmp_path / "pids"))
    assert (tmp_path / "teardown").exists()


@pytest.mark.slow
def test_sc3_twenty_runs_with_ctrl_c_and_ready_timeouts_leave_nothing_behind(
    make_project, tmp_path
):
    kinds = ["in_run", "in_ready", "ready_timeout"]
    pids: list[int] = []

    for i in range(20):
        kind = kinds[i % 3]
        work = tmp_path / f"round{i}"
        work.mkdir()
        root = make_project(service(work, kind))
        before = user_state(root)

        proc = start_mutaspec(root)
        code = interrupt_or_wait(proc, work, kind)

        assert code == (3 if kind == "ready_timeout" else INTERRUPTED), proc.stderr
        assert (work / "teardown").exists()
        assert user_state(root) == before
        pids += started_pids(work / "pids")

    assert all_gone(pids)
