"""One error type for everything mutaspec reports to people and agents (spec FR4, FR9)."""

from dataclasses import dataclass

OK = 0
BELOW_THRESHOLD = 1
USAGE = 2
ENVIRONMENT = 3


@dataclass
class MutaspecError(Exception):
    """A problem the user can fix.

    `where` names the file, Suite or field; `hint` says what to do next.
    """

    exit_code: int
    message: str
    where: str | None = None
    hint: str | None = None

    def __str__(self) -> str:
        text = self.message
        if self.where:
            text = f"{self.where}: {text}"
        if self.hint:
            text = f"{text} {self.hint}"
        return text

    def to_json(self) -> dict:
        return {"message": self.message, "where": self.where, "hint": self.hint}
