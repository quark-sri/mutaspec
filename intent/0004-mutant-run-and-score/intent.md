# Intent: mutant run and score

Author: Srinivas. Status: draft. Part of [0000 mutaspec](../0000-mutaspec/intent.md).

## Problem
Teams have no number for how many real-looking bugs their tests catch, and no way to see that, for example, unit tests are strong while API tests catch almost nothing. Without that, they cannot decide where to improve tests.

## Proposed outcome
Users run each planted bug against the same suites as the clean code and get the percentage of bugs caught, overall and per test level (unit, integration, API, UI), plus the list of bugs that got through. Results are readable by people (Markdown, HTML) and tools (JSON in a common format). A long run can be stopped and resumed.

## Affected users and systems
- Developers, testers, leads; agents reading results.
- The worktree from 0002 and bug set from 0003; the user's suites and services.

## Constraints
- A bug counts as caught only if a test that passed on the clean code fails.
- Flaky tests never count as catching a bug.
- The user's working tree stays unchanged.

## Open questions
- Run every suite for every bug (per-level scores, slow) or stop at the first failing suite (fast, overall score only)? Proposed: both modes; pick by estimated time, print the estimate first.
