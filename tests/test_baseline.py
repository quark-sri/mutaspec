"""`mutaspec baseline`: run every Suite on the Baseline and say if the project is ready (0002)."""

import json

import pytest
from conftest import git, tool, write

from mutaspec import baseline, process
from mutaspec.errors import ENVIRONMENT, OK

RESULT = ".mutaspec/runs/baseline.json"


@pytest.fixture(autouse=True)
def fast_waits(monkeypatch):
    """Shorter waits than the real 1s ready poll and 10s stop grace; same behaviour."""
    monkeypatch.setattr(baseline, "READY_POLL", 0.1)
    monkeypatch.setattr(process, "STOP_GRACE", 1.0)


def result(root):
    return json.loads((root / RESULT).read_text())


def suite(name, run, **more):
    return {"name": name, "level": more.pop("level", "unit"), "run": run, **more}


# S1: ready or not ready


def test_ac1_all_suites_pass_prints_ready_with_durations(make_project, run_cli):
    root = make_project(suite("unit", tool("exit", 0)), suite("api", tool("exit", 0), level="api"))

    out = run_cli(root, "baseline")

    assert out.code == OK
    assert "ready" in out.out
    assert "not ready" not in out.out
    data = result(root)
    assert data["ready"] is True
    assert data["baseline"] == "HEAD"
    assert data["commit"] == git(root, "rev-parse", "HEAD").strip()
    assert data["uncommitted"] is False
    assert data["started_at"]
    assert [s["name"] for s in data["suites"]] == ["unit", "api"]
    for entry in data["suites"]:
        assert entry["status"] == "ok"
        assert entry["reason"] is None
        assert len(entry["durations"]) == 2
        assert f"{entry['durations'][0]:.1f}s" in out.out


def test_ac2_suite_failing_every_run_without_junit_is_broken(make_project, run_cli):
    root = make_project(suite("unit", tool("exit", 1)))

    out = run_cli(root, "baseline")

    assert out.code == ENVIRONMENT
    assert "not ready" in out.out
    assert "exit 1" in out.out  # the output tail
    entry = result(root)["suites"][0]
    assert entry["status"] == "broken"
    assert "fail" in entry["reason"]
    assert result(root)["ready"] is False


def test_ac3_a_broken_suite_does_not_stop_the_next_one(make_project, run_cli, tmp_path):
    marker = tmp_path / "ran"
    root = make_project(
        suite("first", tool("exit", 1)), suite("second", tool("record", marker, "x"))
    )

    out = run_cli(root, "baseline")

    assert out.code == ENVIRONMENT
    assert marker.read_text().count("x ") == 2
    statuses = {s["name"]: s["status"] for s in result(root)["suites"]}
    assert statuses == {"first": "broken", "second": "ok"}
    assert "first" in out.out
    assert "second" in out.out


def test_ac4_json_is_one_object_with_the_baseline_json_shape(make_project, run_cli):
    root = make_project(suite("unit", tool("exit", 0)), suite("bad", tool("exit", 1)))

    out = run_cli(root, "baseline", "--json")

    data = out.json()
    assert out.code == ENVIRONMENT
    assert data["ok"] is False
    assert data["exit_code"] == ENVIRONMENT
    assert data["ready"] is False
    assert "error" not in data
    assert data["suites"] == result(root)["suites"]
    assert {"status", "durations", "reason"} <= set(data["suites"][0])


def test_ac4_json_has_per_test_status_for_junit_suites(make_project, run_cli, tmp_path):
    root = make_project(
        suite("unit", tool("junit", tmp_path / "n", "a=pp", "b=ff"), junit=JUNIT),
    )

    data = run_cli(root, "baseline", "--json").json()

    assert data["suites"][0]["tests"] == {"shop.T#a": "pass", "shop.T#b": "failing"}


def test_ac4_json_when_ready(make_project, run_cli):
    root = make_project(suite("unit", tool("exit", 0)))

    data = run_cli(root, "baseline", "--json").json()

    assert data["ok"] is True
    assert data["exit_code"] == OK
    assert data["ready"] is True


# S2 without junit


def test_ac7_suite_that_flips_without_junit_is_a_flaky_suite(make_project, run_cli, tmp_path):
    root = make_project(suite("unit", tool("seq", tmp_path / "n", 1, 0)))

    out = run_cli(root, "baseline")

    entry = result(root)["suites"][0]
    assert out.code == ENVIRONMENT
    assert entry["status"] == "broken"
    assert entry["reason"] == "flaky Suite"
    assert "junit" in entry["hint"]


