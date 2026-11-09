# Spec: survivor analysis and suggestions (from intent.md)

Status: pre-draft. Intent: [intent.md](intent.md)

## User scenarios and acceptance

### S1 Context for the agent (P1)
- **AC1** Given a Survived Mutant, When I run `mutaspec explain <id> --json`, Then the output has the patch, ±20 lines of context, the Suites that ran, and the nearest test files.

### S2 Complete, usable Suggestions (P1)
- **AC2** Given Suggestions written by the agent, When `mutaspec suggestions check` runs, Then every Survived Mutant is covered by a Suggestion or an equivalence flag, and every Suggestion names a Level and a target test file.
- **AC3** Given 5 Survived Mutants in one function about input validation, Then the report groups them under one theme.

### S3 Equivalent Mutants (P1)
- **AC4** Given the agent flags a Mutant as likely Equivalent, Then it stays Survived and scored until a person runs `mutaspec mark-equivalent <id> --by human:<name>`; then it is excluded and the report shows who marked it.

### S4 Safety (P1)
- **AC5** No mutaspec command or shipped skill writes to files matched by `tests`.

## Edge cases
- Survived Mutant in code with no tests near it: Suggestion proposes a new test file path.

## Functional requirements
- **FR1** Suggestion fields: mutant ids, untested behaviour, recommended Level and why, sketch of the check, target test file, priority (high/med/low).
- **FR2** Output: `.mutaspec/runs/<round>/suggestions.md` and `suggestions.json`.

## Key entities
Suggestion, Equivalent.

## Success criteria
- **SC1** A reviewer rates ≥ 80% of Suggestions on `examples/shop` useful.
- **SC2** Applying the high-priority Suggestions by hand raises the next Round's score (checked in 0007).

## Out of scope
Writing tests for the user.

## Needs clarification
- none
