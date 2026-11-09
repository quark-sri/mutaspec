# Intent: CI gate

Author: Srinivas. Status: draft. Part of [0000 mutaspec](../0000-mutaspec/intent.md).

## Problem
Teams want test quality checked on every pull request, but a full run is too slow for CI, and nobody notices when test quality slowly drops.

## Proposed outcome
A pull request triggers a short run on the changed code within a time budget. The pull request gets a brief summary: score, bugs that got through on changed lines, top suggestions. The check fails when the team's rules are broken (minimum score, no drop). Setup problems are reported separately from quality problems.

## Affected users and systems
- Developers opening pull requests; reviewers; team leads.
- GitHub Actions first; other CI through a documented command.

## Constraints
- A broken or flaky setup must never look like poor test quality.

## Open questions
- Post the PR comment ourselves or leave it to the CI step? Proposed: produce Markdown; the GitHub Action posts it.
