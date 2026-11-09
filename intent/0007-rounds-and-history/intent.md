# Intent: rounds and history

Author: Srinivas. Status: draft. Part of [0000 mutaspec](../0000-mutaspec/intent.md).

## Problem
Improving tests takes several passes. Users cannot see what their last test changes achieved, and if the planted bugs differ between runs, a score change may come from the bugs, not the tests. They also cannot spot when a test change makes things worse.

## Proposed outcome
Every run is recorded. Users compare any two runs on the same bugs and see the score change overall and per level, which bugs are now caught, and which bugs are no longer caught. They can re-check only the bugs that got through last time for fast feedback. When code changes break some planted bugs, they are told and can refresh them.

## Affected users and systems
- Developers iterating on tests; leads watching the trend; CI.
- Run results in `.mutaspec/`; a short history file that can be committed.

## Constraints
- Only compare results on the same bugs; say clearly when the sets differ.

## Open questions
- Commit the history file by default? Proposed: yes, one summary line per run.
