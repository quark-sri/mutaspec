# Spec: per-Level scores

Status: approved when the PR merges (2026-11-18). Roadmap item 1 in docs/PLAN.md.

## Why
- One overall score hides where tests are weak. Unit tests may catch 80% of the bugs and API tests 20%.
- To decide where to add tests, users need a score for each Level.
- `mutaspec run` stops at the first Suite that catches a Mutant, so slower Suites never get a result.

## What the user sees
```text
$ mutaspec run --per-level
...
Score: 100.0% (4 of 4 Mutants caught; 0 survived, 0 invalid)
Per Level:
  unit         75.0%  (3 of 4)
  integration  25.0%  (1 of 4)
```
Without `--per-level`, a project with more than one Level gets the hint
`For a score per Level, run with --per-level (runs every Suite on every Mutant).`

## Acceptance criteria
- **AC1** Given `--per-level`, When a Suite catches a Mutant, Then the other Suites still run on it.
- **AC2** The score of Level L = Mutants caught by a Suite of Level L / Mutants scored at Level L. A Mutant is not scored at Level L when it is Invalid, or when a Suite of Level L broke on it.
- **AC3** The overall score keeps its meaning: caught by any Suite.
- **AC4** Without `--per-level`, the run is the same as before. When the Suites have more than one Level, the output names the flag.
- **AC5** The text output, `report.md` and `--json` show the score of each Level, and the result of each Suite on each Mutant.

## Out of scope
Comparing Levels across runs (Rounds); choosing which Level should test a Survived Mutant (Suggestions).
