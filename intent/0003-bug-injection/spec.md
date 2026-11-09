# Spec: bug injection (from intent.md)

Status: pre-draft. Intent: [intent.md](intent.md)

## User scenarios and acceptance

### S1 Create Rule Mutants (P1, v0.1)
- **AC1** Given `examples/shop`, When I run `mutaspec inject --max 50`, Then at most 50 Rule Mutants are written, each as one `.patch` plus one entry in `mutants.json`, none under `tests`.
- **AC2** Running `inject` twice on unchanged code gives the same Mutant ids.
- **AC3** Given a candidate that does not apply or fails `build`, Then it is not added and the reason is in `rejected.json`.
- **AC4** Given two candidates that differ only in whitespace, Then one is kept.
- **AC5** Given a line that only calls a logger, Then no Mutant is made there by default.

### S2 Add Agent Mutants (P1, v0.2)
- **AC6** Given an Agent Mutant patch without `category` or `spec_ref`, When I run `mutaspec inject --add`, Then it is rejected and the missing fields are listed.
- **AC7** Given an Agent Mutant that changes a test file, Then it is rejected.

## Edge cases
- A file with syntax the parser cannot read: skipped and reported.
- Generated code (e.g. `*_pb2.py`): excluded by default patterns.

## Functional requirements
- **FR1** Operators (selective mutation): relational, arithmetic, logical connector, negation, boolean/constant, removed call, return value. Python via tree-sitter first.
- **FR2** Mutant id = short hash of the normalized patch.
- **FR3** `mutants.json` entry: id, file, line, origin `rule|agent`, operator or category, description, `spec_ref`, `why_realistic` (agent only).
- **FR4** Limits: `--max`, per-file cap, one Mutant per line by default; seeded sampling.
- **FR5** Agent Mutant categories: validation, boundary, error handling, wrong value/status, state/ordering, auth/permission, UI text/visibility, other.

## Key entities
Mutant, Mutant Set, Rule Mutant, Agent Mutant, Operator, Arid code.

## Success criteria
- **SC1** ≥ 90% of Rule Mutants for `examples/shop` are valid (apply and build).
- **SC2** A reviewer understands each Mutant from its description alone.

## Out of scope
Multi-bug Mutants; changing the DOM at runtime for UI tests.

## Needs clarification
- [NEEDS CLARIFICATION: where requirements live; proposed `spec = [...]` globs in config]
