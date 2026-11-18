"""Command line: `init`, `config check`, `baseline`, `run`. Every command takes --json."""

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

from mutaspec import __version__, baseline, gitrepo, runner, scaffold
from mutaspec.config import CONFIG_FILE, load
from mutaspec.errors import OK, USAGE, MutaspecError

Output = dict  # what a command returns: "lines" for people, the rest for --json
# Optional keys: "exit_code" (default 0), "warnings" (stderr for people, a list in --json).

INTERRUPTED = 130  # Ctrl-C, shell convention (D24)


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

    base = sub.add_parser(
        "baseline", help="run every Suite on the clean code and check it is ready"
    )
    base.add_argument(
        "--include-uncommitted",
        action="store_true",
        help="also use uncommitted changes and new files (baseline must be HEAD)",
    )
    base.add_argument("--json", action="store_true", help="print one JSON object on stdout")
    base.set_defaults(handler=_baseline)

    run = sub.add_parser("run", help="check the Baseline, then run and score the Mutants")
    run.add_argument(
        "--max",
        type=int,
        default=runner.DEFAULT_MAX,
        metavar="N",
        help=f"run at most N Mutants, picked the same way each time (default {runner.DEFAULT_MAX})",
    )
    run.add_argument(
        "--include-uncommitted",
        action="store_true",
        help="also use uncommitted changes and new files (baseline must be HEAD)",
    )
    run.add_argument(
        "--per-level",
        action="store_true",
        help="run every Suite on every Mutant and give a score per Level (slower)",
    )
    run.add_argument("--json", action="store_true", help="print one JSON object on stdout")
    run.set_defaults(handler=_run)
    return parser


def _init(root: Path, args: argparse.Namespace) -> Output:
    return scaffold.init(root, force=args.force)


def _config_check(root: Path, args: argparse.Namespace) -> Output:
    config = load(root)
    suites = [{"name": s.name, "level": s.level} for s in config.suites]
    lines = [f"{CONFIG_FILE} is valid. Suites:"]
    lines += [f"  {s['name']} ({s['level']})" for s in suites]
    return {"lines": lines, "suites": suites}


def _baseline(root: Path, args: argparse.Namespace) -> Output:
    return baseline.run(load(root), include_uncommitted=args.include_uncommitted)


def _run(root: Path, args: argparse.Namespace) -> Output:
    if args.max < 1:
        raise MutaspecError(USAGE, "--max must be 1 or more.", hint="Example: --max 20.")
    say = (lambda _: None) if args.json else (lambda line: print(line, flush=True))
    return runner.run(
        load(root),
        args.include_uncommitted,
        max_mutants=args.max,
        say=say,
        per_level=args.per_level,
    )


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
    except KeyboardInterrupt:
        message = "interrupted; started processes were stopped and teardown ran."
        if as_json:
            print(
                json.dumps({"ok": False, "exit_code": INTERRUPTED, "error": {"message": message}})
            )
        else:
            print(f"mutaspec: {message}", file=sys.stderr)
        return INTERRUPTED

    exit_code = output.get("exit_code", OK)
    if as_json:
        data = {k: v for k, v in output.items() if k not in ("lines", "exit_code")}
        print(json.dumps({"ok": exit_code == OK, "exit_code": exit_code, **data}))
    else:
        for warning in output.get("warnings", []):
            print(f"mutaspec: {warning}", file=sys.stderr)
        for line in output.get("lines", []):
            print(line)
    return exit_code
