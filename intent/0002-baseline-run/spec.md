# Spec: baseline run (from intent.md, 2026-11-16)

Status: approved. Intent: [intent.md](intent.md)

Decisions behind this spec: [docs/decisions.md](../../docs/decisions.md) D15–D36. Rows marked `agent` are for the owner to confirm in the PR review.

## User scenarios and acceptance

### S1 Confirm the project is ready (P1)
- **AC1** Given every Suite passes on each run, When I run `mutaspec baseline`, Then it prints "ready" with each Suite's duration, writes `.mutaspec/runs/baseline.json`, and exits 0.
- **AC2** Given a Suite with no `junit` that fails on every run, When I run `mutaspec baseline`, Then that Suite is `broken`, the last 20 lines of its output are shown, the result is "not ready", and the exit code is 3.
- **AC3** Given two Suites where the first is `broken`, When I run `mutaspec baseline`, Then the second Suite still runs, both results are reported, and the exit code is 3.
- **AC4** Given `--json`, When I run `mutaspec baseline`, Then stdout is one JSON object with `ok`, `exit_code`, `ready` and one entry per Suite (status, durations, tests), the same shape as `baseline.json`.

### S2 Failing and flaky tests (P1)
- **AC5** Given a Suite with `junit` where one test fails on every run, Then that test is listed as `failing`, excluded from scoring, and the Suite stays `ok`.
- **AC6** Given a Suite with `junit` where one test fails on one run and passes on another, Then that test is listed as `flaky`, excluded from scoring, and the Suite stays `ok`.
- **AC7** Given a Suite with no `junit` that fails on one run and passes on another, Then that Suite is `broken` with the reason "flaky Suite", and the hint says to set `junit` to find the test.
- **AC8** Given a Suite with `junit` that exits non-zero but its JUnit XML shows no failed test (for example, a compile error), Then that Suite is `broken`.
- **AC9** Given `repeat = 3` on a Suite, Then that Suite runs 3 times; given no `repeat`, it runs 2 times.

### S3 Services (P1)
- **AC10** Given a `ready` check that never succeeds within `ready_timeout`, Then that Suite is `broken` with "service did not become ready within 60s", the `start` process is stopped, and `teardown` runs.
- **AC11** Given a Suite with `start`, After each run (pass or fail), Then the `start` process and its child processes are stopped and `teardown` runs.
- **AC12** Given I press Ctrl-C during a run, Then every started process is stopped, `teardown` runs for every Suite that started, and mutaspec exits 130.
- **AC13** Given `{port}` in `start`, `ready` or `run`, Then mutaspec replaces it with a free TCP port, the same value in all three commands of that run.
- **AC14** Given a Suite that runs longer than its `timeout` on the clean code, Then it is stopped and that Suite is `broken` with "took longer than 300s".

### S4 Safety (P1)
- **AC15** After any baseline run (ready, not ready, or Ctrl-C), the user's `HEAD`, branch and `git status --porcelain` are unchanged, and no command ran in the user's working tree.
- **AC16** Given uncommitted changes to tracked files or new untracked files, When I run `mutaspec baseline`, Then it uses only the `baseline` ref and prints a warning that lists those files (first 10, then "and N more").
- **AC17** Given uncommitted changes and `--include-uncommitted`, Then the worktree has those changes (tracked edits and untracked, not ignored files), and `baseline.json` records `"uncommitted": true`.
- **AC18** Given `--include-uncommitted` and a `baseline` ref other than `HEAD`, Then it stops with a usage error, exit code 2.

### S5 init writes per-test results (P2)
- **AC19** Given a Maven project, When I run `mutaspec init`, Then each Suite it writes has `junit = "**/target/surefire-reports/TEST-*.xml"`.

