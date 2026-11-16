"""Per-test results from JUnit XML files, as Maven Surefire and Failsafe write them (FR5).

One run gives `{test id: passed|failed|skipped|flaky}`; `combine` turns several runs
into `{test id: pass|failing|flaky}`. A test id is `classname#name`.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

PASS, FAILING, FLAKY = "pass", "failing", "flaky"

_FAILED = ("failure", "error")
# Surefire re-runs (rerunFailingTestsCount): failed first, then passed in the same run.
_RERUN_PASSED = ("flakyFailure", "flakyError")


class JunitError(ValueError):
    """A JUnit XML file could not be read."""


def _files(folder: Path, glob: str) -> list[Path]:
    return sorted(p for p in folder.glob(glob) if p.is_file())


def clear(folder: Path, glob: str) -> None:
    """D29: delete old result files before a run, so they are never read twice."""
    for path in _files(folder, glob):
        path.unlink()


def _outcome(testcase: ET.Element) -> str:
    tags = {child.tag for child in testcase}
    if tags & set(_FAILED):
        return "failed"
    if "skipped" in tags:
        return "skipped"
    if tags & set(_RERUN_PASSED):
        return "flaky"
    return "passed"


_RANK = {"skipped": 0, "passed": 1, "flaky": 2, "failed": 3}


def read_results(folder: Path, glob: str) -> dict[str, str]:
    """The outcome of each test in the files under `folder` that match `glob`."""
    results: dict[str, str] = {}
    for path in _files(folder, glob):
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as error:
            raise JunitError(f"cannot read JUnit XML {path.name}: {error}") from None
        for testcase in root.iter("testcase"):
            test_id = f"{testcase.get('classname', '')}#{testcase.get('name', '')}"
            outcome = _outcome(testcase)
            old = results.get(test_id)
            if old is None or _RANK[outcome] > _RANK[old]:
                results[test_id] = outcome
    return results


def combine(runs: list[dict[str, str]]) -> dict[str, str]:
    """FR5: `pass` every run, `failing` every run, else `flaky`. Skipped tests are left out."""
    seen: dict[str, set[str]] = {}
    for run in runs:
        for test_id, outcome in run.items():
            if outcome != "skipped":
                seen.setdefault(test_id, set()).add(outcome)
    status = {}
    for test_id, outcomes in sorted(seen.items()):
        if outcomes == {"passed"}:
            status[test_id] = PASS
        elif outcomes == {"failed"}:
            status[test_id] = FAILING
        else:
            status[test_id] = FLAKY
    return status
