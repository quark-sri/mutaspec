import json
import time
import tomllib

import pytest
from conftest import SHOP

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


@pytest.mark.parametrize("argv", [["init", "--json"], ["config", "check", "--json"]])
def test_ac12_json_success_is_one_object_on_stdout(shop_repo, run_cli, argv):
    if argv[0] == "config":
        run_cli(shop_repo, "init")

    result = run_cli(shop_repo, *argv)

    assert result.code == 0
    payload = json.loads(result.out)  # exactly one JSON document, nothing else
    assert payload["ok"] is True
    assert payload["exit_code"] == 0


# The config the spec (SC1) says init writes for examples/shop.
SPEC_EXAMPLE = {
    "project": {
        "baseline": "HEAD",
        "source": ["src/main/java/**"],
        "tests": ["src/test/java/**"],
        "spec": ["docs/**/*.md", "src/main/resources/openapi.yaml"],
        "build": "mvn -q -DskipTests test-compile",
    },
    "suites": [
        {
            "name": "unit",
            "level": "unit",
            "run": "mvn -q test -DexcludedGroups=api",
            "timeout": "300s",
        },
        {
            "name": "api",
            "level": "api",
            "setup": "mvn -q -DskipTests package",
            "start": "java -jar target/*.jar --server.port={port}",
            "ready": "curl -sf http://localhost:{port}/actuator/health",
            "ready_timeout": "60s",
            "run": "mvn -q test -Dgroups=api -DbaseUrl=http://localhost:{port}",
            "timeout": "300s",
        },
    ],
}


def test_sc1_shop_init_and_check_work_with_no_edits(shop_repo, run_cli):
    init = run_cli(shop_repo, "init")
    check = run_cli(shop_repo, "config", "check")

    assert init.code == 0, init.err
    assert check.code == 0, check.err
    written = (shop_repo / "mutaspec.toml").read_text()
    assert tomllib.loads(written) == SPEC_EXAMPLE
    assert written == (SHOP / "mutaspec.toml").read_text()  # golden file is current


def test_sc2_init_and_check_take_under_2_seconds(shop_repo, run_cli):
    started = time.perf_counter()
    run_cli(shop_repo, "init")
    run_cli(shop_repo, "config", "check")

    assert time.perf_counter() - started < 2
