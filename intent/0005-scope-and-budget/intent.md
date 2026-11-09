# Intent: scope and budget

Author: Srinivas. Status: draft. Part of [0000 mutaspec](../0000-mutaspec/intent.md).

## Problem
With API and UI suites one bug can take minutes to check, so a full run on a real project can take days. Users cannot wait that long, and most bugs in untouched or untested code tell them little that is new.

## Proposed outcome
Users can limit a run to what matters: only the code changed on their branch, only code the tests actually reach, or only as many bugs as fit in a time budget. Runs use several copies of the code at once when the machine allows, without suites getting in each other's way.

## Affected users and systems
- Developers on feature branches; CI on pull requests.
- Coverage reports the user already produces; local ports, databases and other shared resources.

## Constraints
- Untested code is reported as "not covered", never mixed into the score.
- Results must be the same whether bugs run one at a time or in parallel.

## Open questions
- Coverage per test level, or one combined report? Proposed: one combined report first.