## Edge cases
- `baseline` ref does not exist: error naming the ref, exit code 2.
- `setup` fails: Suite `broken` with "setup failed", output tail shown; `teardown` still runs. No repeats are tried.
- `start` process exits before `ready` succeeds: Suite `broken` with "service stopped before it was ready", output tail shown.
- `junit` matches no files after a run that exited 0: Suite `ok`, with a warning that per-test results are missing; tests are not listed.
- Every test of a Suite is `failing` or `flaky`: Suite `broken` ("no test passes on the clean code").
- Old JUnit XML from an earlier run: files matching `junit` are deleted in the worktree before each run, so they are never read twice.
- `teardown` fails: warning with its output tail; the Suite's status does not change.
- A worktree from an earlier baseline exists: it is removed and created again from the `baseline` ref.

## Functional requirements
- **FR1** Command: `mutaspec baseline [--include-uncommitted] [--json]`. It loads the config as `config check` does (spec 0001).
- **FR2** Worktree: `.mutaspec/worktrees/base`, created with `git worktree add --detach` at the `baseline` ref. It stays after the run so the user can inspect it. Every Suite command runs with this folder as its working directory, through the shell.
- **FR3** Lifecycle per Suite: `setup` once → for each repeat: start (in background, own process group) → poll `ready` every 1s until `ready_timeout` → `run` with `timeout` → stop `start` (SIGTERM to the process group, SIGKILL after 10s) → after the last repeat, or on any error, `teardown` (always). Suites run one after another, in config order.
- **FR4** `repeat` means the number of baseline runs of a Suite. Default 2 (changes the 0001 default of 1). Must be 1 or more.
- **FR5** Status per test (with `junit`): `pass` (passed every run), `failing` (failed or errored every run), `flaky` (passed at least once and failed at least once). Skipped tests are left out. A test is named `classname#name` from JUnit XML.
- **FR6** Status per Suite: `ok` or `broken`, with a reason. With `junit`: `broken` if setup, start, ready or timeout fails, if a run exits non-zero with no failed test in the XML, or if no test passes. Without `junit`: `broken` if any run exits non-zero.
- **FR7** Result: "ready" if every Suite is `ok`; else "not ready", exit code 3 (spec 0001 FR4: environment or setup error).
- **FR8** `.mutaspec/runs/baseline.json`: `baseline` ref, resolved commit, `uncommitted`, `ready`, started-at time, and per Suite: `name`, `level`, `status`, `reason`, `durations` (seconds, one per run), `tests` (`{id: status}`, only when `junit` is set). Written also when not ready. Later intents (0004, 0005) read it.
- **FR9** Output kept per Suite run: `.mutaspec/runs/baseline/<suite>-<n>.log` (stdout and stderr of start and run). Error messages show the last 20 lines.
- **FR10** `{port}`: one free TCP port per run, picked by binding to port 0 and then closing it.
- **FR11** `init` writes `junit = "**/target/surefire-reports/TEST-*.xml"` in each Maven Suite; the golden `examples/shop/mutaspec.toml` changes the same way.

## Key entities
- **Baseline result** (new in GLOSSARY.md): the outcome of running the Suites on the Baseline. Fields: ref, commit, uncommitted, ready, per-Suite status (`ok|broken`), reason, durations, per-test status (`pass|failing|flaky`).
- **Flaky test** (new in GLOSSARY.md): a test that passes and fails on the same Baseline. Not used to decide Killed.
- Suite (changes): `repeat` default 2.

## Success criteria
- **SC1** On `examples/shop`, `mutaspec baseline` reports "ready" and takes at most `repeat` × (time of one plain run of each Suite) + 60s.
- **SC2** On a fixture with one failing and one flaky test, both are reported by name in 100% of 10 runs.
- **SC3** After 20 runs that include Ctrl-C and ready timeouts, no `start` process is left running and the user's `git status` is unchanged.

## Out of scope
- Parallel worktrees and `parallel = true` (0005).
- Planting and running Mutants, and the rule that a kill needs a non-excluded test to fail (0004).
- JUnit XML from tools other than Maven Surefire/Failsafe-compatible writers; Gradle `init` support.
- Detecting Spring Boot 4 in `init` (open question from 0001; see decisions.md).

## Needs clarification
- None.
