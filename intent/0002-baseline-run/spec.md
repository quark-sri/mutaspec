# Spec: baseline run (from intent.md)

Status: pre-draft. Intent: [intent.md](intent.md)

## User scenarios and acceptance

### S1 Confirm the project is ready (P1)
- **AC1** Given all Suites pass twice, When I run `mutaspec baseline`, Then it reports "ready" with each Suite's duration and writes `.mutaspec/runs/baseline.json`.
- **AC2** Given a Suite fails on both runs and has no JUnit XML, Then that Suite is `broken`, its output tail is shown, exit code 3.

### S2 Handle flaky tests (P1)
- **AC3** Given a Suite with JUnit XML where one test fails on one run and passes on the other, Then that test is listed `flaky`, excluded from kill decisions, and the Suite stays usable.

### S3 Services (P1)
- **AC4** Given a `ready` check that never succeeds within `ready_timeout`, Then that Suite stops, teardown runs, and the error says the service did not become ready.
- **AC5** Given I press Ctrl-C, Then teardown runs for every started Suite and the worktree is clean.

### S4 Safety (P1)
- **AC6** After any baseline run, the user's `HEAD`, branch and `git status` are unchanged.
- **AC7** Given uncommitted changes, Then they are used only with `--include-uncommitted`; otherwise a warning lists them.

## Edge cases
- A Suite fails consistently on only some tests (with JUnit XML): those tests are `failing`, excluded, and listed; Suite usable.
- Port already in use: pick another free port for `{port}`.

## Functional requirements
- **FR1** Lifecycle per Suite: setup → start (background) → poll ready → run → teardown (always).
- **FR2** Worktree at `.mutaspec/worktrees/base` checked out at the Baseline ref.
- **FR3** Record per Suite: duration, exit code, per-test results when `junit` is set.

## Key entities
Baseline, Suite, Baseline result (per-Suite status `ok|broken`, per-test `pass|failing|flaky`, duration).

## Success criteria
- **SC1** On `examples/shop`, baseline is ready in under 2× the normal test time.

## Out of scope
Parallel worktrees (0005).

## Needs clarification
- none
