# Intent: survivor analysis and suggestions

Author: Srinivas. Status: draft. Part of [0000 mutaspec](../0000-mutaspec/intent.md).

## Problem
A score alone does not tell users what to do. Each bug that got through is a concrete gap, but reading raw patches is slow, and users do not know whether a unit, API or UI test is the right place to close it. Some surviving bugs change nothing at all and should not count against the team, but deciding that needs judgement.

## Proposed outcome
For each bug that got through, users get a short explanation: which behaviour no test checks, the cheapest test level that could check it, a sketch of the check, and the existing test file to put it in. Similar gaps are grouped into themes. Bugs that likely change nothing are flagged, and a person decides. Users then change their tests themselves.

## Affected users and systems
- Developers and testers improving tests; the coding agent writing the suggestions.
- The run results from 0004; the user's code, tests and requirement documents (read only).

## Constraints
- Never edit the user's test files (ADR 0002).
- Only a person marks a bug as "changes nothing" (Equivalent).

## Open questions
- Always prefer the lowest test level that can catch the bug? Proposed: yes, and say when only a higher level can.
