import json

import pytest

from mutaspec import gitrepo


@pytest.mark.parametrize("argv", [["init"], ["config", "check"]])
def test_ac10_not_a_git_repo_stops_with_exit_3(tmp_path, run_cli, argv):
    result = run_cli(tmp_path, *argv)

    assert result.code == 3
    assert "mutaspec needs a git repository" in result.err


def test_ac10_git_not_installed_stops_with_exit_3(tmp_path, run_cli, monkeypatch):
    monkeypatch.setattr(gitrepo, "GIT", "git-that-does-not-exist")

    result = run_cli(tmp_path, "init")

    assert result.code == 3
    assert "mutaspec needs a git repository" in result.err
    assert "git not found" in result.err


@pytest.mark.parametrize("argv", [["init", "--json"], ["config", "check", "--json"]])
def test_ac12_json_error_is_one_object_on_stdout(tmp_path, run_cli, argv):
    result = run_cli(tmp_path, *argv)

    assert result.code == 3
    payload = json.loads(result.out)  # exactly one JSON document, nothing else
    assert payload["ok"] is False
    assert payload["exit_code"] == 3
    assert "mutaspec needs a git repository" in payload["error"]["message"]
    assert result.err == ""


def test_usage_error_exits_2(tmp_path, run_cli):
    result = run_cli(tmp_path, "no-such-command")

    assert result.code == 2
