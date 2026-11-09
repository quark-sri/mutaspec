# Spec: self-evaluation (from intent.md)

Status: pre-draft. Intent: [intent.md](intent.md)

## User scenarios and acceptance

### S1 Deterministic benchmark (P1)
- **AC1** Rule Mutant ids and scores for each example match stored golden files; any change shows a readable diff.

### S2 Agent benchmark (P2)
- **AC2** ≥ 80% of Agent Mutants are valid across runs; 2 of 3 runs must pass.
- **AC3** Suggestions name ≥ 70% of each example's known test gaps.

### S3 Dog-fooding (P2)
- **AC4** mutaspec's own unit-Level Mutation Score is in the README and does not drop between releases without a recorded reason.

## Edge cases
- An example's toolchain is missing on the machine: skip it with a clear message, never pass silently.

## Functional requirements
- **FR1** `uv run python evals/run.py` (deterministic) runs in CI.
- **FR2** `evals/run.py --agent --runs 3` before a release.
- **FR3** Each example has `KNOWN_GAPS.md` listing planted test gaps.

## Key entities
Mutation Score, Suggestion.

## Success criteria
- **SC1** All three examples run end to end on a clean machine with the documented toolchains.

## Out of scope
Public leaderboard.

## Needs clarification
- none
