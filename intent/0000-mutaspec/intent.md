# Intent: mutaspec (product)

Author: Srinivas. Status: draft.

## Problem
Teams cannot tell how good their tests are at catching bugs. Line coverage says which code ran, not whether a wrong result would be noticed. This affects developers and testers who own unit, integration, API and UI test suites, and leads who must decide where to invest in tests. Existing mutation tools work for one language's unit tests only, so API and UI suites, often the most expensive ones, are never measured.

## Proposed outcome
A team plants a fixed set of bugs in a copy of their code, runs their existing test suites against the clean code and against each bug, and gets the percentage of bugs caught, overall and per test level. For each bug that got through, they get a plain explanation and a suggestion for how to test it. They change their tests, run again against the same bugs, and see the score move. A coding agent can drive the whole loop.

## Affected users and systems
- Developers and testers on any project in any language, using git.
- Coding agents (Claude Code and others) acting for them.
- Team leads and CI pipelines that want a trend and a gate.
- The user's repository (read), their test commands and local services (run), never their working tree (unchanged).

## Constraints
- Never change the user's working tree or test files.
- Work with any test command; do not depend on one language's test runner.
- Open source, permissive licence, permissive dependencies only.
- Agent-agnostic core; agent packaging holds no logic.
- The agent suggests test changes; people write them.

## Open questions
- None blocking. Feature intents 0001–0010 hold the detail.
