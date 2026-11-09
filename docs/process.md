# How we build mutaspec

We follow Anthropic's [AI-native SDLC playbook](https://claude.com/blog/the-ai-native-sdlc-playbook) (Aug 2026): each stage ends by committing a document the next stage reads. Where the playbook gives no template (spec.md), we use [GitHub spec-kit](https://github.com/github/spec-kit)'s structure.

```
 Plan            Design             Build                         Test / Review           Merge
 intent.md  ──►  spec.md  ──────►  plan.md ──► tests ──► code ──► verifier + checks ──►  PR ──► owner merges
   ▲ owner         ▲ owner          ▲ engineer approves           ▲ fresh context
   approves        approves         in plan mode                  reports only
```

## Stage 1 — Plan: intent.md
- Agent **interviews** you, one question at a time, then writes `intent/NNNN-name/intent.md` with: Problem, Proposed outcome, Affected users and systems, Constraints, Open questions.
- No solutions, libraries or acceptance criteria here. If the problem names a technology, restate it as a symptom.
- Gate: you edit and approve (`Status: approved`), commit. Git history is the audit trail.

Prompt: *"Read AGENTS.md and intent/0000-mutaspec/intent.md. Interview me one short question at a time about <feature>, then write intent/NNNN-<name>/intent.md from intent/_templates/intent.md. Show it to me before committing."*

## Stage 2 — Design: spec.md
- From the approved intent **and the real code**, the agent writes `spec.md`: user scenarios with priorities, Given/When/Then acceptance criteria (AC1…), edge cases, functional requirements (FR1…), key entities, measurable success criteria, out of scope.
- Unknowns are marked `[NEEDS CLARIFICATION: …]`. A spec with open items is not approved.
- Gate: you review, resolve open items, approve, commit `spec.md` next to `intent.md`.

## Stage 3 — Build: plan.md, tests, code
- Fresh session, plan mode, branch `intent/NNNN-name`. The agent writes `plan.md`: **Files that change, Order of work, Risks, Proof** (the tests that show each AC). You approve before any edit.
- Work the "Order of work" list: one step, one commit, test first (`test_acN_...` fails → code → passes). Never edit a test to make it pass; fix the code.
- If the work departs from the plan, update `plan.md` in the same commit. If the spec is wrong, stop and fix the spec first.
- Checks before each commit: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.

## Stage 4 — Test and review
- Run the `verifier` subagent (`.claude/agents/verifier.md`) in a fresh context: it runs the demo on `examples/shop` and checks every AC in `spec.md`. It reports; it does not fix.
- Review before the PR when the change adds behaviour, a file format, or agent-facing text.
- Changes to skills or AGENTS.md: run the skill evals before merge.

## Stage 5 — Merge
- PR description: what changes for users and why. The owner merges. Tags and releases need the owner.

## Habits
- One feature folder per branch and PR. Start each stage in a fresh session (`/clear`).
- Build v0.1 thin first (0001–0004) so a real score comes out of `examples/shop` early, then deepen.
- Every problem found later (bug, bad suggestion, slow run) becomes a new intent or an eval.
