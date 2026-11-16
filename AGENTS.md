# mutaspec

Plants bugs in a git worktree, runs the project's own test suites against the clean code and each bug, and scores the tests. See [README.md](README.md), [docs/PLAN.md](docs/PLAN.md), terms in [GLOSSARY.md](GLOSSARY.md).

## Commands
- Checks before every commit: `uv run ruff check . && uv run ruff format --check . && uv run pytest`
- Demo / golden fixture: in `examples/shop`, `uv run mutaspec init --force && uv run mutaspec config check`; `git status` must stay clean (the committed `mutaspec.toml` is the golden output). From v0.1: `uv run mutaspec run`; review the report diff on any output change.

## Conventions
- Work follows [docs/process.md](docs/process.md): `intent.md` → `spec.md` → `plan.md` → tests → code, in `intent/NNNN-name/`. Do not write code for a feature whose spec.md is not `approved`.
- Each acceptance criterion has a test named `test_acN_...`. Test first. If a test fails, fix the code, not the test.
- If work departs from plan.md, update plan.md in the same commit. If the spec is wrong, stop and say so.
- Use GLOSSARY.md terms in code, docs and commits; never the _Avoid_ words.
- Decisions that are hard to reverse go in `docs/adr/`.
- Dependencies: permissive licences only (MIT, Apache-2.0, BSD). No GPL/AGPL.

## Architecture
- Python CLI (`uv`). Core is agent-agnostic: CLI + files. `skills/` and `.claude-plugin/` hold instructions and packaging only, no logic.
- A Mutant is a git patch applied in a worktree under `.mutaspec/worktrees/`; Suites are shell commands ([ADR 0001](docs/adr/0001-mutants-are-patches-run-in-worktrees.md)).

## Things Claude gets wrong
- Running anything in the user's working tree. Never: only in `.mutaspec/worktrees/`.
- Letting a Mutant touch test files. A Mutant changes source files only.
- Writing tests for the user to kill Survived Mutants. mutaspec suggests; people write tests ([ADR 0002](docs/adr/0002-agent-suggests-tests-user-writes-them.md)).
- Marking a Mutant `equivalent`. Only a person does.
- Counting a failure of a flaky or already-failing test as a kill.
