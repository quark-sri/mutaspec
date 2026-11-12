# intent/

Each feature has one folder with a chain of three documents, following Anthropic's [AI-native SDLC playbook](https://claude.com/blog/the-ai-native-sdlc-playbook):

| File | Stage | Says | Written by | Gate |
|---|---|---|---|---|
| `intent.md` | Plan | what is wanted, why, under which constraints | agent interviews the owner | owner approves (merge) |
| `spec.md` | Design | user scenarios, acceptance criteria, requirements | agent from the approved intent + code | owner approves; no `NEEDS CLARIFICATION` left |
| `plan.md` | Build | files that change, order of work, risks, proof | agent in plan mode from the approved spec | engineer approves before any edit |

The playbook gives no spec.md template; ours follows [GitHub spec-kit](https://github.com/github/spec-kit). Templates: [_templates/](_templates/). How to run the chain: [docs/process.md](../docs/process.md).

| # | Feature | Milestone | intent | spec | plan |
|---|---|---|---|---|---|
| 0000 | [mutaspec (product)](0000-mutaspec/intent.md) | all | approved | — | — |
| 0001 | [Project config and CLI](0001-project-config-and-cli/) | v0.1 | done | done | done |
| 0002 | [Baseline run](0002-baseline-run/) | v0.1 | draft | pre-draft | — |
| 0003 | [Bug injection](0003-bug-injection/) | v0.1 / v0.2 | approved | pre-draft | — |
| 0004 | [Mutant run and score](0004-mutant-run-and-score/) | v0.1 | draft | pre-draft | — |
| 0005 | [Scope and budget](0005-scope-and-budget/) | v0.3 | draft | pre-draft | — |
| 0006 | [Survivor analysis and Suggestions](0006-survivor-analysis-and-suggestions/) | v0.2 | draft | pre-draft | — |
| 0007 | [Rounds and history](0007-rounds-and-history/) | v0.2 | draft | pre-draft | — |
| 0008 | [Agent packaging](0008-agent-packaging/) | v0.2 | draft | pre-draft | — |
| 0009 | [CI gate](0009-ci-gate/) | v0.3 | draft | pre-draft | — |
| 0010 | [Self-evaluation](0010-self-evaluation/) | v0.3 | draft | pre-draft | — |

"pre-draft": the spec was sketched early with the research. Review it again after its intent is approved, before approving the spec.
Status values: `draft` → `approved` → `done` (or `dropped`).
