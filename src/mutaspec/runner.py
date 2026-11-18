"""`mutaspec run`: check the Baseline, then run the Suites on each Rule Mutant and score them.

For each Mutant: write it into the Baseline worktree, run `build` (if set), run the Suites
from the fastest to the slowest until one catches it, and put the code back.
"""

import shutil
import time
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from pathlib import Path

from mutaspec import baseline, junit, mutants, process
from mutaspec import config as cfg
from mutaspec.config import Config, Suite
from mutaspec.errors import ENVIRONMENT, OK

KILLED, TIMEOUT, SURVIVED, INVALID = "killed", "timeout", "survived", "invalid"
LOGS = baseline.RUNS / "mutants"
REPORT = baseline.RUNS / "report.md"
DEFAULT_MAX = 20
MIN_TIMEOUT = 30.0  # seconds; a Suite may take this long on a Mutant, at least
TIMEOUT_FACTOR = 3  # ... or this many times its Baseline duration
BUILD_TIMEOUT = 600.0


@dataclass
class Outcome:
    mutant: mutants.Mutant
    status: str
    suite: str | None = None  # the Suite that caught it
    tests: list[str] = field(default_factory=list)  # tests that failed on it (with junit)
    reason: str | None = None  # why it is Invalid
    seconds: float = 0.0

    def to_json(self) -> dict:
        return {
            **self.mutant.to_json(),
            "status": self.status,
            "suite": self.suite,
            "tests": self.tests,
            "reason": self.reason,
            "seconds": round(self.seconds, 3),
            "diff": self.mutant.diff(),
        }


def newly_failed(before: dict[str, str], now: dict[str, str]) -> list[str]:
    """Tests that passed on every Baseline run and fail on the Mutant. Flaky and already
    failing tests never count."""
    return sorted(t for t, s in now.items() if s == "failed" and before.get(t) == junit.PASS)


def mutant_timeout(suite: Suite, result: baseline.SuiteResult) -> float:
    limit = max(MIN_TIMEOUT, TIMEOUT_FACTOR * max(result.durations, default=0.0))
    return min(limit, suite.timeout) if suite.timeout else limit


def _try_suite(
    suite: Suite, before: baseline.SuiteResult, cwd: Path, logs: Path, root: Path
) -> tuple[str, list[str], str | None]:
    once = replace(suite, repeat=1, timeout=mutant_timeout(suite, before))
    run = baseline._SuiteRun(once, cwd, logs, root, judge=False)
    result = run.run()
    if run.timed_out:
        return TIMEOUT, [], None
    if result.status == baseline.BROKEN:
        return INVALID, [], f"{suite.name}: {result.reason} (log: {result.log})"
    if suite.junit and before.tests:
        tests = newly_failed(before.tests, run.test_runs[0])
        return (KILLED if tests else SURVIVED), tests, None
    return (KILLED if run.codes[0] != 0 else SURVIVED), [], None


def _run_mutant(
    mutant: mutants.Mutant, config: Config, checked: baseline.Checked, root: Path
) -> Outcome:
    started = time.monotonic()
    cwd = checked.base.project_dir
    logs = root / LOGS / mutant.id
    logs.mkdir(parents=True, exist_ok=True)
    order = sorted(
        zip(config.suites, checked.results, strict=True),
        key=lambda pair: sum(pair[1].durations) / max(len(pair[1].durations), 1),
    )
    outcome = Outcome(mutant, SURVIVED)
    try:
        with process.no_interrupts():  # a Ctrl-C never leaves a half-written file
            original = mutants.apply(mutant, cwd)
    except ValueError as error:  # e.g. a build step rewrote the file
        outcome.status, outcome.reason = INVALID, str(error)
        return outcome
    try:
        if config.project.build:
            log = logs / "build.log"
            done = process.run(config.project.build, cwd, log, timeout=BUILD_TIMEOUT)
            if done.timed_out or done.code != 0:
                outcome.status = INVALID
                outcome.reason = f"build failed (log: {log.relative_to(root)})"
        for suite, before in order if outcome.status == SURVIVED else []:
            status, tests, reason = _try_suite(suite, before, cwd, logs, root)
            if status != SURVIVED:
                outcome.status, outcome.tests, outcome.reason = status, tests, reason
                outcome.suite = suite.name if status != INVALID else None
                break
    finally:
        with process.no_interrupts():
            mutants.restore(mutant, cwd, original)
    outcome.seconds = time.monotonic() - started
    return outcome


