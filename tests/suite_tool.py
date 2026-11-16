"""A stand-in for a project's test commands, used by Suites in the baseline tests.

Each call counts its runs in a state file, so a test can fail on run 1 and pass on
run 2 without randomness. Usage (STATE is a file outside the worktree):

    exit N                         exit with code N
    seq STATE C1 C2 ...            exit with C1 on the first call, C2 on the second, ...
    junit STATE [--exit N] T=OUT.. write target/surefire-reports/TEST-T.xml; OUT has one
                                   letter per run: p pass, f fail, s skip; exit 1 when a
                                   test failed (or N)
    serve PIDFILE PORT [--die]     a service with one child process; writes both pids
    probe PORT                     exit 0 when PORT accepts a connection
    record FILE TEXT               append "TEXT <cwd>" to FILE
    sleep S                        sleep S seconds
"""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path


def _count(state: str) -> int:
    path = Path(state)
    n = int(path.read_text()) if path.exists() else 0
    path.write_text(str(n + 1))
    return n


def _junit(state: str, args: list[str]) -> int:
    code = None
    if args[:1] == ["--exit"]:
        code, args = int(args[1]), args[2:]
    n = _count(state)
    failed = False
    cases = []
    for spec in args:
        test, outcomes = spec.split("=")
        outcome = outcomes[min(n, len(outcomes) - 1)]
        inner = {"p": "", "f": '<failure message="boom"/>', "s": "<skipped/>"}[outcome]
        failed = failed or outcome == "f"
        cases.append(f'<testcase classname="shop.T" name="{test}">{inner}</testcase>')
    out = Path("target/surefire-reports")
    out.mkdir(parents=True, exist_ok=True)
    (out / "TEST-shop.T.xml").write_text(f"<testsuite>{''.join(cases)}</testsuite>")
    print(f"run {n + 1}: {'FAILED' if failed else 'ok'}")
    return code if code is not None else int(failed)


def _serve(pidfile: str, port: int, die: bool) -> int:
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
    Path(pidfile).write_text(f"{os.getpid()} {child.pid}\n")
    if die:
        return 1
    with socket.socket() as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", port))
        sock.listen()
        while True:
            conn, _ = sock.accept()
            conn.close()


def _probe(port: int) -> int:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return 0
    except OSError:
        return 1


def main(argv: list[str]) -> int:
    cmd, args = argv[0], argv[1:]
    if cmd == "exit":
        print(f"exit {args[0]}")
        return int(args[0])
    if cmd == "seq":
        n = _count(args[0])
        codes = args[1:]
        code = int(codes[min(n, len(codes) - 1)])
        print(f"run {n + 1}: exit {code}")
        return code
    if cmd == "junit":
        return _junit(args[0], args[1:])
    if cmd == "serve":
        return _serve(args[0], int(args[1]), "--die" in args)
    if cmd == "probe":
        return _probe(int(args[0]))
    if cmd == "record":
        with open(args[0], "a") as out:
            out.write(f"{args[1]} {os.getcwd()}\n")
        return 0
    if cmd == "sleep":
        time.sleep(float(args[0]))
        return 0
    raise SystemExit(f"unknown command {cmd}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
