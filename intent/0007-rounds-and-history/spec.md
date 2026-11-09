# Spec: rounds and history (from intent.md)

Status: pre-draft. Intent: [intent.md](intent.md)

## User scenarios and acceptance

### S1 Compare two Rounds (P1)
- **AC1** Given two Rounds on the same Mutant Set, When I run `mutaspec compare`, Then I see the score per Level for both and the change.
- **AC2** Given a Mutant Survived in Round 1 and Killed in Round 2, Then it is listed under "newly killed" with the killing Suite.
- **AC3** Given a Mutant Killed in Round 1 and Survived in Round 2, Then it is listed under "regressions"; with `--fail-on-regression` exit code is 1.
- **AC4** Given the Mutant Set changed between Rounds, Then compare warns and compares only shared Mutants.

### S2 Fast re-check (P2)
- **AC5** Given `mutaspec run --only-survivors`, Then only last Round's Survived Mutants run, and the overall score merges with last Round's other results, marked as merged.

## Edge cases
- Stale Mutants after source changes: listed; `mutaspec inject --refresh` rebuilds them with new ids and records the link old → new.

## Functional requirements
- **FR1** Round record: id, time, Baseline commit, Mutant Set hash, mode, scores per Level, counts per status.
- **FR2** `.mutaspec/history.jsonl`: one line per Round.

## Key entities
Round, Stale.

## Success criteria
- **SC1** On `examples/shop`: Round 1, apply two Suggestions by hand, Round 2; compare shows a higher API score and the matching newly killed Mutants.

## Out of scope
Hosted dashboard.

## Needs clarification
- none
