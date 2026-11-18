# How we build mutaspec

Small steps that people can use. Each step has one short spec, one branch and one pull request.

```
 spec.md  ──►  tests  ──►  code  ──►  checks + demo  ──►  PR  ──►  owner merges
  owner OKs     test first             (verifier for bigger features)
```

## 1. Spec
- Write `intent/NNNN-name/spec.md` from [the template](../intent/_templates/spec.md): why, what the user sees, acceptance criteria (AC1…), out of scope. One page at most.
- The owner says yes (in the chat or by merging). For a small change, the PR description is enough.

## 2. Build
- Work on a new branch from the newest `main`.
- Test first: each acceptance criterion gets a test named `test_acN_...`. If a test fails, fix the code, not the test.
- Commit in small steps. Checks before each commit: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- If the spec turns out wrong, change the spec in the same PR and say so.

## 3. Check
- Run the demos: `mutaspec run` in `examples/calc` (Python, seconds) and in `examples/shop` (Java and Maven, about a minute). `git status` must stay clean.
- For a bigger feature, run the `verifier` subagent in a fresh context. It reports and does not fix.

## 4. Merge
- PR description: what changes for users and why. The owner merges. Tags and releases need the owner.

## Decisions
- Decisions taken with the owner, and decisions that are hard to reverse, get a row in [decisions.md](decisions.md) in the same commit.
- Architecture decisions go in [docs/adr/](adr/).

## Habits
- Ship the smallest thing people can use, then improve it from what they report.
- Do not build for a future feature. A config key, a file or a flag comes with the feature that reads it.
- Every problem found later (bug, slow run, bad Mutant) becomes a test or a roadmap item.
