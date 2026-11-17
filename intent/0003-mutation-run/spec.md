# Spec: mutation run (minimum usable tool)

Status: approved by the owner on 2026-11-17 ("Please proceed"). Replaces the earlier drafts for bug injection and Mutant run (D49).

## Why
- After `init` and `baseline`, mutaspec still gave no score. People could not use it.
- One command must take a project from "my tests pass" to "this is the score and these are the bugs no test caught".

## What the user sees
```text
$ mutaspec run --max 10
Baseline HEAD (9557337) in .mutaspec/worktrees/base
  unit (unit): ok, 0.0s, 0.0s
ready

5 of 5 Rule Mutants in 1 source files.
[1/5] SURVIVED src/calc/__init__.py:10  < -> <=  (0.0s)
[2/5] KILLED   src/calc/__init__.py:12  + -> - by unit  (0.0s)
...
Score: 60.0% (3 of 5 Mutants caught; 2 survived, 0 invalid)
Survived (no test caught these):
  src/calc/__init__.py:17  >= -> >
    - if subtotal >= FREE_SHIPPING_FROM:
    + if subtotal > FREE_SHIPPING_FROM:
Report: .mutaspec/runs/report.md
```

## Acceptance criteria
- **AC1** Given a project whose Baseline is ready, When I run `mutaspec run`, Then each Mutant is Killed, Survived, Timeout or Invalid, and the score is (Killed + Timeout) / (Killed + Timeout + Survived).
- **AC2** Given a Baseline that is not ready, Then no Mutant runs and the exit code is 3.
- **AC3** Rule Mutants change one operator or boolean word in a `source` file, never in strings, comments (also over several lines: docstrings, block comments, text blocks), imports, annotations or logging statements, and never in `tests` files.
- **AC4** `--max N` runs at most N Mutants, the same ones each time for the same code.
- **AC5** A Mutant that fails `build` is Invalid and not scored.
- **AC6** A Mutant that makes a Suite run longer than max(30 s, 3 × its Baseline duration), or longer than the Suite's own `timeout` if that is shorter, is Timeout.
- **AC7** With `junit`, only tests that passed on every Baseline run count for Killed; flaky and failing tests never do.
- **AC8** The user's files and git state do not change, and every Mutant is removed from the worktree after its run.
- **AC9** The text output and `.mutaspec/runs/report.md` show each Survived Mutant as a diff; `--json` gives the same data.

Tests: `tests/test_run.py`, `tests/test_mutants.py`, `tests/test_example_calc.py`.

## Out of scope (see the roadmap in docs/PLAN.md)
Per-Level scores, Agent Mutants, Suggestions, saved Mutant Sets and Rounds, resume, parallel runs, HTML and schema reports, a CI gate.
