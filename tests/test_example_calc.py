"""The Python example in examples/calc: the quickstart in the README must give this result."""

import shutil

from conftest import REPO_ROOT, commit_all

from mutaspec.errors import OK


def test_calc_example_scores_60_percent_with_two_boundary_survivors(git_repo, run_cli):
    shutil.copytree(
        REPO_ROOT / "examples" / "calc",
        git_repo,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(".mutaspec", "__pycache__"),
    )
    commit_all(git_repo)

    out = run_cli(git_repo, "run", "--json")

    data = out.json()
    assert out.code == OK
    assert data["score"] == 60.0
    survived = {(m["line"], m["rule"]) for m in data["mutants"] if m["status"] == "survived"}
    assert survived == {(10, "< -> <="), (17, ">= -> >")}
