# Plan: baseline run (from spec.md, 2026-11-17)

Status: approved (merging the PR is the approval). Decisions behind this plan: [docs/decisions.md](../../docs/decisions.md) D37–D45.

## Approach
- Still no runtime dependencies: `subprocess`, `os.killpg`, `signal`, `socket`, `xml.etree`, `pathlib.Path.glob`, `time.monotonic`.
- **Project folder in the worktree (D37).** `git worktree add` checks out the whole repository. When the project root is a subfolder of the repo (as with `examples/shop`), Suites run in `<worktree>/<root relative to git toplevel>`. This applies FR2 to D14.
- Every Suite command (`setup`, `start`, `ready`, `run`, `teardown`) runs through `sh -c` with `start_new_session=True`. That gives each one its own process group, which mutaspec stops as a whole: SIGTERM, then SIGKILL after `STOP_GRACE` (10 s; a module constant that tests can patch). Terminal Ctrl-C then reaches only mutaspec (D44).
- Ctrl-C: `KeyboardInterrupt` passes through `try/finally` blocks that stop the groups and run `teardown`. SIGINT is ignored while cleanup runs, so a second Ctrl-C cannot skip `teardown`. `cli.main` maps the interrupt to exit 130.
- `{port}`: only the literal text `{port}` is replaced. Other braces (shell `${VAR}`) are left as they are (D41).
- A Suite with no `timeout` has no time limit (D42).
- `durations[n]` = wall time of one repeat, from `start` to stop (from `run` to its end when there is no `start`). A Mutant run costs the same, and 0005 plans with this number (D38).
- `baseline.json` from an earlier run is deleted at start. A run stopped by Ctrl-C writes none, so 0004 can never read an old "ready" (D40).
- Commands return an optional `exit_code` in `Output`. For "not ready", `--json` prints `ok: false, exit_code: 3, ready: false, suites: [...]`, with no `error` object, because this is a result and not a usage error (D39).
- The list of uncommitted files and the `--include-uncommitted` copy are both limited to the project root (`git diff --name-only HEAD -- .` plus `git ls-files --others --exclude-standard -- .`). Files are copied into the worktree; files deleted in the working tree are deleted there too (D43).
- Per-test status: each run's XML is parsed into `{classname#name: passed|failed|skipped}`. Over the runs, the result is `pass`, `failing` or `flaky` (FR5). The Suite rules in FR6 are applied after the last repeat.

## Files that change
- `src/mutaspec/config.py`: `repeat` default 1 → 2 (FR4).
- `src/mutaspec/worktree.py` (new): output folders that git always ignores (D46), git toplevel and the project's relative path, `create_base(config, include_uncommitted)` (remove/prune, then `worktree add --detach <ref>`), `uncommitted_files(root)`, copying files for AC17, a bad-ref error (exit 2), AC18 (exit 2).
- `src/mutaspec/process.py` (new): `free_port()`, `spawn(cmd, cwd, log)`, `run(cmd, cwd, log, timeout) -> (code, seconds, timed_out)`, `stop(proc)` (process group), `tail(log, 20)`.
- `src/mutaspec/junit.py` (new): `read_results(folder, glob) -> dict[str, str]`, `clear(folder, glob)` (D29), `combine(runs) -> {id: pass|failing|flaky}`.
- `src/mutaspec/baseline.py` (new): the Suite lifecycle (FR3), status rules (FR6, FR7), `BaselineResult` → `baseline.json` (FR8), logs at `.mutaspec/runs/baseline/<suite>-<n>.log`, `-setup.log`, `-teardown.log` (FR9), text lines.
- `src/mutaspec/cli.py`: `baseline [--include-uncommitted] [--json]`, the exit code taken from `Output`, `KeyboardInterrupt` → 130.
- `src/mutaspec/scaffold.py` + `examples/shop/mutaspec.toml`: the `junit` line in each Maven Suite (FR11).
- `tests/conftest.py`: `suite_repo` fixture (a git repo with a committed `mutaspec.toml` whose Suites call small Python scripts through `sys.executable`), and helpers to write JUnit XML and count runs in a counter file under `tmp_path`.
- `tests/test_baseline.py`, `tests/test_worktree.py`, `tests/test_junit.py`, `tests/test_process.py` (new). Update `tests/test_config.py::test_load_defaults` (repeat 2) and `tests/test_init.py` (AC19).
- `AGENTS.md`: add `uv run mutaspec baseline` to the demo line (needs Java and Maven).
- `intent/README.md`: 0002 → `done` after the verifier passes.

