import pytest
from conftest import write

from mutaspec import config as cfg
from mutaspec.config import load, parse_duration, source_files
from mutaspec.errors import MutaspecError

VALID = """
[project]
source = ["src/main/java/**"]
tests = ["src/test/java/**"]

[[suites]]
name = "unit"
level = "unit"
run = "mvn -q test"

[[suites]]
name = "api"
level = "api"
start = "java -jar app.jar --server.port={port}"
ready = "curl -sf http://localhost:{port}/"
run = "mvn -q test -Dgroups=api"
timeout = "5m"
"""


def test_ac9_valid_config_lists_each_suite_with_its_level(git_repo, run_cli):
    write(git_repo, "mutaspec.toml", VALID)

    result = run_cli(git_repo, "config", "check")

    assert result.code == 0
    assert "unit (unit)" in result.out
    assert "api (api)" in result.out


def test_ac9_json_lists_suites(git_repo, run_cli):
    write(git_repo, "mutaspec.toml", VALID)

    result = run_cli(git_repo, "config", "check", "--json")

    assert result.code == 0
    assert result.json()["suites"] == [
        {"name": "unit", "level": "unit"},
        {"name": "api", "level": "api"},
    ]


def test_ac8_unknown_level_names_suite_and_field(git_repo, run_cli):
    write(git_repo, "mutaspec.toml", VALID.replace('level = "api"', 'level = "e2e"'))

    result = run_cli(git_repo, "config", "check")

    assert result.code == 2
    assert "api" in result.err
    assert "level" in result.err
    assert "e2e" in result.err


def test_ac8_missing_run_names_suite_and_field(git_repo, run_cli):
    write(git_repo, "mutaspec.toml", VALID.replace('run = "mvn -q test"\n', ""))

    result = run_cli(git_repo, "config", "check", "--json")

    assert result.code == 2
    error = result.json()["error"]
    assert "unit" in error["where"]
    assert "run" in error["where"]


def test_ac11_no_config_says_run_init(git_repo, run_cli):
    result = run_cli(git_repo, "config", "check")

    assert result.code == 2
    assert "mutaspec init" in result.err


def test_edge_unknown_key_is_named(git_repo, run_cli):
    write(git_repo, "mutaspec.toml", VALID.replace('timeout = "5m"', 'timout = "5m"'))

    result = run_cli(git_repo, "config", "check")

    assert result.code == 2
    assert "timout" in result.err


def test_edge_unknown_project_key_is_named(git_repo, run_cli):
    write(git_repo, "mutaspec.toml", VALID.replace("[project]\n", '[project]\nsorce = ["x"]\n'))

    result = run_cli(git_repo, "config", "check")

    assert result.code == 2
    assert "sorce" in result.err


def test_edge_bad_toml_is_a_config_error(git_repo, run_cli):
    write(git_repo, "mutaspec.toml", "[project\n")

    result = run_cli(git_repo, "config", "check")

    assert result.code == 2
    assert "mutaspec.toml" in result.err


def test_edge_duplicate_suite_names(git_repo, run_cli):
    write(git_repo, "mutaspec.toml", VALID.replace('name = "api"', 'name = "unit"'))

    result = run_cli(git_repo, "config", "check")

    assert result.code == 2
    assert "unit" in result.err


def test_edge_no_suites(git_repo, run_cli):
    write(git_repo, "mutaspec.toml", VALID.split("[[suites]]")[0])

    result = run_cli(git_repo, "config", "check")

    assert result.code == 2
    assert "suites" in result.err


def test_edge_bad_duration_names_field(git_repo, run_cli):
    write(git_repo, "mutaspec.toml", VALID.replace('timeout = "5m"', 'timeout = "five"'))

    result = run_cli(git_repo, "config", "check")

    assert result.code == 2
    assert "timeout" in result.err


@pytest.mark.parametrize(
    ("text", "seconds"), [("120s", 120), ("5m", 300), ("1h", 3600), ("500ms", 0.5)]
)
def test_durations(text, seconds):
    assert parse_duration(text, "x") == seconds


def test_load_defaults(git_repo):
    write(git_repo, "mutaspec.toml", VALID)

    config = load(git_repo)

    assert config.project.baseline == "HEAD"
    assert config.project.exclude == ()
    assert config.suites[1].timeout == 300
    assert config.suites[0].repeat == 1


def test_load_wrong_type_names_field(git_repo):
    write(git_repo, "mutaspec.toml", VALID.replace('source = ["src/main/java/**"]', "source = 3"))

    with pytest.raises(MutaspecError) as info:
        load(git_repo)

    assert "source" in info.value.where


def test_ac7_overlapping_source_and_tests_names_the_files(git_repo, run_cli):
    write(git_repo, "src/shop/Price.java")
    write(git_repo, "src/shop/PriceTest.java")
    write(
        git_repo,
        "mutaspec.toml",
        VALID.replace('"src/main/java/**"', '"src/**"').replace(
            '"src/test/java/**"', '"src/**/*Test.java"'
        ),
    )

    result = run_cli(git_repo, "config", "check")

    assert result.code == 2
    assert "src/shop/PriceTest.java" in result.err
    assert "src/shop/Price.java" not in result.err.replace("PriceTest", "")


def test_ac7_exclude_removes_the_overlap(git_repo, run_cli):
    write(git_repo, "src/shop/Price.java")
    write(git_repo, "src/shop/PriceTest.java")
    text = VALID.replace('"src/main/java/**"', '"src/**"').replace(
        '"src/test/java/**"', '"src/**/*Test.java"'
    )
    text = text.replace("[project]\n", '[project]\nexclude = ["**/*Test.java"]\n')
    write(git_repo, "mutaspec.toml", text)

    result = run_cli(git_repo, "config", "check")

    assert result.code == 0, result.err


def test_source_and_test_files_are_split_per_file(git_repo):
    write(git_repo, "src/main/java/shop/Price.java")
    write(git_repo, "src/main/java/shop/gen/Stub.java")
    write(git_repo, "src/test/java/shop/PriceTest.java")
    text = VALID.replace("[project]\n", '[project]\nexclude = ["**/gen/**"]\n')
    write(git_repo, "mutaspec.toml", text)

    config = load(git_repo)

    assert source_files(config) == ["src/main/java/shop/Price.java"]
    assert cfg.test_files(config) == ["src/test/java/shop/PriceTest.java"]
