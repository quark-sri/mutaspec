"""Suite commands in their own process group (spec 0002 FR3, FR9, FR10, AC13, AC14; D44)."""

import os
import socket
import sys
import time

from mutaspec import process


def gone(pid: int, wait: float = 3.0) -> bool:
    deadline = time.monotonic() + wait
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.05)
    return False


def test_run_gives_exit_code_and_keeps_output_in_the_log(tmp_path):
    log = tmp_path / "x.log"

    done = process.run("echo hello; echo oops >&2; exit 4", tmp_path, log)

    assert done.code == 4
    assert not done.timed_out
    assert "hello" in log.read_text()
    assert "oops" in log.read_text()


def test_run_uses_the_given_folder(tmp_path):
    log = tmp_path / "x.log"
    (tmp_path / "work").mkdir()

    process.run("pwd", tmp_path / "work", log)

    assert str((tmp_path / "work").resolve()) in log.read_text()


def test_ac14_run_longer_than_timeout_is_stopped(tmp_path):
    started = time.monotonic()

    done = process.run("sleep 30", tmp_path, tmp_path / "x.log", timeout=0.3)

    assert done.timed_out
    assert time.monotonic() - started < 5


def test_timeout_stops_child_processes_too(tmp_path):
    pidfile = tmp_path / "child.pid"

    process.run(f"sleep 30 & echo $! > {pidfile}; wait", tmp_path, tmp_path / "x.log", timeout=0.5)

    assert gone(int(pidfile.read_text()))


def test_stop_ends_the_whole_process_group(tmp_path):
    pidfile = tmp_path / "child.pid"
    proc = process.spawn(f"sleep 30 & echo $! > {pidfile}; wait", tmp_path, tmp_path / "x.log")
    while not pidfile.exists() or not pidfile.read_text().strip():
        time.sleep(0.02)

    process.stop(proc)

    assert gone(proc.pid)
    assert gone(int(pidfile.read_text()))


def test_stop_kills_a_process_that_ignores_sigterm(tmp_path, monkeypatch):
    monkeypatch.setattr(process, "STOP_GRACE", 0.3)
    ready = tmp_path / "ready"
    script = tmp_path / "stubborn.py"
    script.write_text(
        "import signal, time, pathlib\n"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        f"pathlib.Path({str(ready)!r}).write_text('1')\n"
        "time.sleep(30)\n"
    )
    proc = process.spawn(f"exec {sys.executable} {script}", tmp_path, tmp_path / "x.log")
    while not ready.exists():
        time.sleep(0.02)

    started = time.monotonic()
    process.stop(proc)

    assert gone(proc.pid)
    assert time.monotonic() - started < 3


def test_ac13_free_port_can_be_bound():
    port = process.free_port()

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", port))


def test_ac13_only_the_port_placeholder_is_replaced():
    assert process.with_port("serve --port={port} ${HOME} {other}", 8123) == (
        "serve --port=8123 ${HOME} {other}"
    )


def test_fr9_tail_shows_the_last_20_lines(tmp_path):
    log = tmp_path / "x.log"
    log.write_text("".join(f"line {i}\n" for i in range(30)))

    text = process.tail(log)

    assert text.splitlines() == [f"line {i}" for i in range(10, 30)]


def test_fr9_tail_of_a_missing_log_is_empty(tmp_path):
    assert process.tail(tmp_path / "none.log") == ""


def test_d44_ctrl_c_while_stopping_is_ignored(tmp_path):
    import signal

    with process.no_interrupts():
        os.kill(os.getpid(), signal.SIGINT)  # would raise KeyboardInterrupt outside
        time.sleep(0.1)

    assert signal.getsignal(signal.SIGINT) is signal.default_int_handler
