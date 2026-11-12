"""`mutaspec init`: look at the project and write a working draft of mutaspec.toml (spec S1)."""

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

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


def detect(root: Path) -> Project:
    if _pom(root) is None:
        return Project(kind="unknown")
    mvn = "./mvnw" if (root / "mvnw").is_file() else "mvn"
    return Project(kind="maven", mvn=mvn)


def render(project: Project) -> str:
    mvn = project.mvn
    lines = [
        "# Written by 'mutaspec init'. Check it, then run 'mutaspec config check'.",
        "",
        "[project]",
        'baseline = "HEAD"  # git ref of the clean code',
        f"source = {_toml(['src/main/java/**'])}  # files Mutants may change",
        f"tests = {_toml(['src/test/java/**'])}  # files Mutants never change",
        f"build = {_toml(f'{mvn} -q -DskipTests test-compile')}  # fails -> Mutant is Invalid",
        "",
        "[[suites]]",
        'name = "unit"',
        'level = "unit"',
        f"run = {_toml(f'{mvn} -q test -DexcludedGroups=api')}",
        'timeout = "300s"',
    ]
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
            f"Wrote {CONFIG_FILE} for a Maven project.",
            "Check it, then run 'mutaspec config check'.",
        ],
        "project_type": project.kind,
        "written": written,
    }