def test_ac9_repeat_sets_the_number_of_runs(make_project, run_cli, tmp_path):
    root = make_project(
        suite("three", tool("seq", tmp_path / "three", 0), repeat=3),
        suite("default", tool("seq", tmp_path / "default", 0)),
    )

    run_cli(root, "baseline")

    assert (tmp_path / "three").read_text() == "3"
    assert (tmp_path / "default").read_text() == "2"
    assert [len(s["durations"]) for s in result(root)["suites"]] == [3, 2]


# Logs and safety


def test_fr9_output_of_each_run_is_kept(make_project, run_cli):
    root = make_project(suite("unit", tool("exit", 0)))

    run_cli(root, "baseline")

    logs = root / ".mutaspec/runs/baseline"
    assert "exit 0" in (logs / "unit-1.log").read_text()
    assert "exit 0" in (logs / "unit-2.log").read_text()


def test_ac15_commands_run_only_in_the_worktree(make_project, run_cli, tmp_path):
    cwd_log = tmp_path / "cwd"
    root = make_project(
        suite(
            "unit",
            tool("record", cwd_log, "run"),
            setup=tool("record", cwd_log, "setup"),
            teardown=tool("record", cwd_log, "teardown"),
        )
    )
    write(root, "src/app.txt", "uncommitted edit\n")
    before = (
        git(root, "rev-parse", "HEAD"),
        git(root, "branch", "--show-current"),
        git(root, "status", "--porcelain"),
    )

    run_cli(root, "baseline")

    after = (
        git(root, "rev-parse", "HEAD"),
        git(root, "branch", "--show-current"),
        git(root, "status", "--porcelain"),
    )
    assert after == before
    base = str((root / ".mutaspec/worktrees/base").resolve())
    lines = cwd_log.read_text().splitlines()
    assert len(lines) == 4
    assert all(line.split(" ", 1)[1] == base for line in lines)


def test_ac16_uncommitted_files_are_named_in_a_warning(make_project, run_cli):
    root = make_project(suite("unit", tool("exit", 0)))
    write(root, "src/app.txt", "edited\n")

    out = run_cli(root, "baseline")

    assert out.code == OK
    assert "src/app.txt" in out.err
    assert "--include-uncommitted" in out.err


def test_ac17_include_uncommitted_is_recorded(make_project, run_cli):
    root = make_project(suite("unit", tool("exit", 0)))
    write(root, "src/app.txt", "edited\n")

    run_cli(root, "baseline", "--include-uncommitted")

    assert result(root)["uncommitted"] is True
    assert (root / ".mutaspec/worktrees/base/src/app.txt").read_text() == "edited\n"


def test_ac18_include_uncommitted_with_other_ref_exits_2(make_project, run_cli):
    root = make_project(suite("unit", tool("exit", 0)), project='baseline = "HEAD~1"')

    out = run_cli(root, "baseline", "--include-uncommitted")

    assert out.code == 2


def test_edge_bad_ref_exits_2_and_names_it(make_project, run_cli):
    root = make_project(suite("unit", tool("exit", 0)), project='baseline = "nope"')

    out = run_cli(root, "baseline")

    assert out.code == 2
    assert "nope" in out.err


# Edge cases: setup and teardown


def test_edge_setup_failed_skips_runs_and_still_runs_teardown(make_project, run_cli, tmp_path):
    marks = tmp_path / "marks"
    root = make_project(
        suite(
            "unit",
            tool("record", marks, "run"),
            setup=tool("exit", 7),
            teardown=tool("record", marks, "teardown"),
        )
    )

    out = run_cli(root, "baseline")

    entry = result(root)["suites"][0]
    assert out.code == ENVIRONMENT
    assert entry["status"] == "broken"
    assert entry["reason"] == "setup failed"
    assert entry["durations"] == []
    assert "exit 7" in out.out
    assert [line.split()[0] for line in marks.read_text().splitlines()] == ["teardown"]


def test_edge_teardown_failure_is_a_warning_only(make_project, run_cli):
    root = make_project(suite("unit", tool("exit", 0), teardown=tool("exit", 5)))

    out = run_cli(root, "baseline")

    assert out.code == OK
    assert result(root)["suites"][0]["status"] == "ok"
    assert "teardown" in out.out
    assert "exit 5" in out.out


def test_d40_old_result_is_removed_when_a_baseline_starts(make_project, run_cli):
    root = make_project(suite("unit", tool("exit", 0)))
    write(root, RESULT, '{"ready": true, "old": true}')

    run_cli(root, "baseline")

    assert "old" not in result(root)


