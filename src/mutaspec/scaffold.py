"""`mutaspec init`: look at the project and write a working draft of mutaspec.toml (spec S1)."""

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from mutaspec.config import CONFIG_FILE
from mutaspec.errors import USAGE, MutaspecError

STATE_DIR = ".mutaspec"

STATE_GITIGNORE = """\
# Written by mutaspec init. Temporary files only.
worktrees/
runs/
"""


@dataclass(frozen=True)
class Project:
    """What `init` found in the project root."""

    kind: str  # "maven" or "unknown"
    mvn: str = "mvn"
    web: bool = False  # Spring Boot web app: gets an api Suite
    actuator: bool = False  # has /actuator/health
    modules: tuple[str, ...] = ()  # Maven modules of a parent pom


def _toml(value) -> str:
    """A TOML value for a string or a list of strings (JSON strings are valid TOML strings)."""
    if isinstance(value, list):
        return "[" + ", ".join(json.dumps(v) for v in value) + "]"
    return json.dumps(value)


def _pom(root: Path) -> ET.Element | None:
    path = root / "pom.xml"
    if not path.is_file():
        return None
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as error:
        raise MutaspecError(
            USAGE, f"cannot read pom.xml: {error}.", where=str(path), hint="Fix the XML first."
        ) from None


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]  # drop the XML namespace


def _artifacts(pom: ET.Element) -> set[str]:
    """artifactIds of every dependency in the pom."""
    found = set()
    for element in pom.iter():
        if _local(element.tag) == "dependency":
            for child in element:
                if _local(child.tag) == "artifactId" and child.text:
                    found.add(child.text.strip())
    return found


def _modules(pom: ET.Element) -> list[str]:
    """Module folders listed in a parent pom's <modules>."""
    return [
        child.text.strip()
        for element in pom
        if _local(element.tag) == "modules"
        for child in element
        if _local(child.tag) == "module" and child.text and child.text.strip()
    ]


def detect(root: Path) -> Project:
    pom = _pom(root)
    if pom is None:
        return Project(kind="unknown")
    modules = tuple(_modules(pom))
    artifacts = _artifacts(pom)
    for module in modules:
        module_pom = _pom(root / module)
        if module_pom is not None:
            artifacts |= _artifacts(module_pom)
    return Project(
        kind="maven",
        mvn="./mvnw" if (root / "mvnw").is_file() else "mvn",
        web="spring-boot-starter-web" in artifacts,
        actuator="spring-boot-starter-actuator" in artifacts,
        modules=modules,
    )


# Per-test results from Maven Surefire, in every module (spec 0002 FR11, D28).
JUNIT_LINE = 'junit = "**/target/surefire-reports/TEST-*.xml"  # per-test results'


def _api_suite(project: Project) -> list[str]:
    mvn = project.mvn
    if project.actuator:
        ready = "curl -sf http://localhost:{port}/actuator/health"
    else:
        ready = "curl -s -o /dev/null http://localhost:{port}/"  # any HTTP answer
    return [
        "[[suites]]",
        'name = "api"',
        'level = "api"',
        f"setup = {_toml(f'{mvn} -q -DskipTests package')}",
        f"start = {_toml('java -jar target/*.jar --server.port={port}')}",
        f"ready = {_toml(ready)}",
        'ready_timeout = "60s"',
        f"run = {_toml(f'{mvn} -q test -Dgroups=api -DbaseUrl=http://localhost:{{port}}')}",
        'timeout = "300s"',
        JUNIT_LINE,
    ]


def _commented(lines: list[str]) -> list[str]:
    return [f"# {line}" if line else "#" for line in lines]


HEADER = "# Written by 'mutaspec init'. Check it, then run 'mutaspec run'."


def _render_maven(project: Project) -> str:
    mvn = project.mvn
    prefixes = [f"{m}/" for m in project.modules] or [""]
    source = [f"{p}src/main/java/**" for p in prefixes]
    tests = [f"{p}src/test/java/**" for p in prefixes]
    lines = [
        HEADER,
        "",
        "[project]",
        'baseline = "HEAD"  # git ref of the clean code',
        f"source = {_toml(source)}  # files Mutants may change",
        f"tests = {_toml(tests)}  # files Mutants never change",
        f"build = {_toml(f'{mvn} -q -DskipTests test-compile')}  # fails -> Mutant is Invalid",
        "",
        "[[suites]]",
        'name = "unit"',
        'level = "unit"',
        f"run = {_toml(f'{mvn} -q test -DexcludedGroups=api')}",
        'timeout = "300s"',
        JUNIT_LINE,
    ]
    if project.web and project.modules:
        lines += [
            "",
            "# Review before use: a multi-module project. Point 'setup' and 'start' at the",
            "# module that holds the Spring Boot app, then remove the '# ' in front of each line.",
            *_commented(_api_suite(project)),
        ]
    elif project.web:
        lines += [
            "",
            '# REST API tests (JUnit @Tag("api")) against the running app.',
            "# mutaspec stops the 'start' process after 'run'.",
            *_api_suite(project),
        ]
    return "\n".join(lines) + "\n"


def _render_unknown(project: Project) -> str:
    body = [
        "[project]",
        'baseline = "HEAD"  # git ref of the clean code',
        'source = ["src/**"]  # files Mutants may change',
        'tests = ["tests/**"]  # files Mutants never change',
        'build = "make build"  # fails -> Mutant is Invalid',
        "",
        "[[suites]]",
        'name = "unit"',
        'level = "unit"  # unit, integration, api, ui or other',
        'run = "make test"',
        'timeout = "300s"',
    ]
    lines = [
        HEADER,
        "# The project type was not detected (mutaspec 0.1 detects Maven).",
        "# Fill in the values, then remove the '# ' in front of each line.",
        "",
        *_commented(body),
    ]
    return "\n".join(lines) + "\n"


def render(project: Project) -> str:
    return _render_maven(project) if project.kind == "maven" else _render_unknown(project)


def _message(project: Project) -> str:
    if project.kind != "maven":
        return (
            f"Project type not detected yet; wrote a commented {CONFIG_FILE} template. "
            "Fill it in, then run 'mutaspec run'."
        )
    if project.web and project.modules:
        kind = "a multi-module Maven project; review the commented api Suite"
    elif project.web:
        kind = "a Maven project with a Spring Boot web app (unit and api Suites)"
    else:
        kind = "a Maven project"
    return f"Wrote {CONFIG_FILE} for {kind}. Check it, then run 'mutaspec run'."


def init(root: Path, force: bool) -> dict:
    config_path = root / CONFIG_FILE
    if config_path.exists() and not force:
        raise MutaspecError(
            USAGE,
            f"{CONFIG_FILE} already exists; not overwritten.",
            where=str(config_path),
            hint="Pass --force to replace it.",
        )

    project = detect(root)
    config_path.write_text(render(project))
    state = root / STATE_DIR
    state.mkdir(exist_ok=True)
    (state / ".gitignore").write_text(STATE_GITIGNORE)

    message = _message(project)
    return {
        "lines": [message],
        "message": message,
        "project_type": project.kind,
        "written": [CONFIG_FILE, f"{STATE_DIR}/.gitignore"],
    }
