"""Per-test results from JUnit XML (spec 0002 FR5, AC5, AC6; D29)."""

import pytest
from conftest import write

from mutaspec import junit

GLOB = "**/target/surefire-reports/TEST-*.xml"


def suite(*cases: str) -> str:
    return f'<testsuite name="s" tests="{len(cases)}">{"".join(cases)}</testsuite>'


def xml(*cases: str) -> str:
    return f'<?xml version="1.0"?>{suite(*cases)}'


def case(name: str, outcome: str = "pass", cls: str = "shop.PricingTest") -> str:
    inner = {
        "pass": "",
        "fail": '<failure message="x">trace</failure>',
        "error": '<error message="x">trace</error>',
        "skip": "<skipped/>",
        "flaky": '<flakyFailure message="x"/>',
    }[outcome]
    return f'<testcase name="{name}" classname="{cls}" time="0.01">{inner}</testcase>'


def test_fr5_outcomes_of_one_run(tmp_path):
    write(
        tmp_path,
        "target/surefire-reports/TEST-shop.PricingTest.xml",
        xml(case("a"), case("b", "fail"), case("c", "error"), case("d", "skip")),
    )

    results = junit.read_results(tmp_path, GLOB)

    assert results == {
        "shop.PricingTest#a": "passed",
        "shop.PricingTest#b": "failed",
        "shop.PricingTest#c": "failed",
        "shop.PricingTest#d": "skipped",
    }


def test_fr5_files_in_modules_and_testsuites_root_are_read(tmp_path):
    write(tmp_path, "a/target/surefire-reports/TEST-x.xml", xml(case("a", cls="m1.T")))
    write(
        tmp_path,
        "b/target/surefire-reports/TEST-y.xml",
        f"<testsuites>{suite(case('b', cls='m2.T'))}</testsuites>",
    )
    write(tmp_path, "b/target/surefire-reports/other.xml", xml(case("z", cls="no.T")))

    assert junit.read_results(tmp_path, GLOB) == {"m1.T#a": "passed", "m2.T#b": "passed"}


def test_no_matching_files_gives_no_results(tmp_path):
    assert junit.read_results(tmp_path, GLOB) == {}


def test_broken_xml_names_the_file(tmp_path):
    write(tmp_path, "target/surefire-reports/TEST-bad.xml", "<testsuite><testcase")

    with pytest.raises(junit.JunitError) as info:
        junit.read_results(tmp_path, GLOB)

    assert "TEST-bad.xml" in str(info.value)


def test_d29_clear_deletes_old_result_files_only(tmp_path):
    old = write(tmp_path, "target/surefire-reports/TEST-x.xml", xml(case("a")))
    keep = write(tmp_path, "target/surefire-reports/x.txt", "keep")

    junit.clear(tmp_path, GLOB)

    assert not old.exists()
    assert keep.exists()


@pytest.mark.parametrize(
    ("runs", "status"),
    [
        (["passed", "passed"], "pass"),
        (["failed", "failed"], "failing"),  # AC5
        (["failed", "passed"], "flaky"),  # AC6
        (["passed", "failed", "passed"], "flaky"),
        (["passed", "flaky"], "flaky"),  # passed only on a Surefire re-run
        (["passed", "skipped"], "pass"),
        (["failed"], "failing"),
    ],
)
def test_fr5_status_over_runs(runs, status):
    assert junit.combine([{"T#a": r} for r in runs]) == {"T#a": status}


def test_fr5_skipped_tests_are_left_out():
    assert junit.combine([{"T#a": "skipped"}, {"T#a": "skipped"}]) == {}


def test_fr5_a_test_missing_from_one_run_uses_the_runs_it_is_in():
    assert junit.combine([{"T#a": "failed"}, {}]) == {"T#a": "failing"}


def test_surefire_flaky_failure_is_flaky_in_that_run(tmp_path):
    write(tmp_path, "target/surefire-reports/TEST-x.xml", xml(case("a", "flaky")))

    assert junit.read_results(tmp_path, GLOB) == {"shop.PricingTest#a": "flaky"}
