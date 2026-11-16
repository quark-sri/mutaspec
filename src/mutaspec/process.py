"""Run Suite commands through the shell, each in its own process group (spec 0002 FR3; D44).

A process group lets mutaspec stop a command together with every child it started
(Maven forks, `java -jar`, browsers). Ctrl-C in the terminal reaches only mutaspec,
which then stops the groups itself.
"""

import contextlib
import os
import signal
import socket
import subprocess
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

STOP_GRACE = 10.0  # seconds between SIGTERM and SIGKILL (D31)
TAIL_LINES = 20


@dataclass(frozen=True)
class Finished:
    code: int | None  # None when stopped for the timeout
    seconds: float
    timed_out: bool


def free_port() -> int:
    """FR10: a free TCP port, found by binding to port 0 and closing it again."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def with_port(command: str, port: int | None) -> str:
    """Replace the literal `{port}` only; `${VAR}` and other braces stay as written (D41)."""
    return command if port is None else command.replace("{port}", str(port))


def spawn(command: str, cwd: Path, log: Path) -> subprocess.Popen:
    """Start `command` in the background in a new process group; output goes to `log`."""
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("ab") as out:
        out.write(f"$ {command}\n".encode())
        out.flush()
        return subprocess.Popen(
            ["/bin/sh", "-c", command],
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )


_guard = threading.local()


@contextlib.contextmanager
def no_interrupts() -> Iterator[None]:
    """D44: Ctrl-C waits until stopping processes or `teardown` ends, then takes effect.

    A Ctrl-C that arrives inside the block is saved, not dropped: when the outermost
    block ends, KeyboardInterrupt is raised as if Ctrl-C came just then.
    """
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    depth = getattr(_guard, "depth", 0)
    if depth == 0:
        _guard.pending = False
        _guard.old = signal.signal(signal.SIGINT, _save_interrupt)
    _guard.depth = depth + 1
    try:
        yield
    finally:
        _guard.depth = depth
        if depth == 0:
            signal.signal(signal.SIGINT, _guard.old)
            if _guard.pending:
                _guard.pending = False
                raise KeyboardInterrupt


def _save_interrupt(signum: int, frame: object) -> None:
    _guard.pending = True


def _group_alive(proc: subprocess.Popen) -> bool:
    proc.poll()  # reap the leader, so a finished leader does not count
    try:
        os.killpg(proc.pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _signal_group(proc: subprocess.Popen, sig: int) -> None:
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(proc.pid, sig)


def stop(proc: subprocess.Popen) -> None:
    """Stop the process group: SIGTERM, then SIGKILL after STOP_GRACE seconds (FR3)."""
    with no_interrupts():
        if _group_alive(proc):
            _signal_group(proc, signal.SIGTERM)
            deadline = time.monotonic() + STOP_GRACE
            while _group_alive(proc) and time.monotonic() < deadline:
                time.sleep(0.05)
            if _group_alive(proc):
                _signal_group(proc, signal.SIGKILL)
        proc.wait()


def run(command: str, cwd: Path, log: Path, timeout: float | None = None) -> Finished:
    """Run `command` to its end, or stop it after `timeout` seconds (AC14).

    Child processes left behind by the command are stopped too.
    """
    started = time.monotonic()
    proc = spawn(command, cwd, log)
    try:
        code = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        stop(proc)
        return Finished(None, time.monotonic() - started, timed_out=True)
    finally:
        stop(proc)  # also on Ctrl-C (KeyboardInterrupt)
    return Finished(code, time.monotonic() - started, timed_out=False)


def tail(log: Path, lines: int = TAIL_LINES) -> str:
    """FR9: the last lines of a log, for error messages."""
    try:
        text = log.read_text(errors="replace")
    except FileNotFoundError:
        return ""
    return "\n".join(text.splitlines()[-lines:])
