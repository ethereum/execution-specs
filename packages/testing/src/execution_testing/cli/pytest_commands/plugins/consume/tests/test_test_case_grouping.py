"""Tests for grouping collected test cases by fixture file."""

from pathlib import Path
from typing import List

from execution_testing.cli.pytest_commands.plugins.consume.consume import (
    group_test_cases_by_fixture_file,
)
from execution_testing.fixtures import BlockchainFixture
from execution_testing.fixtures.consume import (
    TestCaseBase,
    TestCaseIndexFile,
)

HASH = "0x" + "11" * 32


def _case(test_id: str, path: str) -> TestCaseIndexFile:
    """Create an index test case for `path` with the given id."""
    return TestCaseIndexFile(
        id=test_id,
        fixture_hash=HASH,
        format=BlockchainFixture,
        json_path=Path(path),
    )


def test_cases_of_one_file_become_contiguous() -> None:
    """Interleaved files come out grouped, in file path order."""
    cases: List[TestCaseBase] = [
        _case("a1", "for_osaka/x/a.json"),
        _case("b1", "for_osaka/x/b.json"),
        _case("a2", "for_osaka/x/a.json"),
        _case("c1", "for_amsterdam/y/c.json"),
        _case("b2", "for_osaka/x/b.json"),
        _case("a3", "for_osaka/x/a.json"),
    ]

    grouped = group_test_cases_by_fixture_file(cases)

    assert [tc.id for tc in grouped] == ["c1", "a1", "a2", "a3", "b1", "b2"]
    assert sorted(tc.id for tc in grouped) == sorted(tc.id for tc in cases)


def test_order_within_a_file_is_preserved() -> None:
    """Grouping is stable: the index order inside a file is kept."""
    cases: List[TestCaseBase] = [
        _case("z", "f.json"),
        _case("m", "g.json"),
        _case("a", "f.json"),
    ]

    grouped = group_test_cases_by_fixture_file(cases)

    assert [tc.id for tc in grouped] == ["z", "a", "m"]


def test_forks_run_one_after_another() -> None:
    """Fork directories are the leading path component, so forks group."""
    cases: List[TestCaseBase] = [
        _case("o1", "for_osaka/x/a.json"),
        _case("p1", "for_prague/x/a.json"),
        _case("o2", "for_osaka/x/b.json"),
        _case("p2", "for_prague/x/b.json"),
    ]

    forks = [
        str(tc.json_path).split("/")[0]  # type: ignore[attr-defined]
        for tc in group_test_cases_by_fixture_file(cases)
    ]

    assert forks == ["for_osaka", "for_osaka", "for_prague", "for_prague"]


def test_cases_without_a_file_keep_their_order() -> None:
    """Stream test cases carry no path and are returned untouched."""
    cases: List[TestCaseBase] = [
        TestCaseBase(id="s2", fixture_hash=HASH, format=BlockchainFixture),
        TestCaseBase(id="s1", fixture_hash=HASH, format=BlockchainFixture),
    ]

    assert list(group_test_cases_by_fixture_file(cases)) == cases
