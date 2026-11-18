# mutaspec

Plants bugs in a git worktree, runs the project's own test suites against the clean code and each bug, and scores the tests. See [README.md](README.md), [docs/PLAN.md](docs/PLAN.md), terms in [GLOSSARY.md](GLOSSARY.md).

## Commands
- Checks before every commit: `uv run ruff check . && uv run ruff format --check . && uv run pytest`
- Demos: in `examples/calc`, `uv run mutaspec run` (Python only, seconds; must score 60%). In `examples/shop`, `uv run mutaspec init --force && uv run mutaspec run --max 10` (needs Java and Maven, about a minute; with `--per-level`, about 2.5 minutes and unit 70%, api 10%). `git status` must stay clean (the committed `examples/shop/mutaspec.toml` is the golden output of `init`).

## Conventions
- Work follows [docs/process.md](docs/process.md): a short `intent/NNNN-name/spec.md` the owner says yes to, then tests, then code. Build the smallest thing people can use; no config keys, files or flags for future features.
- Each acceptance criterion has a test named `test_acN_...`. Test first. If a test fails, fix the code, not the test.
- If the spec turns out wrong, change it in the same PR and say so.
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
