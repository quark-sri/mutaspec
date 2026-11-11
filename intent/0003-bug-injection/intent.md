# Intent: bug injection

Author: Srinivas. Status: approved. Part of [0000 mutaspec](../0000-mutaspec/intent.md).

## Problem
A test-quality score is only as good as the bugs used to measure it. Mechanical bugs (`<` to `<=`) are cheap and repeatable, but many are trivial or change nothing. The bugs teams really ship (a missing validation, a wrong status code, an off-by-one in paging, a swallowed error) are the ones integration, API and UI tests should catch, and no open tool plants them for any language. If the set of bugs changes between runs, scores cannot be compared.

## Proposed outcome
Users get a fixed, reviewable set of bugs for their project, each stored as a small patch with a plain description. The set mixes mechanical bugs and realistic bugs written by a coding agent from the code and its requirements. Every bug is checked before use: it applies, it builds, it touches no test file, it is not a duplicate. The set is kept in the repository so every later run uses the same bugs.

## Affected users and systems
- Developers and agents creating the bug set; reviewers reading it.
- The user's source files (read only); requirement documents, API contracts and UI stories if the user points to them.
- `.mutaspec/mutants/` in the user's repository.

## Constraints
- Never change test files.
- No secrets or personal data in patches.
- Same input gives the same mechanical bugs.

## Open questions
- None. universalmutator may be used for languages we do not support yet: its LICENSE file is Apache-2.0 (docs/research.md). Languages after Java: Python, then TypeScript (docs/PLAN.md).
