# Intent: baseline run

Author: Srinivas. Status: draft. Part of [0000 mutaspec](../0000-mutaspec/intent.md).

## Problem
A planted bug only counts as caught if a test fails with the bug and passed without it. If tests already fail or fail at random on the clean code, every score is wrong, and users find out only after a long run. Users also cannot tell up front whether their API or UI suites can even start outside their normal setup.

## Proposed outcome
Before any bugs are planted, users run their suites on the clean code in a separate copy, a few times. They get a clear answer: ready, or exactly what is broken. Tests that fail or flip are listed and left out of scoring, never ignored silently. Run times are recorded for later planning.

## Affected users and systems
- Developers and agents preparing a run; CI.
- The user's test commands and local services (databases, servers, browsers).
- Git worktrees under `.mutaspec/`; the user's working tree stays unchanged.

## Constraints
- Never run anything in the user's working tree.
- Always stop started services, also on errors and Ctrl-C.

## Open questions
- Use uncommitted changes as the clean code? Proposed: only when asked; warn otherwise.
- How many repeats by default? Proposed: 2, configurable per suite.
