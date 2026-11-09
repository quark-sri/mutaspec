# mutaspec

Measure how good your tests are by planting bugs and checking which ones your tests catch.

mutaspec injects bugs into a copy of your code (a git worktree), runs your **existing** unit, integration, API and UI tests against the clean baseline and against each bug, and gives a score:

```
bugs caught / bugs injected      (per test level and overall)
```

For each bug your tests miss, an AI agent explains why and suggests how to change the tests. You change the tests. You run mutaspec again against the **same** bugs and see the score move.

```
 baseline (HEAD) ──► run all suites ──► must pass (flaky tests are set aside)
        │
        ├─ + bug 1 (patch) ──► run suites ──► caught? ─┐
        ├─ + bug 2 (patch) ──► run suites ──► caught? ─┼─► score per level ─► suggestions ─► you improve tests
        └─ + bug N (patch) ──► run suites ──► caught? ─┘                                        │
                         ▲                                                                        │
                         └──────────────── next round, same bugs ◄────────────────────────────────┘
```

Status: design. See [docs/PLAN.md](docs/PLAN.md) and [intent/](intent/).

- Works with any language and any test command.
- Bugs come from two sources: rule-based changes (`<` to `<=`, `&&` to `||`, removed call…) and realistic bugs written by an agent from the code and its spec.
- Agent-agnostic: a CLI plus files, with skills and plugins for Claude Code and other coding agents.

Licence: [Apache-2.0](LICENSE).
