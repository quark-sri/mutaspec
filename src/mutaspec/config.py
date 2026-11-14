"""mutaspec.toml: load it, check it, and explain mistakes plainly (spec 0001 FR2, FR9)."""

import re
import tomllib
from dataclasses import dataclass, fields
from pathlib import Path, PurePosixPath
from typing import Any

from mutaspec import gitrepo
from mutaspec.errors import USAGE, MutaspecError

CONFIG_FILE = "mutaspec.toml"
LEVELS = ("unit", "integration", "api", "ui", "other")

_DURATION = re.compile(r"^(\d+(?:\.\d+)?)(ms|s|m|h)$")
_UNIT_SECONDS = {"ms": 0.001, "s": 1, "m": 60, "h": 3600}


@dataclass(frozen=True)
class Project:
    source: tuple[str, ...]
    tests: tuple[str, ...]
    baseline: str = "HEAD"
    exclude: tuple[str, ...] = ()
    spec: tuple[str, ...] = ()
    build: str | None = None


@dataclass(frozen=True)
class Suite:
    name: str
    level: str
    run: str
    setup: str | None = None
    start: str | None = None
    ready: str | None = None
    ready_timeout: float = 60
    teardown: str | None = None
    timeout: float | None = None
    junit: str | None = None
    repeat: int = 1
    parallel: bool = False


@dataclass(frozen=True)
class Config:
    root: Path
    project: Project
    suites: tuple[Suite, ...]


def _error(where: str, message: str, hint: str | None = None) -> MutaspecError:
    return MutaspecError(USAGE, message, where=f"{CONFIG_FILE}, {where}", hint=hint)


def parse_duration(value: Any, where: str) -> float:
    """'120s', '5m', '1h', '500ms' -> seconds."""
    match = _DURATION.match(value) if isinstance(value, str) else None
    if not match:
        raise _error(where, f"{value!r} is not a duration.", 'Write it like "120s" or "5m".')
    number, unit = match.groups()
    seconds = float(number) * _UNIT_SECONDS[unit]
    if seconds <= 0:
        raise _error(where, "must be more than 0.", 'Write it like "120s" or "5m".')
    return seconds


def _check_keys(table: dict, allowed: set[str], where: str) -> None:
    unknown = sorted(set(table) - allowed)
    if unknown:
        raise _error(
            where,
            f"unknown key {', '.join(repr(k) for k in unknown)}.",
            f"Known keys: {', '.join(sorted(allowed))}.",
        )


_STR_HINT = 'Write it in quotes, for example run = "mvn -q test".'
_GLOBS_HINT = 'Write a list of globs, for example ["src/main/java/**"].'


def _str(table: dict, key: str, where: str, required: bool = False) -> str | None:
    value = table.get(key)
    if value is None:
        if required:
            raise _error(f"{where}, field '{key}'", "is missing.", _STR_HINT)
        return None
    if not isinstance(value, str) or not value.strip():
        raise _error(f"{where}, field '{key}'", "must be a non-empty string.", _STR_HINT)
    return value


def _globs(table: dict, key: str, where: str, required: bool = False) -> tuple[str, ...]:
    value = table.get(key)
    if value is None:
        if required:
            raise _error(f"{where}, field '{key}'", "is missing.", _GLOBS_HINT)
        return ()
    if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
        raise _error(f"{where}, field '{key}'", "must be a list of glob strings.", _GLOBS_HINT)
    return tuple(value)


def _project(table: Any) -> Project:
    where = "[project]"
    if not isinstance(table, dict):
        raise _error(where, "is missing.", "Run 'mutaspec init --force' to write a draft.")
    _check_keys(table, {f.name for f in fields(Project)}, where)
    return Project(
        source=_globs(table, "source", where, required=True),
        tests=_globs(table, "tests", where, required=True),
        baseline=_str(table, "baseline", where) or "HEAD",
        exclude=_globs(table, "exclude", where),
        spec=_globs(table, "spec", where),
        build=_str(table, "build", where),
    )


