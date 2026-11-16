"""`mutaspec baseline`: run every Suite on the Baseline and say if the project is ready (0002)."""

import json

from conftest import git, tool, write

from mutaspec.errors import ENVIRONMENT, OK

RESULT = ".mutaspec/runs/baseline.json"


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
