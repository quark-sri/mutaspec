# Spec: project config and CLI (from intent.md)

Status: pre-draft. Intent: [intent.md](intent.md)

## User scenarios and acceptance

### S1 Set up a project (P1)
- **AC1** Given a git repo with `pyproject.toml` and `tests/`, When I run `mutaspec init`, Then `mutaspec.toml` is written with `source`, `tests` and one `unit` Suite using pytest.
- **AC2** Given `mutaspec.toml` exists, When I run `mutaspec init`, Then it is not overwritten unless I pass `--force`.

### S2 Find config mistakes early (P1)
- **AC3** Given `source` and `tests` patterns overlap, When any command loads the config, Then it stops with an error naming the overlapping paths.
- **AC4** Given a Suite with an unknown `level` or no `run`, When I run `mutaspec config check`, Then the error names the Suite and field, exit code 2.
- **AC5** Given a directory that is not a git repo, When I run any command, Then it stops with "mutaspec needs a git repository".

### S3 Agents read results (P2)
- **AC6** Every command accepts `--json` and then prints one JSON object on stdout.

## Edge cases
- Monorepo with several languages: `init` writes one Suite per detected tool, all commented for review.
- Unknown project type: `init` writes a commented template and says so.

## Functional requirements
- **FR1** Detect pytest, npm/pnpm test, mvn/gradle test, go test, cargo test.
- **FR2** Config fields: `[project] baseline, source, exclude, tests, spec, build`; `[[suites]] name, level, run, setup, start, ready, ready_timeout, teardown, timeout, junit, repeat, parallel`.
- **FR3** Placeholders `{port}` and `{worktree}` allowed in Suite commands.
- **FR4** Exit codes: 0 ok, 1 quality result below threshold, 2 usage/config error, 3 environment/setup error.

Example:
```toml
[project]
baseline = "HEAD"
source = ["src/**/*.py"]
tests = ["tests/**"]

[[suites]]
name = "unit"
level = "unit"
run = "uv run pytest tests/unit -q"
timeout = "120s"

[[suites]]
name = "api"
level = "api"
start = "uv run uvicorn shop.app:app --port {port}"
ready = "curl -sf http://localhost:{port}/health"
run = "uv run pytest tests/api -q --base-url http://localhost:{port}"
timeout = "300s"
```

## Key entities
Suite, Level, Baseline (see GLOSSARY.md).

## Success criteria
- **SC1** On `examples/shop`, `mutaspec init && mutaspec config check` succeeds with no edits.

## Out of scope
Running anything (0002+); non-git projects.

## Needs clarification
- none
