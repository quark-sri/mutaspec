# mutaspec plan

## Goal

Give a team one number they can trust for "how good are our tests at catching bugs", per test Level, and a short list of concrete ways to raise it. Work on any project, any language, any test command, driven by a person or a coding agent.

## Who uses it

- **Developer / tester** on a project: wants to know which tests are weak and what to add.
- **Coding agent** (Claude Code, Codex, Copilot, Cursor…): runs mutaspec through the CLI and a skill, explains Survived Mutants, writes Suggestions.
- **Team lead / CI**: wants a score trend and a gate on pull requests.

## The workflow (one Round)

1. **Configure** — `mutaspec init` writes `mutaspec.toml`: source paths, Baseline ref, and one entry per Suite (unit, integration, api, ui) with `run` and optional `setup`, `start`, `ready`, `teardown`, `timeout`.
2. **Baseline** — run every Suite on the Baseline in a worktree, 2–3 times. All must pass. Tests that fail or flip are excluded from scoring and reported.
3. **Inject** — build the Mutant Set once: Rule Mutants (operators) plus Agent Mutants (realistic bugs from code and spec). Each is a patch in `.mutaspec/mutants/`. Validate: applies, builds, changes behaviour on the surface, not a duplicate.
4. **Run** — for each Mutant: reset the worktree to the Baseline, apply the patch, run the Suites (cheapest first), record Killed / Survived / Timeout / Invalid and which Suite killed it.
5. **Score** — Mutation Score overall and per Level. Report as Markdown, JSON (mutation-testing-elements schema) and HTML.
6. **Suggest** — the agent reads each Survived Mutant and writes a Suggestion: what behaviour is untested, which Level is the cheapest place to test it, a sketch of the check, the nearest existing test file.
7. **Improve** — the person changes the tests (on their branch).
8. **Next Round** — same Mutant Set, new tests. `mutaspec compare` shows score change and which Mutants are now Killed.

## Architecture

```
mutaspec CLI (Python, uv)
 ├─ config        mutaspec.toml → typed config
 ├─ workspace     git worktrees under .mutaspec/worktrees/, reset + apply patch
 ├─ suites        run commands, start/ready/teardown services, timeouts, ports
 ├─ baseline      repeated runs, flaky detection, excluded tests
 ├─ inject        operators (tree-sitter) ; import from universalmutator ; Agent Mutant intake + validation
 ├─ run           scheduler (sequential → parallel worktrees), result per Mutant per Suite
 ├─ score/report  score, Markdown/JSON/HTML (mutation-testing-elements)
 ├─ history       Rounds, compare
 └─ explain       context pack per Survived Mutant for the agent (diff, code, nearest tests, spec refs)
skills/           agent-facing instructions: run a Round, write Agent Mutants, write Suggestions
.claude-plugin/   packaging only
```

Key decisions:
- [ADR 0001](adr/0001-mutants-are-patches-run-in-worktrees.md): a Mutant is a git patch applied in a worktree; Suites are plain shell commands. This is what makes API and UI tests possible.
- [ADR 0002](adr/0002-agent-suggests-tests-user-writes-them.md): the agent suggests; the person writes tests.
- The Mutant Set is committed and reused, so score changes come from test changes, not from different bugs.

## Roadmap

| Milestone | Intents | Result |
|---|---|---|
| **v0.1 walking skeleton** | 0001, 0002, 0003 (rules, Python only), 0004 (sequential) | A real score for the example project's unit + API Suites. |
| **v0.2 the improvement loop** | 0003 (Agent Mutants), 0006, 0007, 0008 | Suggestions, Rounds, compare, Claude Code skill + plugin. |
| **v0.3 scale and teams** | 0005, 0009, 0010, more languages, parallel worktrees, UI Suite example | Diff-scoped runs, CI gate, self-evaluation benchmark. |

## Risks

- **Run time.** API and UI Suites per Mutant are slow. Mitigate: few, good Mutants (Agent Mutants, arid filter, diff scope), cheapest Suite first, stop at first kill in `fast` mode, parallel worktrees.
- **Flaky tests** give false Killed results. Mitigate: repeated Baseline, exclude flaky tests, optional re-run of a Killed Mutant.
- **Equivalent Mutants** lower the score unfairly. Mitigate: agent flags likely equivalents; a person decides.
- **Shared resources** (database, ports) between parallel worktrees. Mitigate: sequential first; `{port}` and `{worktree}` placeholders later.
