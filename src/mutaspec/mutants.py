"""Rule Mutants: small operator changes, found with text rules that work for most languages.

A rule changes one operator that has a space on each side (`a < b`, `x and y`) or one
boolean word (`true`, `False`). Text in strings and comments is never changed, and lines
that only import, annotate or log are skipped.
"""

import hashlib
import random
import re
from dataclasses import dataclass
from pathlib import Path

SWAPS = {
    "<": "<=",
    "<=": "<",
    ">": ">=",
    ">=": ">",
    "==": "!=",
    "!=": "==",
    "&&": "||",
    "||": "&&",
    "and": "or",
    "or": "and",
    "+": "-",
    "-": "+",
    "*": "/",
    "/": "*",
    "true": "false",
    "false": "true",
    "True": "False",
    "False": "True",
}
_OPERATOR = re.compile(r"(?<= )(<=|>=|==|!=|&&|\|\||and|or|<|>|\+|-|\*|/)(?= )")
_WORD = re.compile(r"\b(true|false|True|False)\b")
_SKIP_START = ("//", "#", "*", "/*", "import ", "from ", "package ", "@")
_LOGGING = re.compile(r"\b(log|logger|LOG|LOGGER|logging|print|console)\b|System\.(out|err)")


@dataclass(frozen=True)
class Mutant:
    id: str
    file: str  # relative to the project root
    line: int  # 1-based
    old: str
    new: str
    before: str  # the full line, with its line ending
    after: str

    @property
    def rule(self) -> str:
        return f"{self.old} -> {self.new}"

    def diff(self) -> str:
        return (
            f"--- a/{self.file}\n+++ b/{self.file}\n@@ -{self.line} +{self.line} @@\n"
            f"-{self.before.rstrip()}\n+{self.after.rstrip()}\n"
        )

    def to_json(self) -> dict:
        return {"id": self.id, "file": self.file, "line": self.line, "rule": self.rule}


def _code_end_and_strings(line: str) -> tuple[int, set[int]]:
    """Where a trailing comment starts, and the positions that are inside string literals."""
    inside: set[int] = set()
    quote = None
    i = 0
    while i < len(line):
        ch = line[i]
        if quote:
            inside.add(i)
            if ch == "\\":
                inside.add(i + 1)
                i += 1
            elif ch == quote:
                quote = None
        elif ch in "\"'`":
            quote = ch
            inside.add(i)
        elif line.startswith("//", i) or ch == "#":
            return i, inside
        i += 1
    return len(line), inside


def _candidates(line: str) -> list[tuple[int, str]]:
    text = line.strip()
    if not text or text.startswith(_SKIP_START) or _LOGGING.search(text):
        return []
    end, strings = _code_end_and_strings(line)
    found = [(m.start(), m.group()) for m in _OPERATOR.finditer(line)]
    found += [(m.start(), m.group()) for m in _WORD.finditer(line)]
    # '+' next to text joins strings ("a" + b); '-' does not compile there.
    joins_text = bool(strings)
    return sorted(
        (col, old)
        for col, old in found
        if col < end and col not in strings and not (old == "+" and joins_text)
    )


def _make(file: str, number: int, line: str, col: int, old: str) -> Mutant:
    new = SWAPS[old]
    key = f"{file}\n{number}\n{col}\n{old}\n{new}".encode()
    return Mutant(
        id=hashlib.sha1(key).hexdigest()[:8],
        file=file,
        line=number,
        old=old,
        new=new,
        before=line,
        after=line[:col] + new + line[col + len(old) :],
    )


def _read(path: Path) -> str | None:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            return handle.read()
    except (OSError, UnicodeDecodeError):
        return None  # missing in the Baseline, or not a text file


def find(folder: Path, files: list[str]) -> list[Mutant]:
    """Every Rule Mutant in `files` (relative to `folder`), in file and line order."""
    found = []
    for file in files:
        text = _read(folder / file)
        if text is not None:
            found += find_in_text(file, text)
    return found


def find_in_text(file: str, text: str) -> list[Mutant]:
    found = []
    for number, line in enumerate(text.splitlines(keepends=True), start=1):
        found += [_make(file, number, line, col, old) for col, old in _candidates(line)]
    return found


def sample(found: list[Mutant], limit: int, seed: int = 0) -> list[Mutant]:
    """At most `limit` Mutants, the same ones for the same code and seed."""
    if len(found) <= limit:
        return found
    chosen = random.Random(seed).sample(found, limit)
    return sorted(chosen, key=lambda m: (m.file, m.line, m.id))


def apply(mutant: Mutant, folder: Path) -> str:
    """Write the Mutant into `folder`; return the original text for `restore`."""
    path = folder / mutant.file
    original = _read(path)
    if original is None:
        raise ValueError(f"cannot read {mutant.file}")
    lines = original.splitlines(keepends=True)
    if lines[mutant.line - 1] != mutant.before:
        raise ValueError(f"{mutant.file}:{mutant.line} changed since the Mutant was made")
    lines[mutant.line - 1] = mutant.after
    _write(path, "".join(lines))
    return original


def restore(mutant: Mutant, folder: Path, original: str) -> None:
    _write(folder / mutant.file, original)


def _write(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)
