"""Rule Mutants: small operator changes, found with text rules that work for most languages.

A rule changes one operator that has a space on each side (`a < b`, `x and y`) or one
boolean word (`true`, `False`). Text in strings and comments is never changed, and lines
that only import, annotate or log are skipped.
"""

import hashlib
import os
import random
import re
import time
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
_SKIP_START = ("//", "#", "*", "import ", "from ", "package ", "@")
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


def _scan(lines: list[str]) -> list[tuple[list[bool], bool]]:
    """For each line: which positions are code (not string or comment), and whether the
    line holds string text. Block comments and multi-line strings carry over lines."""
    out = []
    mode: str | None = None  # None, "block", or the quote that ends the string
    for line in lines:
        code = [False] * len(line)
        has_text = mode not in (None, "block")
        i = 0
        while i < len(line):
            if mode == "block":
                end = line.find("*/", i)
                if end < 0:
                    break
                i, mode = end + 2, None
            elif mode is not None:
                has_text = True
                if line[i] == "\\":
                    i += 2
                elif line.startswith(mode, i):
                    i, mode = i + len(mode), None
                else:
                    i += 1
            elif line.startswith("//", i) or line[i] == "#":
                break
            elif line.startswith("/*", i):
                i, mode = i + 2, "block"
            elif line.startswith(('"""', "'''"), i):
                i, mode, has_text = i + 3, line[i : i + 3], True
            elif line[i] in "\"'`":
                i, mode, has_text = i + 1, line[i], True
            else:
                code[i] = True
                i += 1
        if mode in ('"', "'"):
            mode = None  # these strings end with the line
        out.append((code, has_text))
    return out


def _arid(line: str) -> bool:
    text = line.strip()
    return not text or text.startswith(_SKIP_START) or bool(_LOGGING.search(text))


def _depth(line: str, code: list[bool]) -> int:
    """How many brackets the code on this line leaves open."""
    return sum(
        (ch in "([") - (ch in ")]") for ch, is_code in zip(line, code, strict=True) if is_code
    )


def _candidates(line: str, code: list[bool], has_text: bool) -> list[tuple[int, str]]:
    found = [(m.start(), m.group()) for m in _OPERATOR.finditer(line)]
    found += [(m.start(), m.group()) for m in _WORD.finditer(line)]
    return sorted(
        (col, old)
        for col, old in found
        if all(code[col : col + len(old)])
        # '+' next to text joins strings ("a" + b); '-' does not compile there.
        and not (old == "+" and has_text)
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
    lines = text.splitlines(keepends=True)
    found = []
    open_arid = 0  # brackets still open in an import, annotation or logging statement
    for number, (line, (code, has_text)) in enumerate(zip(lines, _scan(lines), strict=True), 1):
        if open_arid > 0 or _arid(line):
            open_arid = max(0, open_arid + _depth(line, code))
            continue
        found += [
            _make(file, number, line, col, old) for col, old in _candidates(line, code, has_text)
        ]
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
    """Write `text`; the file's mtime always moves forward, so build tools see the change."""
    before = path.stat().st_mtime_ns
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    stamp = max(time.time_ns(), before + 1)
    os.utime(path, ns=(stamp, stamp))
