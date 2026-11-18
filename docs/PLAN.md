# mutaspec plan

## Goal

Give a team one number they can trust for "how good are our tests at catching bugs", per test Level, and a short list of concrete ways to raise it. Work on any project, any language, any test command, driven by a person or a coding agent.

## Who uses it

- **Developer / tester** on a project: wants to know which tests are weak and what to add.
- **Coding agent** (Claude Code, Codex, Copilot, Cursor…): runs mutaspec through the CLI and a skill, explains Survived Mutants, writes Suggestions.
- **Team lead / CI**: wants a score trend and a gate on pull requests.

## What works today (v0.1)

1. **Configure**: `mutaspec init` writes `mutaspec.toml` with `source`, `tests`, optional `build`, and one entry per Suite (`run`, plus optional `setup`, `start`, `ready`, `teardown`, `timeout`, `junit`). It detects Maven and Spring Boot; for other projects it writes a template.
2. **Run**: `mutaspec run` does the rest:
   - It checks the Baseline in a git worktree. Each Suite runs 2 times and must pass. With `junit`, failing and flaky tests are set aside.
   - It makes Rule Mutants with text rules (`<` to `<=`, `&&` to `||`, `+` to `-`, `true` to `false`, ...) and picks `--max` of them, the same ones each time.
   - For each Mutant it runs `build`, then the Suites from the fastest to the slowest, and stops at the first that catches it.
   - It prints the Mutation Score and each Survived Mutant as a diff, and writes `.mutaspec/runs/report.md`.
   - With `--per-level`, it runs every Suite on every Mutant and gives a score per Level (spec 0004).

`mutaspec baseline` runs only the first step, to set up the Suites.

## Architecture

```
mutaspec CLI (Python, uv, no runtime dependencies)
 ├─ config.py     mutaspec.toml -> typed config, plain error messages
 ├─ scaffold.py   init: detect the project, write a draft config
 ├─ worktree.py   the Baseline worktree under .mutaspec/worktrees/base
 ├─ process.py    run Suite commands in their own process group; timeouts; {port}
 ├─ junit.py      per-test results from JUnit XML
 ├─ baseline.py   run each Suite on the Baseline; ready or not ready
 ├─ mutants.py    Rule Mutants from text rules; apply and restore
 └─ runner.py     mutaspec run: each Mutant, score, report
```

Key decisions:
- [ADR 0001](adr/0001-mutants-are-patches-run-in-worktrees.md): Mutants are run in a git worktree; Suites are plain shell commands. This is what makes API and UI tests possible.
- [ADR 0002](adr/0002-agent-suggests-tests-user-writes-them.md): the agent suggests; the person writes tests.

## Roadmap

Ordered by what users are likely to ask for first. Each item becomes a short spec when we start it ([process](process.md)).

| Next | What the user gets |
|---|---|
| Better Rule Mutants | Fewer Mutants that do not build; more operators (removed calls, return values); one Mutant per line. |
| Saved Mutant Set and Rounds | Keep the Mutants in the repository, run them again after test changes, and compare two runs. |
| Faster runs | Only the code changed on a branch; a time budget; several worktrees at once. |
| Suggestions | A coding agent explains each Survived Mutant: what is not tested, at which Level, and a sketch of the check. People write the tests. |
| Agent Mutants | Realistic bugs written by a coding agent from the code and its requirements (validation, status codes, paging, error handling). |
| Agent packaging | Skills for Claude Code and other agents: "check how good my tests are". |
| CI gate | A short run on each pull request, with a summary and a minimum score. |
| Reports | HTML and the mutation-testing-elements JSON format. |
| Self-evaluation | Example projects with known test gaps that check mutaspec's own results. |

## Risks

- **Run time.** API and UI Suites per Mutant are slow. Mitigate: few, good Mutants (Agent Mutants, arid filter, diff scope), cheapest Suite first, stop at first kill in `fast` mode, parallel worktrees.
- **Flaky tests** give false Killed results. Mitigate: repeated Baseline, exclude flaky tests, optional re-run of a Killed Mutant.
- **Equivalent Mutants** lower the score unfairly. Mitigate: agent flags likely equivalents; a person decides.
- **Shared resources** (database, ports) between parallel worktrees. Mitigate: sequential first; `{port}` and `{worktree}` placeholders later.