# S2 with junit

JUNIT = "**/target/surefire-reports/TEST-*.xml"


def junit_suite(state, *tests, exit=None, **more):
    args = ["junit", state, *(["--exit", exit] if exit is not None else []), *tests]
    return suite("unit", tool(*args), junit=JUNIT, **more)


def test_ac5_test_failing_every_run_is_listed_and_suite_stays_ok(make_project, run_cli, tmp_path):
    root = make_project(junit_suite(tmp_path / "n", "a=pp", "b=ff"))

    out = run_cli(root, "baseline")

    entry = result(root)["suites"][0]
    assert out.code == OK
    assert entry["status"] == "ok"
    assert entry["tests"] == {"shop.T#a": "pass", "shop.T#b": "failing"}
    assert "shop.T#b" in out.out


def test_ac6_test_that_flips_is_flaky_and_suite_stays_ok(make_project, run_cli, tmp_path):
    root = make_project(junit_suite(tmp_path / "n", "a=pp", "c=fp"))

    out = run_cli(root, "baseline")

    entry = result(root)["suites"][0]
    assert out.code == OK
    assert entry["status"] == "ok"
    assert entry["tests"]["shop.T#c"] == "flaky"
    assert "shop.T#c" in out.out


def test_ac8_non_zero_exit_with_no_failed_test_in_xml_is_broken(make_project, run_cli, tmp_path):
    root = make_project(junit_suite(tmp_path / "n", "a=pp", exit=1))

    out = run_cli(root, "baseline")

    entry = result(root)["suites"][0]
    assert out.code == ENVIRONMENT
    assert entry["status"] == "broken"
    assert "no failed test" in entry["reason"]


def test_ac8_non_zero_exit_with_no_xml_at_all_is_broken(make_project, run_cli):
    root = make_project(suite("unit", tool("exit", 1), junit=JUNIT))

    run_cli(root, "baseline")

    assert result(root)["suites"][0]["status"] == "broken"


def test_edge_junit_matches_no_files_after_exit_0_is_ok_with_warning(make_project, run_cli):
    root = make_project(suite("unit", tool("exit", 0), junit=JUNIT))

    out = run_cli(root, "baseline")

    entry = result(root)["suites"][0]
    assert out.code == OK
    assert entry["status"] == "ok"
    assert entry["tests"] == {}
    assert "per-test results are missing" in entry["warnings"][0]
    assert "per-test results are missing" in out.out


def test_edge_no_test_passes_is_broken(make_project, run_cli, tmp_path):
    root = make_project(junit_suite(tmp_path / "n", "a=ff", "b=fp"))

    out = run_cli(root, "baseline")

    entry = result(root)["suites"][0]
    assert out.code == ENVIRONMENT
    assert entry["reason"] == "no test passes on the clean code"


def test_d29_old_xml_is_deleted_before_each_run(make_project, run_cli, tmp_path):
    old = '<testsuite><testcase classname="old.T" name="x"><failure/></testcase></testsuite>'
    setup = f"mkdir -p target/surefire-reports && echo '{old}' > target/surefire-reports/TEST-o.xml"
    root = make_project(suite("unit", tool("exit", 0), junit=JUNIT, setup=setup))

    run_cli(root, "baseline")

    entry = result(root)["suites"][0]
    assert entry["status"] == "ok"
    assert "old.T#x" not in entry["tests"]


def test_fr8_tests_are_left_out_when_junit_is_not_set(make_project, run_cli):
    root = make_project(suite("unit", tool("exit", 0)))

    run_cli(root, "baseline")

    assert "tests" not in result(root)["suites"][0]


def test_sc2_failing_and_flaky_tests_are_named_in_10_of_10_runs(make_project, run_cli, tmp_path):
    state = tmp_path / "n"
    root = make_project(junit_suite(state, "a=pp", "b=ff", "c=fp"))

    for _ in range(10):
        state.unlink(missing_ok=True)
        out = run_cli(root, "baseline")
        tests = result(root)["suites"][0]["tests"]
        assert (tests["shop.T#b"], tests["shop.T#c"]) == ("failing", "flaky")
        assert "shop.T#b" in out.out
        assert "shop.T#c" in out.out


# S3 services


def started_pids(pidfile):
    return [int(p) for line in pidfile.read_text().splitlines() for p in line.split()[:2]]


