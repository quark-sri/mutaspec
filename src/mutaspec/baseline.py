"""`mutaspec baseline`: run every Suite on the clean Baseline, `repeat` times (spec 0002).

The Baseline result says "ready" or "not ready", each Suite `ok` or `broken` with a reason,
and is written to `.mutaspec/runs/baseline.json` for later intents (FR8).
"""

import json
import shutil
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from mutaspec import junit, process, worktree
from mutaspec.config import Config, Suite
from mutaspec.errors import ENVIRONMENT, OK

RUNS = Path(".mutaspec") / "runs"
RESULT_FILE = RUNS / "baseline.json"
LOGS = RUNS / "baseline"

OK_STATUS, BROKEN = "ok", "broken"
READY_POLL = 1.0  # seconds between `ready` checks (D31)


@dataclass
class SuiteResult:
    name: str
    level: str
    status: str = OK_STATUS
    reason: str | None = None
    hint: str | None = None
    durations: list[float] = field(default_factory=list)
    log: str | None = None  # the log to read for `reason`
    tail: str = ""
    warnings: list[str] = field(default_factory=list)
    tests: dict[str, str] | None = None  # only when the Suite has `junit` (FR8)

    def excluded(self, status: str) -> list[str]:
        return [t for t, s in (self.tests or {}).items() if s == status]

    def to_json(self) -> dict:
        data = {
            "name": self.name,
            "level": self.level,
            "status": self.status,
            "reason": self.reason,
            "hint": self.hint,
            "durations": [round(d, 3) for d in self.durations],
            "log": self.log,
            "warnings": self.warnings,
        }
        if self.tests is not None:
            data["tests"] = self.tests
        return data


class _Broken(Exception):
    def __init__(self, reason: str, log: Path | None = None, hint: str | None = None):
        super().__init__(reason)
        self.reason, self.log, self.hint = reason, log, hint


def seconds(value: float) -> str:
    return f"{value:g}s"


class _SuiteRun:
    """FR3: setup once, then each repeat, then teardown (always)."""

    def __init__(self, suite: Suite, cwd: Path, logs: Path, root: Path, judge: bool = True):
        self.suite, self.cwd, self.logs, self.root = suite, cwd, logs, root
        self.judge = judge  # False for a Mutant run: failures are the point there
        self.timed_out = False
        self.result = SuiteResult(suite.name, suite.level)
        self.codes: list[int] = []
        self.last_log: Path | None = None
        self.test_runs: list[dict[str, str]] = []
        if suite.junit is not None:
            self.result.tests = {}

    def _log(self, part: str) -> Path:
        return self.logs / f"{self.suite.name}-{part}.log"

    def _rel(self, path: Path) -> str:
        return str(path.relative_to(self.root))

    def run(self) -> SuiteResult:
        try:
            try:
                self._setup()
                for n in range(1, self.suite.repeat + 1):
                    self._repeat(n)
                if self.judge:
                    self._judge()
            finally:
                with process.no_interrupts():
                    self._teardown()
        except _Broken as broken:
            self.result.status = BROKEN
            self.result.reason = broken.reason
            self.result.hint = broken.hint
            if broken.log is not None:
                self.result.log = self._rel(broken.log)
                self.result.tail = process.tail(broken.log)
        return self.result

    def _setup(self) -> None:
        if self.suite.setup is None:
            return
        log = self._log("setup")
        done = process.run(self.suite.setup, self.cwd, log, timeout=self.suite.timeout)
        if done.timed_out or done.code != 0:
            raise _Broken("setup failed", log)

    def _repeat(self, n: int) -> None:
        suite, log = self.suite, self._log(str(n))
        if suite.junit is not None:
            junit.clear(self.cwd, suite.junit)  # D29
        commands = (suite.start, suite.ready, suite.run)
        port = process.free_port() if any("{port}" in (c or "") for c in commands) else None
        started = time.monotonic()  # D38: one repeat, from `start` to stop
        service = None
        try:
            if suite.start is not None:
                service = process.spawn(process.with_port(suite.start, port), self.cwd, log)
                self._wait_ready(service, port, log)
            run = process.with_port(suite.run, port)
            done = process.run(run, self.cwd, log, timeout=suite.timeout)
        finally:
            if service is not None:
                process.stop(service)  # AC11
            self.result.durations.append(time.monotonic() - started)
        if done.timed_out:
            self.timed_out = True
            raise _Broken(f"took longer than {seconds(suite.timeout or 0)}", log)
        code = done.code or 0
        self.codes.append(code)
        self.last_log = log
        if suite.junit is not None:
            self._read_tests(code, log)

    def _wait_ready(self, service, port: int | None, log: Path) -> None:
        """FR3: poll `ready` every second until it succeeds or `ready_timeout` ends (AC10)."""
        if self.suite.ready is None:
            return
        check = process.with_port(self.suite.ready, port)
        limit = self.suite.ready_timeout
        deadline = time.monotonic() + limit
        while True:
            if service.poll() is not None:
                raise _Broken("service stopped before it was ready", log)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise _Broken(f"service did not become ready within {seconds(limit)}", log)
            if process.run(check, self.cwd, log, timeout=remaining).code == 0:
                return
            time.sleep(max(0.0, min(READY_POLL, deadline - time.monotonic())))

    def _read_tests(self, code: int, log: Path) -> None:
        """FR6: a non-zero exit must be explained by a failed test, or the Suite is broken."""
        try:
            outcomes = junit.read_results(self.cwd, self.suite.junit or "")
        except junit.JunitError as error:
            raise _Broken(str(error), log) from None
        if code != 0 and not {"failed", "flaky"} & set(outcomes.values()):
            raise _Broken(
                f"exited with code {code}, but its JUnit XML shows no failed test",
                log,
                hint="For example, the build failed. Read the log.",
            )
        self.test_runs.append(outcomes)

    def _judge(self) -> None:
        if self.suite.junit is not None:
            self._judge_tests()
        else:
            self._judge_codes()

    def _judge_tests(self) -> None:
        """FR5, FR6 with `junit`: failing and flaky tests are excluded; one must pass."""
        tests = junit.combine(self.test_runs)
        self.result.tests = tests
        if not any(self.test_runs):
            self.result.warnings.append(
                f"no file matched junit = {self.suite.junit!r}; per-test results are missing."
            )
        elif junit.PASS not in tests.values():
            raise _Broken("no test passes on the clean code", self.last_log)

    def _judge_codes(self) -> None:
        """FR6 without `junit`: any non-zero run makes the Suite broken."""
        failed = [code != 0 for code in self.codes]
        if all(failed):
            raise _Broken(f"failed on every run (exit code {self.codes[-1]})", self.last_log)
        if any(failed):
            first = self._log(str(failed.index(True) + 1))
            raise _Broken(
                "flaky Suite",
                first,
                hint="It failed on one run and passed on another. "
                "Set 'junit' in this Suite to find the flaky test.",
            )

    def _teardown(self) -> None:
        if self.suite.teardown is None:
            return
        log = self._log("teardown")
        done = process.run(self.suite.teardown, self.cwd, log, timeout=self.suite.timeout)
        if done.timed_out or done.code != 0:
            text = process.tail(log)
            self.result.warnings.append(f"teardown failed (see {self._rel(log)}):\n{text}")


