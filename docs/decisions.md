# Decision ledger

Every decision taken with the owner, newest last. One row per decision; never delete a row. If a decision changes, add a new row and mark the old one `superseded by Dnn`.
Hard-to-reverse decisions also get an ADR in [adr/](adr/); intents and specs record the detail. This file is the index.

**By:** `owner` = the owner chose it. `agent` = the agent chose the recommended option on the owner's instruction (2026-11-16); the owner confirms or changes it in the PR review.

| ID | Date | By | Decision | Why / rejected options | Recorded in |
|---|---|---|---|---|---|
| D01 | ≤ 2026-11-09 | owner | Name `mutaspec`; Python CLI built with `uv`. | — | intent 0001 |
| D02 | ≤ 2026-11-09 | owner | Hybrid bug sources: Rule Mutants (tree-sitter operators) + Agent Mutants (realistic, from code and requirements). | Rules alone miss realistic bugs; agents alone are not repeatable. | intent 0003 |
| D03 | ≤ 2026-11-09 | owner | A Mutant is a git patch applied in a worktree; Suites are shell commands with setup/start/ready/teardown, so API and UI tests work. | — | [ADR 0001](adr/0001-mutants-are-patches-run-in-worktrees.md) |
| D04 | ≤ 2026-11-09 | owner | The agent suggests tests and never edits the user's tests. | — | [ADR 0002](adr/0002-agent-suggests-tests-user-writes-them.md) |
| D05 | ≤ 2026-11-09 | owner | The Mutant Set is committed and reused across Rounds. | Scores between Rounds must be comparable. | intent 0007 |
| D06 | ≤ 2026-11-09 | owner | Report JSON uses the mutation-testing-elements schema, plus our own fields. | Existing viewers work. | spec 0004 |
| D07 | ≤ 2026-11-09 | owner | Process: Anthropic AI-native SDLC playbook (`intent.md → spec.md → plan.md`); spec.md layout from GitHub spec-kit; no tasks.md (task list = plan.md "Order of work"). | Playbook gives no spec template. | [process.md](process.md) |
| D08 | ≤ 2026-11-09 | owner | `.mutaspec/` writes its own `.gitignore` (worktrees and run output ignored; Mutant Set committable). Never edit the user's `.gitignore`. | — | intent 0001 |
| D09 | ≤ 2026-11-09 | owner | The source/test rule is per file (works for Go/JS colocated tests). Rust inline `#[cfg(test)]` is a spec edge case. | — | intent 0001 |
| D10 | ≤ 2026-11-09 | owner | One config file, `mutaspec.toml`, for every language; not inside `pyproject.toml` or `package.json`. | — | intent 0001 |
| D11 | ≤ 2026-11-09 | owner | Use universalmutator only if its licence is permissive. Result: its LICENSE is Apache-2.0, so allowed. | Permissive licences only. | intent 0003, [research.md](research.md) |
| D12 | 2026-11-10 | owner | v0.1 targets Java + Spring Boot (Maven, JUnit unit tests, REST API tests against the running app). Python rules move to v0.2; then TypeScript. | Reason in PLAN.md. | [PLAN.md](PLAN.md), intents 0000/0003/0010 |
| D13 | 2026-11-11 | owner | API tests are marked with JUnit `@Tag("api")`; `mutaspec init` writes a unit Suite and an api Suite. | — | spec 0001 (PR #3) |
| D14 | 2026-11-11 | owner | Project root = the folder where mutaspec runs (spec 0001 FR5 changed). | — | spec/plan 0001 (PR #4) |
| D15 | 2026-11-16 | owner | Baseline uses committed code (the `baseline` ref) only. Uncommitted changes are used only when the user asks (`--include-uncommitted`); otherwise a warning lists them. | Rejected: never include (too strict); include by default (Baseline no longer a commit, Mutant Set may not match). | intent 0002 |
| D16 | 2026-11-16 | owner | Baseline runs each Suite 2 times by default; configurable per Suite. | Rejected: 3 (breaks the 2× time target); 1 + re-check on kill (moves flaky detection into 0004). | intent 0002 |
| D17 | 2026-11-16 | owner | Per-test results come from the optional per-Suite `junit` glob of JUnit XML files (the field already exists, spec 0001 FR2); `init` now fills it in for Maven. Without it, a Suite is judged only by its exit code. | Rejected: auto-detect Maven folders (ties to Maven); Suite level only (one flaky test removes a whole Suite). Needs a change to `init` and the golden `examples/shop/mutaspec.toml`. | intent 0002, spec 0002 FR11 |
| D18 | 2026-11-16 | owner | If any Suite is broken on the clean code, the baseline is "not ready" and exits non-zero. All Suites run and every problem is reported at once. To go on, the user fixes the Suite or removes it from `mutaspec.toml` on purpose. | Rejected: ready with warnings (silently drops a test Level); stop at the first broken Suite (fix one at a time). | intent 0002 |
| D19 | 2026-11-16 | owner (asked) | All decisions taken with the owner are recorded in this ledger. | Decisions were scattered across an uncommitted HANDOFF.md, ADRs and intents. | [process.md](process.md) |
| D20 | 2026-11-16 | owner (asked) | For the rest of 0002, the agent uses its recommended option for each choice and records it here as `agent`; the owner checks them in the PR review. | Owner's instruction. | this ledger |
| D21 | 2026-11-16 | agent | Intent 0002 and spec 0002 go in one PR, both marked `approved`; merging the PR is the owner's approval. | Rejected: separate PRs per stage, as for 0001 (slower). | this PR |
| D22 | 2026-11-16 | agent | `repeat` means the number of baseline runs of a Suite; its default changes from 1 to 2. | Implements D16 with the field that already exists (spec 0001 FR2). Rejected: a new `baseline_repeat` field (two fields for one idea). | spec 0002 FR4 |
| D23 | 2026-11-16 | agent | Command: `mutaspec baseline [--include-uncommitted] [--json]`. | Matches the pre-draft spec and the 0001 CLI style. | spec 0002 FR1 |
| D24 | 2026-11-16 | agent | "Not ready" exits with code 3 (environment or setup error); Ctrl-C exits with 130. | Uses spec 0001 FR4 codes; 130 is the shell convention for Ctrl-C. Rejected: a new exit code. | spec 0002 FR7, AC12 |
| D25 | 2026-11-16 | agent | Worktree `.mutaspec/worktrees/base` at the `baseline` ref (detached). Created again on each baseline; kept after the run for inspection. | Clean start every time; kept so failures can be checked. Rejected: remove after run. | spec 0002 FR2 |
| D26 | 2026-11-16 | agent | Suites run one after another in config order. `setup` once per Suite; `start`, `ready`, `run` and stop on each repeat; `teardown` once at the end, always. | Simple and safe for shared services; parallel is 0005. Rejected: full setup on each repeat (slow). | spec 0002 FR3 |
| D27 | 2026-11-16 | agent | Per-test status: `pass`, `failing` (fails every run), `flaky` (passes and fails); skipped tests left out. Without `junit`, a Suite that fails on any run is `broken` ("flaky Suite" if it flips). With `junit`, a non-zero exit with no failed test in the XML is `broken`, and so is a Suite where no test passes. | Never count a failure that also happens on clean code; never hide a broken build behind per-test results. | spec 0002 FR5, FR6 |
| D28 | 2026-11-16 | agent | `init` writes `junit = "**/target/surefire-reports/TEST-*.xml"` in each Maven Suite. | Covers single and multi-module projects; both 0001 Suites run through Surefire, so Failsafe is not needed yet. | spec 0002 FR11, AC19 |
| D29 | 2026-11-16 | agent | Files matching `junit` are deleted in the worktree before each run. | Stops old results from an earlier run or Suite being read again. | spec 0002 edge cases |
| D30 | 2026-11-16 | agent | `{port}`: one free TCP port per run (bind to port 0), the same value in `start`, `ready` and `run`. | Avoids clashes with the user's own running app. | spec 0002 FR10, AC13 |
| D31 | 2026-11-16 | agent | `start` runs in its own process group; stop = SIGTERM, then SIGKILL after 10s. `ready` is polled every 1s. | Spring Boot and Maven fork child processes; stopping only the parent can leave the port taken. | spec 0002 FR3 |
| D32 | 2026-11-16 | agent | Results in `.mutaspec/runs/baseline.json` (written also when not ready); logs in `.mutaspec/runs/baseline/<suite>-<n>.log`; errors show the last 20 lines. | `runs/` is already git-ignored (D08). 0004 and 0005 read baseline.json. | spec 0002 FR8, FR9 |
| D33 | 2026-11-16 | agent | `--include-uncommitted` copies tracked edits and untracked, not ignored files into the worktree; it is a usage error (exit 2) when `baseline` is not `HEAD`. The warning lists the first 10 left-out files. | Uncommitted changes only make sense on top of HEAD. | spec 0002 AC16–AC18 |
| D34 | 2026-11-16 | agent | New glossary terms: **Baseline result**, **Flaky test**. | Used in code and reports from 0002 on. | GLOSSARY.md |
| D35 | 2026-11-16 | agent | Success criterion SC1 is "at most `repeat` × one plain run + 60s", not "under 2× the normal test time". | With 2 repeats plus app start-up, the old target could not be met. | spec 0002 SC1 |
| D36 | 2026-11-16 | agent | Spring Boot 4 detection stays open and out of scope for 0002. | Not part of the baseline; decide with the owner in a small fix or with 0003. | spec 0002 out of scope |

## Open (not yet decided)
- Should `init` also detect Spring Boot 4 (`spring-boot-starter-webmvc`)? Raised 2026-11-12 after building 0001.
