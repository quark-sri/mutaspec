# Plan: project config and CLI (from spec.md, 2026-11-11)

Status: approved.

## Approach
- Python ≥ 3.13, `uv`, build backend hatchling (MIT). **No runtime dependencies**: `argparse`, `tomllib`, `xml.etree`, `subprocess`, `PurePath.full_match` (for `**` globs). Dev: pytest (MIT), ruff (MIT).
- `init` writes TOML from a text template (no TOML writer needed); comments in the template explain each field.
- Project root = current directory; must be inside a git work tree (`git rev-parse --is-inside-work-tree`). File lists for globs come from `git ls-files --cached --others --exclude-standard`, relative to the project root.
- One error type `MutaspecError(exit_code, message, where, hint)`; `cli.main` turns it into text on stderr or one JSON object on stdout (FR4, FR9, AC12).
- Config is parsed into frozen dataclasses; unknown keys, bad Level, missing `run`, bad duration, duplicate Suite name → exit 2 naming Suite and field.

## Files that change
- `pyproject.toml` — package, entry point `mutaspec = mutaspec.cli:main`, ruff and pytest settings.
- `src/mutaspec/__init__.py`, `__main__.py` — package, `python -m mutaspec`.
- `src/mutaspec/cli.py` — commands `init [--force] [--json]`, `config check [--json]`; output and exit codes.
- `src/mutaspec/errors.py` — `MutaspecError`, exit code constants.
- `src/mutaspec/gitrepo.py` — git work tree check (AC10), file listing.
- `src/mutaspec/config.py` — `Config`, `Project`, `Suite`, `load()`, validation, source/test overlap (AC7–AC9, AC11).
- `src/mutaspec/scaffold.py` — Maven / Spring Boot / actuator / mvnw / modules detection, `spec` globs, template text, `.mutaspec/.gitignore` (AC1–AC6).
- `tests/conftest.py` — `git_repo` fixture (tmp dir, `git init`, commit), `shop_repo` (copy of `examples/shop` in a tmp git repo), `run_cli(argv)` helper.
- `tests/test_init.py`, `tests/test_config.py`, `tests/test_cli.py` — `test_acN_...` and `test_edge_...`.
- `examples/shop/` — Spring Boot 3.5.16 app (Java 21, Maven, actuator): an orders/pricing service with a few rules worth mutating (discount, stock, totals, status codes); JUnit 5 unit tests; REST API tests `@Tag("api")` using `java.net.http.HttpClient` against `System.getProperty("baseUrl")`; `src/main/resources/openapi.yaml`; `docs/requirements.md`. Plus `examples/shop/mutaspec.toml` = the golden output of `init`.
- `.gitignore` — add `examples/shop/target/`.
- `AGENTS.md` — demo line: `uv run mutaspec init --force && uv run mutaspec config check` in `examples/shop` until `run` exists.
- `intent/README.md` — status `done` for 0001 at the end.

## Order of work (one commit each; test first, checks pass before each commit)
1. [x] Skeleton: `pyproject.toml`, package, `cli.py` with both commands stubbed, `errors.py`, `gitrepo.py`, JSON/text output. Tests: AC10, AC12 (error path). 
2. [x] Config load and validation. Tests: AC8, AC9, AC11, edge "unknown key", durations, duplicate names.
3. [x] Source/test overlap with `exclude` applied. Test: AC7 (FR6).
4. [x] `examples/shop` fixture. Check by hand: `mvn -q verify` (unit) and the api flow (package, start, ready, `mvn test -Dgroups=api -DbaseUrl=…`) pass. Not part of pytest (pytest needs no Java).
5. [x] `init` for Maven: template, `--force`, `.mutaspec/.gitignore`, nothing else touched, `mvnw`. Tests: AC1, AC4, AC5, AC6, edge mvnw.
6. [x] `init` Spring Boot web: `api` Suite; actuator vs plain HTTP `ready`. Tests: AC2, edge no-actuator.
7. [x] `spec` globs. Test: AC3 (FR7).
8. [x] Edge cases: multi-module (per-module globs, `api` commented), non-Maven commented template with message.
9. [x] Golden + agents: commit `examples/shop/mutaspec.toml`; `--json` on every success path. Tests: AC12 (success), SC1 (init in `shop_repo` equals golden file and `config check` exits 0), SC2 (< 2 s). Update AGENTS.md demo line. (`intent/README.md` → `done` after the verifier passes.)

## Departures (found by the verifier, 2026-11-12)
- FR7: `openapi.*`, `swagger.*` and files in an `openapi/` folder count only with `.yaml`, `.yml` or `.json`; build output (`target/`, `build/`, `node_modules/`, `.mutaspec/`) is skipped. Other suffixes (for example `openapi.html`) are not requirement documents.
- Left for 0002: FR3 free-port picking and placeholder checks. `--help` and `--version` print text even with `--json` (they are not commands).

## Risks
- **Maven passing `-DbaseUrl` to tests**: Surefire copies user properties into the test JVM. Checked in step 4: the 4 API tests ran, none skipped. Fallback: `<systemPropertyVariables>` in the shop `pom.xml`.
- **`target/*.jar` glob**: Spring Boot repackage leaves `x.jar` and `x.jar.original`; `*.jar` matches one. Checked in step 4: only `shop-0.1.0.jar`.
- **`**` glob semantics**: `PurePath.full_match` needs Python 3.13; pin `requires-python >= 3.13`.
- **Git not installed** → AC10 path, exit 3 with the same message plus "git not found".
- **Fixture build time** in CI: pytest never runs Maven; Maven checks stay manual until 0002.
- **Spring Boot version drift**: pin parent version in `pom.xml`.

## Proof
- `tests/test_init.py::test_ac1_…` … `test_ac6_…` — AC1–AC6
- `tests/test_config.py::test_ac7_…` … `test_ac9_…`, `test_ac11_…` — AC7–AC9, AC11
- `tests/test_cli.py::test_ac10_…`, `test_ac12_…`, `test_sc1_…`, `test_sc2_…`
- Edge tests: `test_edge_mvnw…`, `test_edge_no_actuator…`, `test_edge_multi_module…`, `test_edge_not_maven…`, `test_edge_unknown_key…`
- Demo: in `examples/shop`, `uv run mutaspec init --force && uv run mutaspec config check` exits 0, prints `unit (unit)` and `api (api)`, and `git status` shows no change (golden file unchanged).
- Checks: `uv run ruff check . && uv run ruff format --check . && uv run pytest`; then the `verifier` subagent.