def score(outcomes: list[Outcome]) -> dict:
    count = {s: sum(o.status == s for o in outcomes) for s in (KILLED, TIMEOUT, SURVIVED, INVALID)}
    caught = count[KILLED] + count[TIMEOUT]
    scored = caught + count[SURVIVED]
    percent = round(100 * caught / scored, 1) if scored else None
    return {"score": percent, "caught": caught, "scored": scored, **count}


def _where(m: mutants.Mutant) -> str:
    return f"{m.file}:{m.line}"


def _line(n: int, total: int, o: Outcome) -> str:
    by = f" by {o.suite}" if o.suite else ""
    return (
        f"[{n:>{len(str(total))}}/{total}] {o.status.upper():<8} {_where(o.mutant)}  "
        f"{o.mutant.rule}{by}  ({o.seconds:.1f}s)"
    )


def _summary(s: dict) -> str:
    if s["score"] is None:
        return "Score: none (no Mutant could be scored)."
    return (
        f"Score: {s['score']}% ({s['caught']} of {s['scored']} Mutants caught; "
        f"{s['survived']} survived, {s['invalid']} invalid)"
    )


def _report(checked: baseline.Checked, outcomes: list[Outcome], s: dict, found: int) -> str:
    data = checked.data
    out = [
        "# mutaspec report",
        "",
        f"Baseline `{data['baseline']}` ({data['commit'][:7]}), {data['started_at']}.",
        "",
        f"**{_summary(s)}**",
        "",
        f"{len(outcomes)} of {found} Rule Mutants were run.",
        "",
        "Killed and timeout count as caught. Invalid Mutants (they did not build, or a",
        "Suite broke for another reason) are not scored.",
    ]
    survived = [o for o in outcomes if o.status == SURVIVED]
    if survived:
        out += ["", "## Survived: no test caught these bugs", ""]
        for o in survived:
            out += [f"### `{o.mutant.id}` {_where(o.mutant)}: `{o.mutant.rule}`", ""]
            out += ["```diff", o.mutant.diff().rstrip(), "```", ""]
    out += ["", "## All Mutants", "", "| Mutant | Where | Change | Result | Detail |"]
    out += ["|---|---|---|---|---|"]
    for o in outcomes:
        detail = o.reason or ", ".join([o.suite or "", *o.tests[:3]]).strip(", ")
        out.append(
            f"| `{o.mutant.id}` | {_where(o.mutant)} | `{o.mutant.rule}` | {o.status} | "
            f"{detail.replace('|', '/')} |"
        )
    return "\n".join(out) + "\n"


def run(
    config: Config,
    include_uncommitted: bool,
    max_mutants: int = DEFAULT_MAX,
    say: Callable[[str], None] = lambda _: None,
) -> dict:
    root = config.root.resolve()
    checked = baseline.check(config, include_uncommitted)
    for line in checked.lines:
        say(line)
    if not checked.ready:
        return {
            "ready": False,
            "baseline": checked.data,
            "lines": [],
            "warnings": checked.warnings,
            "exit_code": ENVIRONMENT,
        }

    files = cfg.source_files(config)
    found = mutants.find(checked.base.project_dir, files)
    chosen = mutants.sample(found, max_mutants)
    say(f"\n{len(chosen)} of {len(found)} Rule Mutants in {len(files)} source files.")
    shutil.rmtree(root / LOGS, ignore_errors=True)

    outcomes = []
    for n, mutant in enumerate(chosen, start=1):
        outcomes.append(_run_mutant(mutant, config, checked, root))
        say(_line(n, len(chosen), outcomes[-1]))

    s = score(outcomes)
    (root / REPORT).write_text(_report(checked, outcomes, s, len(found)))
    lines = ["", _summary(s)]
    survived = [o for o in outcomes if o.status == SURVIVED]
    if survived:
        lines.append("Survived (no test caught these):")
        for o in survived:
            lines.append(f"  {_where(o.mutant)}  {o.mutant.rule}")
            lines.append(f"    - {o.mutant.before.strip()}")
            lines.append(f"    + {o.mutant.after.strip()}")
    lines.append(f"Report: {REPORT}")
    return {
        "ready": True,
        "baseline": checked.data,
        **s,
        "found": len(found),
        "mutants": [o.to_json() for o in outcomes],
        "report": str(REPORT),
        "lines": lines,
        "warnings": checked.warnings,
        "exit_code": OK,
    }
