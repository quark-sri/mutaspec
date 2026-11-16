"""The Baseline worktree (spec 0002 FR2, AC15-AC18)."""

import pytest
from conftest import commit_all, git, write

from mutaspec import worktree
from mutaspec.config import load
from mutaspec.errors import USAGE, MutaspecError

CONFIG = """\
[project]
baseline = "{ref}"
source = ["src/**"]
tests = ["tests/**"]

[[suites]]
name = "unit"
level = "unit"
run = "true"
"""


def project(repo, ref="HEAD", sub=""):
    root = repo / sub if sub else repo
    write(root, "mutaspec.toml", CONFIG.format(ref=ref))
    write(root, "src/app.txt", "v1\n")
    write(root, "tests/app_test.txt", "t\n")
    commit_all(repo)
    return root


def user_state(repo):
    return (
        git(repo, "rev-parse", "HEAD"),
        git(repo, "branch", "--show-current"),
        git(repo, "status", "--porcelain"),
    )


def test_ac15_base_worktree_leaves_user_tree_unchanged(git_repo):
    root = project(git_repo)
    write(root, "src/app.txt", "edited\n")
    before = user_state(git_repo)

    base = worktree.create_base(load(root), include_uncommitted=False)

    assert user_state(git_repo) == before
    assert base.path == root / ".mutaspec" / "worktrees" / "base"
    assert (base.project_dir / "src" / "app.txt").read_text() == "v1\n"
    assert base.commit == git(git_repo, "rev-parse", "HEAD").strip()
    assert git(base.path, "status", "--porcelain") == ""


def test_fr2_project_in_a_subfolder_runs_in_the_same_subfolder(git_repo):
    root = project(git_repo, sub="apps/shop")

    base = worktree.create_base(load(root), include_uncommitted=False)

    assert base.project_dir == base.path / "apps" / "shop"
    assert (base.project_dir / "src" / "app.txt").read_text() == "v1\n"


def test_ac16_uncommitted_files_are_left_out_and_listed(git_repo):
    root = project(git_repo)
    write(root, "src/app.txt", "edited\n")
    write(root, "src/new.txt", "new\n")

    base = worktree.create_base(load(root), include_uncommitted=False)

    assert base.left_out == ["src/app.txt", "src/new.txt"]
    assert not (base.project_dir / "src" / "new.txt").exists()
    assert base.uncommitted is False


def test_ac16_warning_lists_first_10_then_and_n_more():
    files = [f"f{i:02}.txt" for i in range(13)]

    text = worktree.left_out_warning(files)

    assert "f09.txt" in text
    assert "f10.txt" not in text
    assert "and 3 more" in text


def test_ac17_include_uncommitted_copies_edits_and_untracked_files(git_repo):
    root = project(git_repo)
    write(root, "src/app.txt", "edited\n")
    write(root, "src/new.txt", "new\n")
    write(root, ".gitignore", "*.log\n")
    write(root, "src/debug.log", "ignored\n")
    (root / "tests" / "app_test.txt").unlink()

    base = worktree.create_base(load(root), include_uncommitted=True)

    assert (base.project_dir / "src" / "app.txt").read_text() == "edited\n"
    assert (base.project_dir / "src" / "new.txt").read_text() == "new\n"
    assert not (base.project_dir / "src" / "debug.log").exists()
    assert not (base.project_dir / "tests" / "app_test.txt").exists()
    assert base.uncommitted is True
    assert base.left_out == []


def test_ac18_include_uncommitted_with_other_ref_is_a_usage_error(git_repo):
    project(git_repo)
    git(git_repo, "branch", "old")
    write(git_repo, "src/app.txt", "v2\n")
    commit_all(git_repo)
    write(git_repo, "mutaspec.toml", CONFIG.format(ref="old"))
    commit_all(git_repo)

    with pytest.raises(MutaspecError) as info:
        worktree.create_base(load(git_repo), include_uncommitted=True)

    assert info.value.exit_code == USAGE
    assert "--include-uncommitted" in info.value.message


def test_edge_bad_ref_is_named_with_exit_2(git_repo):
    root = project(git_repo, ref="no-such-branch")

    with pytest.raises(MutaspecError) as info:
        worktree.create_base(load(root), include_uncommitted=False)

    assert info.value.exit_code == USAGE
    assert "no-such-branch" in str(info.value)


def test_edge_other_ref_is_checked_out(git_repo):
    project(git_repo)
    git(git_repo, "branch", "old")
    write(git_repo, "src/app.txt", "v2\n")
    write(git_repo, "mutaspec.toml", CONFIG.format(ref="old"))
    commit_all(git_repo)

    base = worktree.create_base(load(git_repo), include_uncommitted=False)

    assert (base.project_dir / "src" / "app.txt").read_text() == "v1\n"


def test_edge_existing_worktree_is_created_again(git_repo):
    root = project(git_repo)
    first = worktree.create_base(load(root), include_uncommitted=False)
    write(first.project_dir, "src/app.txt", "changed by a run\n")
    write(first.project_dir, "leftover.txt", "x")

    second = worktree.create_base(load(root), include_uncommitted=False)

    assert (second.project_dir / "src" / "app.txt").read_text() == "v1\n"
    assert not (second.project_dir / "leftover.txt").exists()


def test_edge_mutaspec_folder_is_never_listed_as_uncommitted(git_repo):
    root = project(git_repo)
    worktree.create_base(load(root), include_uncommitted=False)
    write(root, ".mutaspec/runs/baseline.json", "{}")

    base = worktree.create_base(load(root), include_uncommitted=False)

    assert base.left_out == []
