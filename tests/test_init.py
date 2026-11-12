import tomllib

import pytest
from conftest import commit_all, git, write

POM = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>example</groupId>
  <artifactId>app</artifactId>
  <version>1</version>
  <dependencies>
{deps}
  </dependencies>
</project>
"""


def dep(artifact: str, group: str = "org.springframework.boot") -> str:
    return (
        f"    <dependency><groupId>{group}</groupId>"
        f"<artifactId>{artifact}</artifactId></dependency>"
    )


@pytest.fixture
def maven_repo(git_repo):
    write(git_repo, "pom.xml", POM.format(deps=dep("junit-jupiter", "org.junit.jupiter")))
    write(git_repo, "src/main/java/app/Price.java", "class Price {}")
    write(git_repo, "src/test/java/app/PriceTest.java", "class PriceTest {}")
    commit_all(git_repo)
    return git_repo


def read_config(repo) -> dict:
    return tomllib.loads((repo / "mutaspec.toml").read_text())


def test_ac1_maven_project_gets_source_tests_build_and_unit_suite(maven_repo, run_cli):
    result = run_cli(maven_repo, "init")

    assert result.code == 0, result.err
    config = read_config(maven_repo)
    assert config["project"]["source"] == ["src/main/java/**"]
    assert config["project"]["tests"] == ["src/test/java/**"]
    assert config["project"]["build"] == "mvn -q -DskipTests test-compile"
    [unit] = config["suites"]
    assert unit["name"] == "unit"
    assert unit["level"] == "unit"
    assert unit["run"] == "mvn -q test -DexcludedGroups=api"


def test_ac1_written_config_passes_config_check(maven_repo, run_cli):
    run_cli(maven_repo, "init")

    result = run_cli(maven_repo, "config", "check")

    assert result.code == 0, result.err
    assert "unit (unit)" in result.out


def test_ac4_existing_config_is_not_overwritten(maven_repo, run_cli):
    write(maven_repo, "mutaspec.toml", "# mine\n")

    result = run_cli(maven_repo, "init")

    assert result.code == 2
    assert "--force" in result.err
    assert (maven_repo / "mutaspec.toml").read_text() == "# mine\n"


def test_ac4_force_overwrites(maven_repo, run_cli):
    write(maven_repo, "mutaspec.toml", "# mine\n")

    result = run_cli(maven_repo, "init", "--force")

    assert result.code == 0, result.err
    assert "unit" in read_config(maven_repo)["suites"][0]["name"]


def test_ac5_only_config_and_mutaspec_gitignore_are_new(maven_repo, run_cli):
    run_cli(maven_repo, "init")

    status = git(maven_repo, "status", "--porcelain", "--untracked-files=all").splitlines()
    assert sorted(status) == ["?? .mutaspec/.gitignore", "?? mutaspec.toml"]


def test_ac5_users_gitignore_is_not_touched(maven_repo, run_cli):
    write(maven_repo, ".gitignore", "target/\n")
    commit_all(maven_repo)

    run_cli(maven_repo, "init")

    assert (maven_repo / ".gitignore").read_text() == "target/\n"


@pytest.mark.parametrize(
    ("path", "ignored"),
    [
        (".mutaspec/worktrees/m1/Price.java", True),
        (".mutaspec/runs/baseline.json", True),
        (".mutaspec/mutants/mutants.json", False),
        (".mutaspec/history.jsonl", False),
    ],
)
def test_ac6_run_output_is_ignored_and_mutant_set_is_not(maven_repo, run_cli, path, ignored):
    run_cli(maven_repo, "init")
    write(maven_repo, path, "x")

    status = git(maven_repo, "status", "--porcelain", "--untracked-files=all")

    assert (path in status) is not ignored


def test_edge_mvnw_is_used_when_present(maven_repo, run_cli):
    write(maven_repo, "mvnw", "#!/bin/sh\n")

    run_cli(maven_repo, "init")

    config = read_config(maven_repo)
    assert config["project"]["build"].startswith("./mvnw ")
    assert config["suites"][0]["run"].startswith("./mvnw ")


def test_init_json_reports_what_was_written(maven_repo, run_cli):
    result = run_cli(maven_repo, "init", "--json")

    payload = result.json()
    assert payload["ok"] is True
    assert payload["project_type"] == "maven"
    assert sorted(payload["written"]) == [".mutaspec/.gitignore", "mutaspec.toml"]


def spring_repo(repo, *artifacts):
    deps = "\n".join(dep(a) for a in artifacts)
    write(repo, "pom.xml", POM.format(deps=deps))
    commit_all(repo)
    return repo


def test_ac2_spring_boot_web_gets_api_suite(maven_repo, run_cli):
    spring_repo(maven_repo, "spring-boot-starter-web", "spring-boot-starter-actuator")

    result = run_cli(maven_repo, "init")

    assert result.code == 0, result.err
    unit, api = read_config(maven_repo)["suites"]
    assert unit["run"] == "mvn -q test -DexcludedGroups=api"
    assert api["name"] == "api"
    assert api["level"] == "api"
    assert api["setup"] == "mvn -q -DskipTests package"  # builds the app
    assert api["start"] == "java -jar target/*.jar --server.port={port}"  # starts it on {port}
    assert api["ready"] == "curl -sf http://localhost:{port}/actuator/health"  # waits
    assert api["run"] == "mvn -q test -Dgroups=api -DbaseUrl=http://localhost:{port}"
    assert "teardown" not in api  # mutaspec stops the start process itself
    assert "stops" in (maven_repo / "mutaspec.toml").read_text()


def test_ac2_api_suite_passes_config_check(maven_repo, run_cli):
    spring_repo(maven_repo, "spring-boot-starter-web", "spring-boot-starter-actuator")
    run_cli(maven_repo, "init")

    result = run_cli(maven_repo, "config", "check")

    assert result.code == 0, result.err
    assert "api (api)" in result.out


def test_ac2_no_web_starter_means_no_api_suite(maven_repo, run_cli):
    spring_repo(maven_repo, "spring-boot-starter", "spring-boot-starter-actuator")

    run_cli(maven_repo, "init")

    assert [s["name"] for s in read_config(maven_repo)["suites"]] == ["unit"]


def test_edge_no_actuator_ready_waits_for_any_http_answer(maven_repo, run_cli):
    spring_repo(maven_repo, "spring-boot-starter-web")

    run_cli(maven_repo, "init")

    api = read_config(maven_repo)["suites"][1]
    assert api["ready"] == "curl -s -o /dev/null http://localhost:{port}/"


def test_edge_mvnw_in_api_suite(maven_repo, run_cli):
    spring_repo(maven_repo, "spring-boot-starter-web")
    write(maven_repo, "mvnw", "#!/bin/sh\n")

    run_cli(maven_repo, "init")

    api = read_config(maven_repo)["suites"][1]
    assert api["setup"].startswith("./mvnw ")
    assert api["run"].startswith("./mvnw ")
