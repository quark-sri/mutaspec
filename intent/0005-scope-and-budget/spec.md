# Spec: scope and budget (from intent.md)

Status: pre-draft. Intent: [intent.md](intent.md)

## User scenarios and acceptance

### S1 Only my changes (P1)
- **AC1** Given `--diff main` and a branch that changes 2 files, Then only Mutants on changed lines of those files run.

### S2 Only covered code (P2)
- **AC2** Given a coverage report where a line has 0 hits, Then no Mutant runs there and the report lists it under "not covered".

### S3 Time budget (P1)
- **AC3** Given `--budget 10m` and an estimate of 1 min per Mutant with `--jobs 1`, Then at most 10 Mutants run and the report says how many were skipped for budget.

### S4 Parallel (P2)
- **AC4** Given `--jobs 3`, Then three worktrees run at once, each Suite gets a distinct `{port}`, and results equal a `--jobs 1` run on the same Mutants.
- **AC5** Given a Suite with `parallel = false`, Then it never runs in two worktrees at once.

## Edge cases
- `--diff` ref not found: exit 2 with the ref name.
- Diff touches only test files: nothing to run; say so, exit 0.

## Functional requirements
- **FR1** Coverage input: Cobertura XML and LCOV.
- **FR2** Selection under budget: one Mutant per line, spread across files, Agent Mutants first.
- **FR3** Arid-code filter configurable (`arid = ["log.*", "metrics.*"]`).

## Key entities
Arid code; "not covered" and "skipped (budget)" result groups.

## Success criteria
- **SC1** `--jobs 3` on `examples/shop` is at least 2× faster than `--jobs 1` with identical results.

## Out of scope
Per-test impact analysis.

## Needs clarification
- none
