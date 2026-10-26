"""
Tests for the order of the enginex collection.

Enginex runs the largest pre-alloc group first and, within a group, keeps
the tests of one fixture file contiguous so that the worker's fixture file
cache loads each file once per group.
"""

from pathlib import Path
from types import SimpleNamespace
from typing import Any, List, cast

import pytest

from execution_testing.fixtures import BlockchainEngineXFixture
from execution_testing.fixtures.consume import (
    TestCaseBase,
    TestCaseIndexFile,
)

from ..simulators.enginex.conftest import pytest_collection_modifyitems

HASH = "0x" + "11" * 32


def _item(test_id: str, group: str, path: str | None) -> pytest.Item:
    """Return an item stub of `group` whose test case is in `path`."""
    test_case: TestCaseBase
    if path is None:
        test_case = TestCaseBase(
            id=test_id, fixture_hash=HASH, format=BlockchainEngineXFixture
        )
    else:
        test_case = TestCaseIndexFile(
            id=test_id,
            fixture_hash=HASH,
            format=BlockchainEngineXFixture,
            json_path=Path(path),
        )
    marker = pytest.mark.xdist_group(name=group).mark
    return cast(
        pytest.Item,
        SimpleNamespace(
            name=test_id,
            callspec=SimpleNamespace(params={"test_case": test_case}),
            iter_markers=lambda name: [marker] if name == marker.name else [],
        ),
    )


def _sorted_ids(items: List[pytest.Item]) -> List[str]:
    """Sort `items` with the enginex collection hook and return their ids."""
    session = cast(pytest.Session, SimpleNamespace(stash={}))
    config = cast(
        pytest.Config,
        SimpleNamespace(supported_fixture_formats=[BlockchainEngineXFixture]),
    )
    pytest_collection_modifyitems(session, config, items)
    return [cast(Any, item).name for item in items]


def test_largest_group_runs_first() -> None:
    """Order groups by size, largest first, then by group id."""
    items = [
        _item("b1", "g-b", "f.json"),
        _item("a1", "g-a", "f.json"),
        _item("c1", "g-c", "f.json"),
        _item("c2", "g-c", "f.json"),
    ]

    assert _sorted_ids(items) == ["c1", "c2", "a1", "b1"]


def test_files_are_contiguous_within_a_group() -> None:
    """Interleaved fixture files of one group come out grouped by file."""
    items = [
        _item("a1", "g", "for_amsterdam/x/a.json"),
        _item("b1", "g", "for_amsterdam/x/b.json"),
        _item("a2", "g", "for_amsterdam/x/a.json"),
        _item("c1", "g", "for_amsterdam/y/c.json"),
        _item("b2", "g", "for_amsterdam/x/b.json"),
        _item("a3", "g", "for_amsterdam/x/a.json"),
    ]

    assert _sorted_ids(items) == ["a1", "a2", "a3", "b1", "b2", "c1"]


def test_file_order_does_not_cross_groups() -> None:
    """A file shared by two groups is visited once in each group."""
    items = [
        _item("x-a", "g-x", "a.json"),
        _item("y-b", "g-y", "b.json"),
        _item("x-b", "g-x", "b.json"),
        _item("y-a", "g-y", "a.json"),
        _item("x-a2", "g-x", "a.json"),
    ]

    assert _sorted_ids(items) == ["x-a", "x-a2", "x-b", "y-a", "y-b"]


def test_cases_without_a_file_keep_their_order() -> None:
    """Stream test cases carry no path and keep their order in the group."""
    items = [
        _item("s2", "g", None),
        _item("s1", "g", None),
        _item("s3", "g", None),
    ]

    assert _sorted_ids(items) == ["s2", "s1", "s3"]
