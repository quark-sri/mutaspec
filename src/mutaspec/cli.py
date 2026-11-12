"""Command line: `mutaspec init`, `mutaspec config check`. Every command takes --json (AC12)."""

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

from mutaspec import __version__, gitrepo
from mutaspec.config import CONFIG_FILE, load
from mutaspec.errors import OK, USAGE, MutaspecError

Output = dict  # what a command returns: "lines" for people, the rest for --json


class _Parser(argparse.ArgumentParser):
    def error(self, message: str):
        raise MutaspecError(USAGE, message, hint=f"Run '{self.prog} --help'.")


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="mutaspec", description="Plant bugs, run your tests, score them.")
    parser.add_argument("--version", action="version", version=f"mutaspec {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)

    init = sub.add_parser("init", help="write a draft mutaspec.toml for this project")
    init.add_argument("--force", action="store_true", help="overwrite an existing mutaspec.toml")
    init.add_argument("--json", action="store_true", help="print one JSON object on stdout")
    init.set_defaults(handler=_init)

    config = sub.add_parser("config", help="work with mutaspec.toml")
    config_sub = config.add_subparsers(dest="config_command", required=True, parser_class=_Parser)
    check = config_sub.add_parser("check", help="load and check mutaspec.toml")
    check.add_argument("--json", action="store_true", help="print one JSON object on stdout")
    check.set_defaults(handler=_config_check)
    return parser


def _init(root: Path, args: argparse.Namespace) -> Output:
    raise NotImplementedError


def _config_check(root: Path, args: argparse.Namespace) -> Output:
    config = load(root)
    suites = [{"name": s.name, "level": s.level} for s in config.suites]
    lines = [f"{CONFIG_FILE} is valid. Suites:"]
    lines += [f"  {s['name']} ({s['level']})" for s in suites]
    return {"lines": lines, "suites": suites}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    as_json = "--json" in argv
    try:
        args = _parser().parse_args(argv)
        root = Path.cwd()
        gitrepo.require_work_tree(root)
        handler: Callable[[Path, argparse.Namespace], Output] = args.handler
        output = handler(root, args)
    except MutaspecError as error:
        if as_json:
            payload = {"ok": False, "exit_code": error.exit_code, "error": error.to_json()}
            print(json.dumps(payload))
        else:
            print(f"mutaspec: {error}", file=sys.stderr)
        return error.exit_code

    if as_json:
        data = {k: v for k, v in output.items() if k != "lines"}
        print(json.dumps({"ok": True, "exit_code": OK, **data}))
    else:
        for line in output.get("lines", []):
            print(line)
    return OK
