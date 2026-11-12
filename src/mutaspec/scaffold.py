"""`mutaspec init`: look at the project and write a working draft of mutaspec.toml (spec S1)."""

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from mutaspec import gitrepo
from mutaspec.config import CONFIG_FILE
from mutaspec.errors import USAGE, MutaspecError

STATE_DIR = ".mutaspec"

# Temporary files are ignored; the Mutant Set (mutants/) and history stay committable (AC6).
STATE_GITIGNORE = """\
# Written by mutaspec init. Temporary files only.
# The Mutant Set (mutants/) and history.jsonl are meant to be committed.
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
    spec: tuple[str, ...] = ()  # requirement documents


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


_BUILD_OUTPUT = {"target", "build", "node_modules", ".mutaspec"}
_CONTRACT_SUFFIXES = {".yaml", ".yml", ".json"}


def spec_globs(files: list[str]) -> list[str]:
    """Requirement documents in common places: docs/ and OpenAPI/Swagger files (spec FR7)."""
    docs = [f for f in files if f.startswith("docs/")]
    found = []
    if any(f.endswith(".md") for f in docs):
        found.append("docs/**/*.md")
    elif docs:
        found.append("docs/**")
    contracts = []
    for f in files:
        path = PurePosixPath(f)
        if _BUILD_OUTPUT & set(path.parts) or path.suffix not in _CONTRACT_SUFFIXES:
            continue
        named = path.stem in ("openapi", "swagger")
        in_folder = path.parent.name == "openapi"
        if named or in_folder:
            contracts.append(f)
    return found + sorted(contracts)


def detect(root: Path) -> Project:
    pom = _pom(root)
    spec = tuple(spec_globs(gitrepo.list_files(root)))
    if pom is None:
        return Project(kind="unknown", spec=spec)
    artifacts = _artifacts(pom)
    return Project(
        kind="maven",
        spec=spec,
        mvn="./mvnw" if (root / "mvnw").is_file() else "mvn",
        web="spring-boot-starter-web" in artifacts,
        actuator="spring-boot-starter-actuator" in artifacts,
    )


def _api_suite(project: Project) -> list[str]:
    mvn = project.mvn
    if project.actuator:
        ready = "curl -sf http://localhost:{port}/actuator/health"
    else:
        ready = "curl -s -o /dev/null http://localhost:{port}/"  # any HTTP answer
    return [
        "",
        '# REST API tests (JUnit @Tag("api")) against the running app.',
        "# mutaspec stops the 'start' process after 'run'.",
        "[[suites]]",
        'name = "api"',
        'level = "api"',
        f"setup = {_toml(f'{mvn} -q -DskipTests package')}",
        f"start = {_toml('java -jar target/*.jar --server.port={port}')}",
        f"ready = {_toml(ready)}",
        'ready_timeout = "60s"',
        f"run = {_toml(f'{mvn} -q test -Dgroups=api -DbaseUrl=http://localhost:{{port}}')}",
        'timeout = "300s"',
    ]


def _spec_line(project: Project) -> str:
    if project.spec:
        return f"spec = {_toml(list(project.spec))}  # requirement documents"
    return '# spec = ["docs/**/*.md"]  # requirement documents (none found)'


def render(project: Project) -> str:
    mvn = project.mvn
    lines = [
        "# Written by 'mutaspec init'. Check it, then run 'mutaspec config check'.",
        "",
        "[project]",
        'baseline = "HEAD"  # git ref of the clean code',
        f"source = {_toml(['src/main/java/**'])}  # files Mutants may change",
        f"tests = {_toml(['src/test/java/**'])}  # files Mutants never change",
        _spec_line(project),
        f"build = {_toml(f'{mvn} -q -DskipTests test-compile')}  # fails -> Mutant is Invalid",
        "",
        "[[suites]]",
        'name = "unit"',
        'level = "unit"',
        f"run = {_toml(f'{mvn} -q test -DexcludedGroups=api')}",
        'timeout = "300s"',
    ]
    if project.web:
        lines += _api_suite(project)
    return "\n".join(lines) + "\n"


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

    written = [CONFIG_FILE, f"{STATE_DIR}/.gitignore"]
    return {
        "lines": [
            f"Wrote {CONFIG_FILE} for a Maven project"
            + (" with a Spring Boot web app (unit and api Suites)." if project.web else "."),
            "Check it, then run 'mutaspec config check'.",
        ],
        "project_type": project.kind,
        "written": written,
    }