def _text(data: dict, results: list[SuiteResult], base: worktree.Base) -> list[str]:
    lines = [f"Baseline {base.ref} ({base.commit[:7]}) in {worktree.BASE}"]
    for r in results:
        if r.status == OK_STATUS:
            times = ", ".join(f"{d:.1f}s" for d in r.durations)
            lines.append(f"  {r.name} ({r.level}): ok, {times}")
            for status in (junit.FAILING, junit.FLAKY):
                tests = r.excluded(status)
                if tests:
                    lines.append(f"    {len(tests)} {status} test(s), excluded from scoring:")
                    lines += [f"      {t}" for t in tests]
        else:
            lines.append(f"  {r.name} ({r.level}): broken: {r.reason}")
            lines += [f"    | {line}" for line in r.tail.splitlines()]
            if r.log:
                lines.append(f"    log: {r.log}")
            if r.hint:
                lines.append(f"    {r.hint}")
        for warning in r.warnings:
            lines += [f"    warning: {line}" for line in warning.splitlines()[:1]]
            lines += [f"    | {line}" for line in warning.splitlines()[1:]]
    broken = [r.name for r in results if r.status == BROKEN]
    if broken:
        lines.append(
            f"not ready: {len(broken)} of {len(results)} Suites broken ({', '.join(broken)}). "
            "Fix them, or remove them from mutaspec.toml on purpose."
        )
    else:
        lines.append("ready")
    return lines


@dataclass
class Checked:
    base: worktree.Base
    results: list[SuiteResult]
    data: dict  # what baseline.json holds
    lines: list[str]
    warnings: list[str]

    @property
    def ready(self) -> bool:
        return self.data["ready"]


def check(config: Config, include_uncommitted: bool) -> Checked:
    """Run every Suite on the Baseline and write baseline.json (FR1-FR9)."""
    root = config.root.resolve()
    worktree.own_folder(root / RUNS)
    (root / RESULT_FILE).unlink(missing_ok=True)  # D40
    logs = root / LOGS
    shutil.rmtree(logs, ignore_errors=True)
    logs.mkdir(parents=True)

    base = worktree.create_base(config, include_uncommitted)
    warnings = [worktree.left_out_warning(base.left_out)] if base.left_out else []
    started_at = datetime.now(UTC).isoformat(timespec="seconds")

    results = [_SuiteRun(suite, base.project_dir, logs, root).run() for suite in config.suites]
    ready = all(r.status == OK_STATUS for r in results)
    data = {
        "baseline": base.ref,
        "commit": base.commit,
        "uncommitted": base.uncommitted,
        "ready": ready,
        "started_at": started_at,
        "suites": [r.to_json() for r in results],
    }
    (root / RESULT_FILE).write_text(json.dumps(data, indent=2) + "\n")
    return Checked(base, results, data, _text(data, results, base), warnings)


def run(config: Config, include_uncommitted: bool) -> dict:
    """`mutaspec baseline`: the Baseline result for people and for --json."""
    checked = check(config, include_uncommitted)
    return {
        **checked.data,
        "lines": checked.lines,
        "warnings": checked.warnings,
        "exit_code": OK if checked.ready else ENVIRONMENT,
    }