## Order of work (one commit each; test first; checks pass before each commit)
1. [x] `repeat` default 2. Test: AC9 (default 2; `repeat = 3` is kept).
2. [x] `worktree.py`: create the base worktree (also in a subfolder project), recreate it, bad ref, uncommitted warning list (first 10 + "and N more"), `--include-uncommitted` copy, non-HEAD error. Tests: AC15 (git state of the user tree), AC16, AC17, AC18, edge "bad ref", edge "worktree exists".
3. [ ] `process.py`: process groups, timeout, stop with grace, free port, log tail. Tests: AC14 (unit level), a child process is killed with its group, `free_port` can be bound.
4. [ ] `junit.py`: parse Surefire XML (failure, error, skipped), clear old files, combine runs. Tests: FR5 table, AC5/AC6 at unit level.
5. [ ] `baseline.py` + CLI, Suites without services: lifecycle without `start`, repeats, FR6 without `junit`, `baseline.json`, logs, text output, `--json`, exit codes. Tests: AC1, AC2, AC3, AC4, AC7, AC9 (end to end), edge "setup failed" (no repeats, teardown runs), edge "teardown fails".
6. [ ] `junit` in the baseline: AC5, AC6, AC8, edges "junit matches no files" and "no test passes", D29 old XML. SC2 (10 runs, both names reported every time).
7. [ ] Services: `start`/`ready`/stop/`teardown`, `{port}`. Tests: AC10, AC11, AC13, AC14 (end to end), edge "start exits before ready".
8. [ ] Ctrl-C: subprocess `python -m mutaspec baseline`, SIGINT to its pid. Tests: AC12 (exit 130, start pid and child pid dead, teardown marker written, no `baseline.json`), AC15 after Ctrl-C, SC3 (20 runs mixing Ctrl-C and ready timeouts; `ready_timeout = "1s"`, grace patched down).
9. [ ] `init` writes `junit`; update the golden file. Tests: AC19, the existing SC1 golden test. Manual: `uv run mutaspec baseline` in `examples/shop` says "ready" (SC1 time check). Update the AGENTS.md demo line. Then the verifier; then `intent/README.md` → done.

## Risks
- **Nested worktree in `examples/shop`**: the base worktree holds a full copy of the mutaspec repo under `examples/shop/.mutaspec/worktrees/base`. It is git-ignored by `.mutaspec/.gitignore`. Check that pytest/ruff in the repo root do not collect it (add `.mutaspec` to ruff `extend-exclude` and pytest `norecursedirs` if needed).
- **Process groups on macOS vs Linux**: `os.killpg` behaves the same on both. Windows is not supported in v0.1 (POSIX only, stated in the error if `os.killpg` is missing).
- **Free-port race**: the port is closed before `start` binds it; another process can take it. This is rare, and the result is "service stopped before it was ready", which the user can see.
- **Maven `-q` and Surefire XML**: reports are written even with `-q`. A compile error writes no XML → AC8 path. Check by hand in step 9.
- **Test time**: the lifecycle tests use short Python scripts and `ready_timeout = "1s"`, and patch `STOP_GRACE`. SC3's 20 runs must stay under ~30 s; if slower, mark it `slow` but still run it in the default suite.
- **Flaky fixtures for flaky tests**: flips are made deterministic with a counter file (run 1 fails, run 2 passes), never with randomness.

## Proof
- `tests/test_baseline.py::test_ac1_…` … `test_ac14_…`, `test_sc2_…`, `test_sc3_…`, edge tests: AC1–AC14, SC2, SC3.
- `tests/test_worktree.py::test_ac15_…` … `test_ac18_…`: AC15–AC18.
- `tests/test_config.py::test_ac9_…`, `tests/test_init.py::test_ac19_…`, `tests/test_cli.py::test_sc1_…` (golden): AC9, AC19, FR11.
- Demo: in `examples/shop`, `uv run mutaspec init --force && uv run mutaspec config check && uv run mutaspec baseline` prints "ready" with durations for `unit` and `api`, exits 0, takes at most 2 × one plain run + 60 s (SC1), and `git status` stays clean.
- Checks: `uv run ruff check . && uv run ruff format --check . && uv run pytest`; then the `verifier` subagent.
