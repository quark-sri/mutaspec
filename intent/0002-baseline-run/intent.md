# Intent: baseline run

Author: Srinivas. Status: approved. Part of [0000 mutaspec](../0000-mutaspec/intent.md).

## Problem
A planted bug only counts as caught if a test fails with the bug and passed without it. If tests already fail or fail at random on the clean code, every score is wrong, and users find out only after a long run. Users also cannot tell up front whether their API or UI suites can even start outside their normal setup.

## Proposed outcome
Before any bugs are planted, users run their suites on the clean code in a separate copy, a few times. They get a clear answer: ready, or exactly what is broken. Every suite is tried, so all problems show at once. If any suite is broken, the answer is "not ready"; a suite is never dropped silently. Tests that fail or flip are listed by name where the suite reports results per test, and left out of scoring, never ignored silently. Run times are recorded for later planning.

## Affected users and systems
- Developers and agents preparing a run; CI.
- The user's test commands and local services (databases, servers, browsers).
- Git worktrees under `.mutaspec/`; the user's working tree stays unchanged.

## Constraints
- Never run anything in the user's working tree.
- Always stop started services, also on errors and Ctrl-C.
- The clean code is committed code. Uncommitted changes are used only when the user asks; otherwise the user is warned which files are left out.

## Open questions
- None. Answered 2026-11-16 ([decisions](../../docs/decisions.md) D15–D18): committed code only unless asked, with a warning; 2 runs per suite by default, configurable per suite; per-test results where the suite writes them; any broken suite means "not ready".
