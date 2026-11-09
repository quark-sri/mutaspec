# Intent: self-evaluation

Author: Srinivas. Status: draft. Part of [0000 mutaspec](../0000-mutaspec/intent.md).

## Problem
We claim mutaspec's scores and suggestions help teams, but without a benchmark we cannot show it, and a change to the bug rules or the skills could quietly make results worse.

## Proposed outcome
A small set of example projects with known test gaps, and a check that runs mutaspec on them and compares results with what we expect. Cheap checks run on every change; checks that need a paid agent run only before a release. mutaspec also measures its own tests.

## Affected users and systems
- mutaspec maintainers and contributors.
- `examples/` projects (Python API, TypeScript web app with UI tests, Java or Go service); `evals/`.

## Constraints
- Paid agent checks only on demand and before releases.

## Open questions
- Which third example language: Java or Go? Proposed: Java.
