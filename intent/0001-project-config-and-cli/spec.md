# Spec: project config and CLI (from intent.md, 2026-11-11)

Status: approved. Intent: [intent.md](intent.md)

## User scenarios and acceptance

### S1 Set up a project (P1)
- **AC1** Given a git repo with `pom.xml` and tests under `src/test/java`, When I run `mutaspec init`, Then `mutaspec.toml` is written with `source = ["src/main/java/**"]`, `tests = ["src/test/java/**"]`, a `build` command, and one `unit` Suite that runs `mvn test` without tests tagged `api`.
- **AC2** Given the AC1 repo whose `pom.xml` depends on `spring-boot-starter-web`, When I run `mutaspec init`, Then `mutaspec.toml` also has an `api` Suite that builds the app, starts it on `{port}`, waits until it answers, runs only the tests tagged `api` against it, and stops it.
- **AC3** Given the AC1 repo with `openapi.yaml` and a `docs/` folder, When I run `mutaspec init`, Then `spec` lists both.
- **AC4** Given `mutaspec.toml` exists, When I run `mutaspec init`, Then it is not overwritten and the command exits 2, unless I pass `--force`.
- **AC5** Given a git repo, When I run `mutaspec init`, Then the only new files are `mutaspec.toml` and `.mutaspec/.gitignore`, and no tracked file changes.
- **AC6** Given `.mutaspec/.gitignore` written by `init`, Then git ignores `.mutaspec/worktrees/` and `.mutaspec/runs/`, and does not ignore `.mutaspec/mutants/`.

### S2 Find config mistakes early (P1)
- **AC7** Given `source` and `tests` patterns that match the same file, When any command loads the config, Then it stops with an error naming the file(s), exit code 2.
- **AC8** Given a Suite with an unknown `level` or no `run`, When I run `mutaspec config check`, Then the error names the Suite and the field, exit code 2.
- **AC9** Given a valid `mutaspec.toml`, When I run `mutaspec config check`, Then it prints each Suite with its Level and exits 0.
- **AC10** Given a directory that is not a git repo, When I run any command, Then it stops with "mutaspec needs a git repository", exit code 3.
- **AC11** Given no `mutaspec.toml`, When I run any command except `init`, Then it says to run `mutaspec init`, exit code 2.

### S3 Agents read results (P2)
- **AC12** Every command accepts `--json` and then prints exactly one JSON object on stdout, for success and for errors.

## Edge cases
- Maven wrapper: if `mvnw` exists, `init` writes `./mvnw` instead of `mvn`.
- No `spring-boot-starter-actuator`: the `api` Suite's `ready` checks for any HTTP answer instead of `/actuator/health`.
- Multi-module Maven project: `init` writes `source` and `tests` for each module and one `unit` Suite at the root; the `api` Suite is written commented, for review.
- Not a Maven project (Gradle, Python, JS, Go, Rust, other): `init` writes a commented template and says the project type is not detected yet.
- A source file that also holds tests (Rust inline `#[cfg(test)]` modules): the file counts as source; its test block is never mutated. Enforced when Rust Operators land (0003).
- `mutaspec.toml` with keys mutaspec does not know: error naming the key, exit code 2 (catches typos).

## Functional requirements
- **FR1** `init` detects Maven (`pom.xml`) and Spring Boot web (`spring-boot-starter-web` in `pom.xml`). Other build tools come with their language (PLAN.md roadmap).
- **FR2** Config fields: `[project] baseline, source, exclude, tests, spec, build`; `[[suites]] name, level, run, setup, start, ready, ready_timeout, teardown, timeout, junit, repeat, parallel`. Durations are strings like `"120s"`, `"5m"`.
- **FR3** Placeholders `{port}` and `{worktree}` are allowed in Suite commands. mutaspec picks a free port per Suite.
- **FR4** Exit codes: 0 ok, 1 quality result below threshold, 2 usage or config error, 3 environment or setup error.
- **FR5** Config lives only in `mutaspec.toml` in the project root: the directory where mutaspec runs, which must be inside a git repository. `.mutaspec/` sits next to it. Never in `pom.xml`, `pyproject.toml`, `package.json` or similar.
- **FR6** Source/test split is per file: a file matched by `tests` is never a source file. Overlap is an error (AC7).
- **FR7** `init` proposes `spec` globs from common places: OpenAPI/Swagger files (`openapi.*`, `swagger.*`, `**/openapi/*`) and `docs/` (0003 FR6).
- **FR8** `init` writes `.mutaspec/.gitignore`; it never edits the user's own `.gitignore`.
- **FR9** Errors say what is wrong, where (file, Suite, field), and what to do next, in one or two plain sentences.

Example (what `init` writes for `examples/shop`):
```toml
[project]
baseline = "HEAD"
source = ["src/main/java/**"]
tests = ["src/test/java/**"]
spec = ["docs/**/*.md", "src/main/resources/openapi.yaml"]
build = "mvn -q -DskipTests test-compile"

[[suites]]
name = "unit"
level = "unit"
run = "mvn -q test -DexcludedGroups=api"
timeout = "300s"

[[suites]]
name = "api"
level = "api"
setup = "mvn -q -DskipTests package"
start = "java -jar target/*.jar --server.port={port}"
ready = "curl -sf http://localhost:{port}/actuator/health"
ready_timeout = "60s"
run = "mvn -q test -Dgroups=api -DbaseUrl=http://localhost:{port}"
timeout = "300s"
```

## Key entities
Suite, Level, Baseline (see GLOSSARY.md). No new terms.

## Success criteria
- **SC1** On `examples/shop` (Maven, Spring Boot, JUnit 5 unit tests and REST API tests tagged `api`), `mutaspec init && mutaspec config check` succeeds with no edits, and the written config matches the example above.
- **SC2** `init` and `config check` each finish in under 2 seconds on `examples/shop` (no build or test runs).

## Out of scope
Running any Suite or build (0002+); non-git projects; detecting build tools other than Maven; Gradle.

## Needs clarification
- None.
