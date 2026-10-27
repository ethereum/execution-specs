"""Tests for splitting oversized pre-alloc groups across xdist workers."""

import re
import textwrap
from typing import Any

import pytest

from ..simulators.helpers.group_splitter import (
    MIN_SPLITTABLE_GROUP_SIZE,
    SUB_GROUPS_PER_WORKER,
    max_group_size,
    plan_sub_group_counts,
)

GROUP_NAME = "group-a"
FILE_COUNT = 8
TESTS_PER_FILE = 10
GROUP_SIZE = FILE_COUNT * TESTS_PER_FILE
WORKER_COUNT = 2
# Small enough for the group above to be split, so that the tests below
# need not collect thousands of items.
TEST_FLOOR = 10

# `-v` reports a test as, e.g.:
#   [gw0] [ 50%] PASSED test_split.py::test_case[1-f3]@group-a#1
REPORT_LINE = re.compile(
    r"^\[(?P<worker>gw\d+)\] .* PASSED .*\[\d+-f(?P<file>\d+)\]"
    rf"@{GROUP_NAME}#(?P<sub_group>\d+)$"
)

conftest_source = textwrap.dedent(
    f"""\
    from pathlib import Path

    import pytest

    from execution_testing.cli.pytest_commands.plugins.consume.simulators\\
        .helpers import group_splitter
    from execution_testing.fixtures import BlockchainEngineXFixture
    from execution_testing.fixtures.consume import TestCaseIndexFile

    group_splitter.MIN_SPLITTABLE_GROUP_SIZE = {TEST_FLOOR}


    def pytest_generate_tests(metafunc):
        # Interleave the files, as the fixture index does, and name the
        # tests so that node ID order interleaves them too.
        metafunc.parametrize(
            "test_case",
            [
                pytest.param(
                    TestCaseIndexFile(
                        id=f"{{index}}-f{{file}}",
                        fixture_hash="0x" + "11" * 32,
                        format=BlockchainEngineXFixture,
                        json_path=Path(f"file_{{file}}.json"),
                    ),
                    id=f"{{index}}-f{{file}}",
                    marks=[pytest.mark.xdist_group(name="{GROUP_NAME}")],
                )
                for index in range({TESTS_PER_FILE})
                for file in range({FILE_COUNT})
            ],
        )


    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(config, items):
        group_splitter.split_oversized_groups(config, items)
    """
)

test_module_source = textwrap.dedent(
    """\
    def test_case(test_case):
        pass
    """
)


def run_split(pytester: pytest.Pytester, *args: str) -> pytest.RunResult:
    """Run the parametrized group with `args` and return the result."""
    pytester.makeconftest(conftest_source)
    pytester.makepyfile(test_split=test_module_source)
    result = pytester.runpytest_subprocess(
        "-p", "no:cacheprovider", "--dist", "loadgroup", "-v", *args
    )
    result.assert_outcomes(passed=GROUP_SIZE)
    return result


def reported_tests(result: pytest.RunResult) -> list[dict[str, Any]]:
    """Return the worker, file and sub-group of each reported test."""
    return [
        match.groupdict()
        for line in result.outlines
        if (match := REPORT_LINE.match(line.strip())) is not None
    ]


def test_cap_is_half_a_fair_share() -> None:
    """The cap is the selection's size over twice the worker count."""
    assert max_group_size(32_000, 8) == 32_000 // (SUB_GROUPS_PER_WORKER * 8)
    assert plan_sub_group_counts({"a": 23_000}, 2_000) == {"a": 12}


def test_cap_never_below_the_floor() -> None:
    """A small selection is never cut into groups below the floor."""
    assert max_group_size(4_958, 8) == MIN_SPLITTABLE_GROUP_SIZE
    assert plan_sub_group_counts({"a": 261}, max_group_size(273, 8)) == {}


def test_only_oversized_groups_are_split() -> None:
    """Groups small enough to schedule around are left untouched."""
    group_sizes = {"large": 9_000, "small": 1_000} | {
        f"tiny-{index}": 10 for index in range(100)
    }
    assert plan_sub_group_counts(group_sizes, 2_250) == {"large": 4}


def test_split_group_runs_on_several_workers(
    pytester: pytest.Pytester,
) -> None:
    """
    A group too large for one worker is spread over all of them.

    This pins the coupling to xdist: the split has to reach the
    scheduler, and each of its sub-groups still has to be pinned to a
    single worker so that the sub-group's client can be shared.
    """
    tests = reported_tests(run_split(pytester, "-n", str(WORKER_COUNT)))
    assert len(tests) == GROUP_SIZE

    workers_of: dict[str, set[str]] = {}
    for test in tests:
        workers_of.setdefault(test["sub_group"], set()).add(test["worker"])
    expected = -(-GROUP_SIZE // max(TEST_FLOOR, GROUP_SIZE // 4))
    assert len(workers_of) == expected, workers_of
    assert all(len(workers) == 1 for workers in workers_of.values()), (
        f"a sub-group ran on several workers, so it could not share its "
        f"client: {workers_of}"
    )
    assert len(set().union(*workers_of.values())) == WORKER_COUNT


def test_fixture_files_stay_in_one_sub_group(
    pytester: pytest.Pytester,
) -> None:
    """Cut a group along its fixture files, not its collection order."""
    tests = reported_tests(run_split(pytester, "-n", str(WORKER_COUNT)))

    sub_groups_of: dict[str, set[str]] = {}
    for test in tests:
        sub_groups_of.setdefault(test["file"], set()).add(test["sub_group"])
    assert all(len(groups) == 1 for groups in sub_groups_of.values()), (
        sub_groups_of
    )


def test_groups_are_untouched_without_distribution(
    pytester: pytest.Pytester,
) -> None:
    """A run with a single worker has nothing to gain from a split."""
    result = run_split(pytester, "-n", "1")
    assert f"{GROUP_NAME}#" not in "\n".join(result.outlines)
