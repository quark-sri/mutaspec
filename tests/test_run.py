"""`mutaspec run`: run the Suites on each Rule Mutant and score them."""

import json
import shlex
import sys

import pytest
from conftest import commit_all, git, write

from mutaspec import baseline, process, runner
from mutaspec.errors import ENVIRONMENT, OK

CALC = """\
def is_adult(age):
    return age >= 18


def add(a, b):
    return a + b


def countdown(n):
    while n > 0:
        n = n - 1
    return n
"""

TESTS = """\
import sys
import unittest

sys.path.insert(0, "src")
import calc  # noqa: E402


class CalcTest(unittest.TestCase):
    def test_adult(self):
        self.assertTrue(calc.is_adult(30))
        self.assertFalse(calc.is_adult(5))  # no test at 18: '>=' -> '>' survives

    def test_add(self):
        self.assertEqual(calc.add(2, 3), 5)
        self.assertEqual(calc.add(1, 1), 1 + 1)  # a test file: never mutated

    def test_countdown(self):
        self.assertEqual(calc.countdown(3), 0)
"""

UNITTEST = shlex.join([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"])


@pytest.fixture(autouse=True)
def fast_waits(monkeypatch):
    monkeypatch.setattr(baseline, "READY_POLL", 0.1)
    monkeypatch.setattr(process, "STOP_GRACE", 1.0)
    monkeypatch.setattr(runner, "MIN_TIMEOUT", 2.0)


@pytest.fixture
def calc_repo(git_repo):
    def _make(project: str = "", run: str = UNITTEST):
        write(git_repo, "src/calc.py", CALC)
        write(git_repo, "tests/test_calc.py", TESTS)
        write(
            git_repo,
            "mutaspec.toml",
            f'[project]\nsource = ["src/**"]\ntests = ["tests/**"]\n{project}\n\n'
            f'[[suites]]\nname = "unit"\nlevel = "unit"\nrun = {json.dumps(run)}\n',
        )
        commit_all(git_repo)
        return git_repo

    return _make


def by_rule(data: dict) -> dict[str, str]:
    return {f"{m['line']} {m['rule']}": m["status"] for m in data["mutants"]}


def test_ac1_ac6_each_mutant_is_killed_survived_or_timeout_and_scored(calc_repo, run_cli):
    root = calc_repo()

    out = run_cli(root, "run", "--json")

    assert out.code == OK
    data = out.json()
    assert by_rule(data) == {
        "2 >= -> >": "survived",
        "6 + -> -": "killed",
        "10 > -> >=": "killed",
        "11 - -> +": "timeout",
    }
    assert data["score"] == 75.0
    assert {m["file"] for m in data["mutants"]} == {"src/calc.py"}  # AC3: no test file
    assert (data["caught"], data["scored"], data["survived"]) == (3, 4, 1)
    killed = next(m for m in data["mutants"] if m["status"] == "killed")
    assert killed["suite"] == "unit"


def test_ac9_text_output_names_the_survived_mutant_and_writes_a_report(calc_repo, run_cli):
    root = calc_repo()

    out = run_cli(root, "run")

    assert "Score: 75.0%" in out.out
    assert "src/calc.py:2  >= -> >" in out.out
    assert "- return age >= 18" in out.out
    assert "+ return age > 18" in out.out
    report = (root / runner.REPORT).read_text()
    assert "## Survived" in report
    assert "+    return age > 18" in report


def test_ac8_the_users_files_and_git_state_do_not_change(calc_repo, run_cli):
    root = calc_repo()
    before = (git(root, "status", "--porcelain"), (root / "src/calc.py").read_text())

    run_cli(root, "run")

    assert (git(root, "status", "--porcelain"), (root / "src/calc.py").read_text()) == before
    base = root / ".mutaspec/worktrees/base/src/calc.py"
    assert base.read_text() == CALC  # every Mutant was put back


def test_ac4_max_limits_the_mutants(calc_repo, run_cli):
    root = calc_repo()

    data = run_cli(root, "run", "--max", "2", "--json").json()

    assert len(data["mutants"]) == 2
    assert data["found"] == 4


def test_ac5_a_mutant_that_fails_build_is_invalid_and_not_scored(calc_repo, run_cli):
    root = calc_repo(project="build = \"! grep -q 'n + 1' src/calc.py\"")

    data = run_cli(root, "run", "--json").json()

    assert by_rule(data)["11 - -> +"] == "invalid"
    assert data["scored"] == 3
    assert "build failed" in next(m["reason"] for m in data["mutants"] if m["status"] == "invalid")


def test_ac2_not_ready_baseline_stops_before_any_mutant(calc_repo, run_cli):
    root = calc_repo(run="exit 1")

    out = run_cli(root, "run")

    assert out.code == ENVIRONMENT
    assert "not ready" in out.out
    assert not (root / runner.REPORT).exists()


def test_max_must_be_positive(calc_repo, run_cli):
    root = calc_repo()

    assert run_cli(root, "run", "--max", "0").code == 2


def test_ac7_only_tests_that_passed_on_the_baseline_count_as_kills():
    before = {"T#ok": "pass", "T#flaky": "flaky", "T#broken": "failing"}

    assert runner.newly_failed(before, {"T#flaky": "failed", "T#broken": "failed"}) == []
    assert runner.newly_failed(before, {"T#ok": "failed", "T#new": "failed"}) == ["T#ok"]


def test_ac1_score_counts_timeouts_as_caught_and_leaves_invalid_out():
    def o(status):
        return runner.Outcome(mutant=None, status=status)

    outcomes = [o("killed")] * 6 + [o("timeout")] + [o("survived")] * 3 + [o("invalid")] * 2

    s = runner.score(outcomes)

    assert (s["score"], s["caught"], s["scored"], s["invalid"]) == (70.0, 7, 10, 2)


def test_ac1_python_never_runs_stale_bytecode_of_the_baseline(git_repo, run_cli):
    # '+' -> '-' keeps the file size; written in the same second as the Baseline's
    # .pyc, Python would reuse the old bytecode and the Mutant would survive.
    write(git_repo, "src/m.py", "def f(a, b):\n    return a + b\n")
    write(
        git_repo,
        "tests/test_m.py",
        "import sys, unittest\nsys.path.insert(0, 'src')\nimport m\n\n\n"
        "class T(unittest.TestCase):\n    def test_f(self):\n"
        "        self.assertEqual(m.f(2, 3), 5)\n",
    )
    write(
        git_repo,
        "mutaspec.toml",
        '[project]\nsource = ["src/**"]\ntests = ["tests/**"]\n\n'
        f'[[suites]]\nname = "unit"\nlevel = "unit"\nrun = {json.dumps(UNITTEST)}\n',
    )
    commit_all(git_repo)

    for _ in range(3):
        data = run_cli(git_repo, "run", "--json").json()
        assert [m["status"] for m in data["mutants"]] == ["killed"]
