# 0002 The agent suggests test changes; the person writes them

Status: accepted (2026-11-09)

## Context
Many mutation-testing agent skills generate tests to kill Survived Mutants. Tests written only to kill a specific Mutant often over-fit (assert on implementation detail), and the person does not learn where their test strategy is weak.

## Decision
mutaspec and its skills produce Suggestions (what is untested, which Level, a sketch of the check, nearest test file). They never edit the user's test files. The person (or their own separate agent session, by their choice) changes the tests, then starts a new Round.

## Consequences
- The score reflects the team's tests, and the loop teaches the team.
- Slower than auto-generated tests. A future opt-in "draft test" output may be added, but always as a separate file the person reviews.
