"""`mutaspec run`: check the Baseline, then run the Suites on each Rule Mutant and score them.

For each Mutant: write it into the Baseline worktree, run `build` (if set), run the Suites
from the fastest to the slowest until one catches it (or all of them with `--per-level`),
and put the code back.
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
    suites: dict[str, str] = field(default_factory=dict)  # the result of each Suite that ran

    def to_json(self) -> dict:
        return {
            **self.mutant.to_json(),
            "status": self.status,
            "suite": self.suite,
            "tests": self.tests,
            "reason": self.reason,
            "seconds": round(self.seconds, 3),
            "suites": self.suites,
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
    mutant: mutants.Mutant,
    config: Config,
    checked: baseline.Checked,
    root: Path,
    per_level: bool = False,
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
            outcome.suites[suite.name] = status
            outcome.tests += tests
            if status in (KILLED, TIMEOUT) and outcome.suite is None:
                outcome.suite = suite.name
                outcome.status = status
            if status == INVALID and outcome.reason is None:
                outcome.reason = reason
            if status != SURVIVED and not per_level:
                break
        if outcome.suite is None and outcome.reason is not None:
            outcome.status = INVALID  # no Suite caught it, and one broke
        elif outcome.suite is not None:
            outcome.reason = None
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


def level_scores(outcomes: list[Outcome], config: Config) -> dict[str, dict]:
    """Spec 0004 AC2: per Level, the Mutants caught by a Suite of that Level, out of those
    where every Suite of that Level gave a result."""
    levels: dict[str, list[str]] = {}
    for suite in config.suites:
        levels.setdefault(suite.level, []).append(suite.name)
    scores = {}
    for level, names in levels.items():
        caught = scored = 0
        for o in outcomes:
            results = [o.suites.get(name) for name in names]
            if o.status == INVALID or any(r in (None, INVALID) for r in results):
                continue
            scored += 1
            caught += any(r in (KILLED, TIMEOUT) for r in results)
        percent = round(100 * caught / scored, 1) if scored else None
        scores[level] = {"score": percent, "caught": caught, "scored": scored}
    return scores


def _percent(value: float | None) -> str:
    return "none" if value is None else f"{value}%"


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


def _report(
    checked: baseline.Checked,
    outcomes: list[Outcome],
    s: dict,
    found: int,
    levels: dict[str, dict] | None,
    config: Config,
) -> str:
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
    if levels is not None:
        out += ["", "## Per Level", "", "| Level | Score | Caught | Scored |", "|---|---|---|---|"]
        for level, v in levels.items():
            out.append(f"| {level} | {_percent(v['score'])} | {v['caught']} | {v['scored']} |")
    survived = [o for o in outcomes if o.status == SURVIVED]
    if survived:
        out += ["", "## Survived: no test caught these bugs", ""]
        for o in survived:
            out += [f"### `{o.mutant.id}` {_where(o.mutant)}: `{o.mutant.rule}`", ""]
            out += ["```diff", o.mutant.diff().rstrip(), "```", ""]
    out += ["", "## All Mutants", "", "| Mutant | Where | Change | Result | Detail |"]
    out += ["|---|---|---|---|---|"]
    for o in outcomes:
        if levels is not None:
            ran = [s.name for s in config.suites if s.name in o.suites]
            detail = ", ".join(f"{name}: {o.suites[name]}" for name in ran)
        else:
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
    per_level: bool = False,
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
        outcomes.append(_run_mutant(mutant, config, checked, root, per_level))
        say(_line(n, len(chosen), outcomes[-1]))

    s = score(outcomes)
    levels = level_scores(outcomes, config) if per_level else None
    (root / REPORT).write_text(_report(checked, outcomes, s, len(found), levels, config))
    lines = ["", _summary(s)]
    if levels is not None:
        lines.append("Per Level:")
        for level, v in levels.items():
            lines.append(f"  {level:<12} {_percent(v['score'])}  ({v['caught']} of {v['scored']})")
    elif len({suite.level for suite in config.suites}) > 1:
        lines.append(
            "For a score per Level, run with --per-level (runs every Suite on every Mutant)."
        )
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
        **({"levels": levels} if levels is not None else {}),
        "found": len(found),
        "mutants": [o.to_json() for o in outcomes],
        "report": str(REPORT),
        "lines": lines,
        "warnings": checked.warnings,
        "exit_code": OK,
    }