def _suite(table: Any, index: int) -> Suite:
    if not isinstance(table, dict):
        raise _error(f"[[suites]] #{index + 1}", "must be a table.", "Start it with [[suites]].")
    name = table.get("name")
    where = f"Suite '{name}'" if isinstance(name, str) and name else f"[[suites]] #{index + 1}"
    _check_keys(table, {f.name for f in fields(Suite)}, where)
    name = _str(table, "name", where, required=True)

    level = _str(table, "level", where, required=True)
    if level not in LEVELS:
        raise _error(
            f"{where}, field 'level'",
            f"unknown Level {level!r}.",
            f"Use one of: {', '.join(LEVELS)}.",
        )

    repeat = table.get("repeat", 1)
    if not isinstance(repeat, int) or isinstance(repeat, bool) or repeat < 1:
        raise _error(
            f"{where}, field 'repeat'",
            "must be a whole number of 1 or more.",
            "Example: repeat = 2.",
        )
    parallel = table.get("parallel", False)
    if not isinstance(parallel, bool):
        raise _error(
            f"{where}, field 'parallel'", "must be true or false.", "Write it without quotes."
        )

    def duration(key: str) -> float | None:
        if key not in table:
            return None
        return parse_duration(table[key], f"{where}, field '{key}'")

    return Suite(
        name=name,
        level=level,
        run=_str(table, "run", where, required=True),
        setup=_str(table, "setup", where),
        start=_str(table, "start", where),
        ready=_str(table, "ready", where),
        ready_timeout=60 if (ready := duration("ready_timeout")) is None else ready,
        teardown=_str(table, "teardown", where),
        timeout=duration("timeout"),
        junit=_str(table, "junit", where),
        repeat=repeat,
        parallel=parallel,
    )


def load(root: Path) -> Config:
    """Read and check `root/mutaspec.toml` (spec AC8, AC11)."""
    path = root / CONFIG_FILE
    if not path.is_file():
        raise MutaspecError(
            USAGE,
            f"no {CONFIG_FILE} in this folder.",
            where=str(root),
            hint="Run 'mutaspec init' to write a draft.",
        )
    try:
        data = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as error:
        raise MutaspecError(
            USAGE,
            f"is not valid TOML: {error}.",
            where=CONFIG_FILE,
            hint="Fix the syntax at that line, or run 'mutaspec init --force' for a fresh draft.",
        ) from None

    _check_keys(data, {"project", "suites"}, "top level")
    project = _project(data.get("project"))

    raw_suites = data.get("suites")
    if not isinstance(raw_suites, list) or not raw_suites:
        raise _error("[[suites]]", "no Suites defined.", "Add at least one [[suites]] table.")
    suites = tuple(_suite(table, i) for i, table in enumerate(raw_suites))

    seen: set[str] = set()
    for suite in suites:
        if suite.name in seen:
            raise _error(
                f"Suite '{suite.name}'", "the name is used twice.", "Give each Suite its own name."
            )
        seen.add(suite.name)

    config = Config(root=root, project=project, suites=suites)
    _check_overlap(config)
    return config


def _matches(path: str, globs: tuple[str, ...]) -> bool:
    pure = PurePosixPath(path)
    return any(pure.full_match(glob) for glob in globs)


def test_files(config: Config, files: list[str] | None = None) -> list[str]:
    """Files matched by `tests`. A Mutant never changes these."""
    files = gitrepo.list_files(config.root) if files is None else files
    return [f for f in files if _matches(f, config.project.tests)]


def source_files(config: Config, files: list[str] | None = None) -> list[str]:
    """Files matched by `source`, minus `exclude` and minus every test file (spec FR6)."""
    files = gitrepo.list_files(config.root) if files is None else files
    tests = set(test_files(config, files))
    return [
        f
        for f in files
        if _matches(f, config.project.source)
        and not _matches(f, config.project.exclude)
        and f not in tests
    ]


def _check_overlap(config: Config, shown: int = 5) -> None:
    """No file may be both source and test (spec AC7)."""
    files = gitrepo.list_files(config.root)
    project = config.project
    both = [
        f
        for f in files
        if _matches(f, project.source)
        and not _matches(f, project.exclude)
        and _matches(f, project.tests)
    ]
    if both:
        more = f" and {len(both) - shown} more" if len(both) > shown else ""
        raise _error(
            "[project]",
            f"'source' and 'tests' both match: {', '.join(both[:shown])}{more}.",
            "Narrow 'source', or add these files to 'exclude'. Test files are never mutated.",
        )
