# Spec: CI gate (from intent.md)

Status: pre-draft. Intent: [intent.md](intent.md)

## User scenarios and acceptance

### S1 Gate a pull request (P1)
- **AC1** Given `min_score = 60` and a PR Round scoring 55%, Then `mutaspec ci` exits 1 and the summary states the threshold and score.
- **AC2** Given a PR with no changes under `source`, Then `mutaspec ci` exits 0 with "no source changes".

### S2 Short summary (P1)
- **AC3** The summary is under 60 lines, lists at most 10 Survived Mutants, and links or points to the full report.

### S3 Setup vs quality (P1)
- **AC4** Given a broken or flaky Baseline in CI, Then exit code is 3, not 1.

## Edge cases
- Budget too small for any Mutant: exit 0 with a warning, never a false pass on the score rule.

## Functional requirements
- **FR1** `mutaspec ci` = `run --diff <base> --budget <t>` + summary.
- **FR2** Config: `[gate] min_score`, `min_score_<level>`, `no_regression`.
- **FR3** GitHub Action wrapper; cache Mutant Set and baseline durations.

## Key entities
Round, Mutation Score.

## Success criteria
- **SC1** In `examples/shop`, the sample workflow passes a good PR and fails a PR that deletes an assertion.

## Out of scope
Posting to non-GitHub hosts directly.

## Needs clarification
- none