def all_gone(pids, wait=3.0):
    import os
    import time

    deadline = time.monotonic() + wait
    alive = list(pids)
    while alive and time.monotonic() < deadline:
        still = []
        for pid in alive:
            try:
                os.kill(pid, 0)
                still.append(pid)
            except ProcessLookupError:
                pass
        alive = still
        if alive:
            time.sleep(0.05)
    return not alive


def service_suite(tmp_path, run, **more):
    pids = tmp_path / "pids"
    return suite(
        "api",
        run,
        level="api",
        start=more.pop("start", tool("serve", pids, "{port}")),
        ready=more.pop("ready", tool("probe", "{port}")),
        ready_timeout=more.pop("ready_timeout", "5s"),
        teardown=tool("record", tmp_path / "teardown", "teardown"),
        **more,
    )


def test_ac10_ready_never_succeeds_stops_start_and_runs_teardown(make_project, run_cli, tmp_path):
    root = make_project(
        service_suite(tmp_path, tool("exit", 0), ready=tool("exit", 1), ready_timeout="1s")
    )

    out = run_cli(root, "baseline")

    entry = result(root)["suites"][0]
    assert out.code == ENVIRONMENT
    assert entry["reason"] == "service did not become ready within 1s"
    assert all_gone(started_pids(tmp_path / "pids"))
    assert (tmp_path / "teardown").read_text().count("teardown") == 1


@pytest.mark.parametrize("code", [0, 1])
def test_ac11_start_is_stopped_after_each_run(make_project, run_cli, tmp_path, code):
    root = make_project(service_suite(tmp_path, tool("exit", code)))

    run_cli(root, "baseline")

    pids = started_pids(tmp_path / "pids")
    assert len(pids) == 4  # 2 runs x (service + its child)
    assert all_gone(pids)
    assert (tmp_path / "teardown").read_text().count("teardown") == 1


def test_ac13_port_is_the_same_in_start_ready_and_run(make_project, run_cli, tmp_path):
    ports = tmp_path / "ports"
    root = make_project(service_suite(tmp_path, tool("record", ports, "{port}")))

    out = run_cli(root, "baseline")

    assert out.code == OK
    served = [line.split()[2] for line in (tmp_path / "pids").read_text().splitlines()]
    used = [line.split()[0] for line in ports.read_text().splitlines()]
    assert used == served
    assert all(p.isdigit() for p in used)


def test_ac14_suite_longer_than_its_timeout_is_broken(make_project, run_cli, tmp_path):
    root = make_project(service_suite(tmp_path, tool("sleep", 30), timeout="1s"))

    out = run_cli(root, "baseline")

    entry = result(root)["suites"][0]
    assert out.code == ENVIRONMENT
    assert entry["reason"] == "took longer than 1s"
    assert len(entry["durations"]) == 1
    assert all_gone(started_pids(tmp_path / "pids"))


def test_edge_start_exits_before_ready_is_broken(make_project, run_cli, tmp_path):
    root = make_project(
        service_suite(
            tmp_path,
            tool("exit", 0),
            start=tool("serve", tmp_path / "pids", "{port}", "--die"),
            ready=tool("exit", 1),
        )
    )

    out = run_cli(root, "baseline")

    assert out.code == ENVIRONMENT
    assert result(root)["suites"][0]["reason"] == "service stopped before it was ready"
    assert "$ " in out.out  # the output tail of the start log is shown


def test_ac15_start_and_ready_run_in_the_worktree(make_project, run_cli, tmp_path):
    cwd_log = tmp_path / "cwd"
    start = f"{tool('record', cwd_log, 'start')}; {tool('serve', tmp_path / 'pids', '{port}')}"
    ready = f"{tool('record', cwd_log, 'ready')}; {tool('probe', '{port}')}"
    root = make_project(service_suite(tmp_path, tool("exit", 0), start=start, ready=ready))

    run_cli(root, "baseline")

    base = str((root / ".mutaspec/worktrees/base").resolve())
    lines = cwd_log.read_text().splitlines()
    assert {line.split()[0] for line in lines} == {"start", "ready"}
    assert all(line.split(" ", 1)[1] == base for line in lines)


def test_d38_duration_covers_start_to_stop(make_project, run_cli, tmp_path):
    root = make_project(
        service_suite(
            tmp_path,
            tool("exit", 0),
            start=f"sleep 0.5; {tool('serve', tmp_path / 'pids', '{port}')}",
        )
    )

    run_cli(root, "baseline")

    assert all(d >= 0.5 for d in result(root)["suites"][0]["durations"])
