# Spec: mutant run and score (from intent.md)

Status: pre-draft. Intent: [intent.md](intent.md)

## User scenarios and acceptance

### S1 Classify each Mutant (P1)
- **AC1** Given a Mutant that makes a test fail which passed on the Baseline, Then it is Killed, and the result records the Suite (and test names when JUnit XML is set).
- **AC2** Given a Mutant where only a `flaky` test fails, Then it is Survived.
- **AC3** Given a Mutant that makes a Suite exceed its timeout, Then it is Timeout (counted as caught) and teardown runs.

### S2 Score (P1)
- **AC4** Given 10 scored Mutants with 6 Killed, 1 Timeout, 3 Survived, Then the overall score is 70.0%.
- **AC5** In `full` mode the report shows a score per Level; in `fast` mode only the overall score, with the reason.

### S3 Long runs (P2)
- **AC6** Given a Round stopped after 4 of 10 Mutants, When I run `mutaspec run --resume`, Then only the remaining 6 run.
- **AC7** After a Round, the worktree is reset and the user's working tree is unchanged.

### S4 Reports (P1)
- **AC8** `mutaspec report --format json` validates against the mutation-testing-elements schema.

## Edge cases
- Patch no longer applies → Stale, not scored.
- Build fails with the Mutant → Invalid, not scored.

## Functional requirements
- **FR1** Per Mutant: reset worktree to Baseline, apply patch, run Suites, classify Killed / Survived / Timeout / Invalid / Stale.
- **FR2** Suite timeout = max(baseline duration × `timeout_factor` (default 3), floor 30 s), or the Suite's own `timeout`.
- **FR3** `fast` mode: Suites in order of baseline duration, stop at first kill.
- **FR4** Score = (Killed + Timeout) / (Killed + Timeout + Survived). Per Level L: Mutants killed by any Suite of Level L / scored Mutants.
- **FR5** Reports: Markdown, HTML, JSON (mutation-testing-elements + `mutaspec` extension fields: level results, origin, spec_ref).

## Key entities
Round, Killed, Survived, Timeout, Invalid, Stale, Mutation Score.

## Success criteria
- **SC1** On `examples/shop` (planted weak API tests), the API-Level score is clearly lower than unit, and numbers match a hand count.

## Out of scope
Parallel worktrees and diff scope (0005); Suggestions (0006).

## Needs clarification
- none
