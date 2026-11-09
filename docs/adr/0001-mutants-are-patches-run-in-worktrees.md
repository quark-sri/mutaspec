# 0001 A Mutant is a git patch applied in a worktree; Suites are shell commands

Status: accepted (2026-11-09)

## Context
Classic tools (Stryker, PIT, mutmut) change code in memory and drive one unit-test runner. They cannot start a service and run API or UI tests against it. We want one score across unit, integration, API and UI Suites.

## Decision
- A Mutant is a unified diff (`.patch`) against the Baseline, touching source files only.
- mutaspec creates git worktrees under `.mutaspec/worktrees/`, resets each to the Baseline, applies one patch, and runs each Suite as a shell command (with optional setup/start/ready/teardown).
- Killed means: a Suite fails with the Mutant where it passed on the Baseline.

## Consequences
- Any language and any test framework work.
- Each Mutant costs a full build and Suite run: far slower than in-memory tools. We need small, good Mutant Sets, scoping and parallel worktrees.
- Patches are readable, reviewable and can be committed, which makes the frozen Mutant Set possible.
- We can import Mutants from other tools if they can export diffs.
