"""Tests for the order `consume wirex` runs each group's tests in."""

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterator, cast

import pytest

from execution_testing.cli.pytest_commands.plugins.consume.simulators.helpers.test_tracker import (  # noqa: E501
    enginex_group_counts_key,
)
from execution_testing.cli.pytest_commands.plugins.consume.simulators.wirex import (  # noqa: E501
    conftest as wirex,
)
from execution_testing.fixtures import BlockchainEngineXFixture
from execution_testing.fixtures.consume import TestCaseIndexFile

from .variant_generator import HASH

LARGE_GROUP = "z-group"
"""Sorts after the small group by name, so only its size puts it first."""

SMALL_GROUP = "a-group"


def _payload(block: str, parent: str, invalid: bool = False) -> dict[str, Any]:
    """Return a raw Engine API payload linking `block` to `parent`."""
    payload: dict[str, Any] = {
        "params": [{"blockHash": block, "parentHash": parent}]
    }
    if invalid:
        payload["validationError"] = "TransactionException.X"
    return payload


def _bare_chain(length: int, invalid: bool = False) -> dict[str, Any]:
    """Return a raw fixture without targets, `length` payloads long."""
    payloads = [_payload(f"0x{n}", f"0x{n - 1}") for n in range(1, length + 1)]
    if invalid:
        payloads[-1] = _payload(f"0x{length}", f"0x{length - 1}", True)
    return {"engineNewPayloads": payloads}


def _two_targets() -> dict[str, Any]:
    """Return a raw fixture whose two targets serve 2 and 4 blocks."""
    return {
        "engineNewPayloads": [
            _payload("0xa1", "0x0"),
            _payload("0xb1", "0x0"),
            _payload("0xb2", "0xb1"),
            _payload("0xb3", "0xb2"),
        ],
        "syncPayloads": [
            _payload("0xs1", "0xa1"),
            _payload("0xs2", "0xb3"),
        ],
    }


class _Item:
    """The slice of a collected wirex item the collection hook reads."""

    def __init__(self, case_id: str, json_path: str, group: str) -> None:
        """Hold the test case and its group as the generator marks them."""
        self.nodeid = f"test_via_wirex.py::test[{case_id}]"
        self.callspec = SimpleNamespace(
            params={
                "test_case": TestCaseIndexFile(
                    id=case_id,
                    fixture_hash=HASH,
                    format=BlockchainEngineXFixture,
                    json_path=Path(json_path),
                )
            }
        )
        self.group = group

    def iter_markers(self, name: str) -> Iterator[pytest.Mark]:
        """Yield this item's xdist_group marker."""
        assert name == "xdist_group"
        yield pytest.mark.xdist_group(name=self.group).mark


def _collect(tmp_path: Path, sort: bool) -> tuple[list[str], dict[str, int]]:
    """
    Run the collection hook over a large and a small group.

    The large group holds a short and a long valid chain, a valid
    fixture whose targets serve 2 and 4 blocks, and an invalid chain
    shorter than all of them; both groups' fixtures share files, as
    a fixture file's cases do.
    """
    (tmp_path / "large.json").write_text(
        json.dumps(
            {
                "long": _bare_chain(3),
                "short": _bare_chain(2),
                "multi": _two_targets(),
                "invalid": _bare_chain(2, invalid=True),
            }
        )
    )
    (tmp_path / "small.json").write_text(
        json.dumps({"single": _bare_chain(5)})
    )
    items = [
        _Item("single", "small.json", SMALL_GROUP),
        _Item("invalid", "large.json", LARGE_GROUP),
        _Item("long", "large.json", LARGE_GROUP),
        _Item("multi", "large.json", LARGE_GROUP),
        _Item("short", "large.json", LARGE_GROUP),
    ]
    session = SimpleNamespace(stash=pytest.Stash())

    def getoption(name: str, default: Any = None) -> Any:
        del default
        assert name == "wirex_sort_by_chain_length"
        return sort

    config = SimpleNamespace(
        supported_fixture_formats=[BlockchainEngineXFixture],
        fixtures_source=SimpleNamespace(path=tmp_path),
        getoption=getoption,
    )
    wirex.pytest_collection_modifyitems(
        cast(pytest.Session, session),
        cast(pytest.Config, config),
        cast(list[pytest.Item], items),
    )
    order = [item.callspec.params["test_case"].id for item in items]
    return order, session.stash[enginex_group_counts_key]


def test_groups_run_largest_first_valid_chains_by_length(
    tmp_path: Path,
) -> None:
    """Largest group first; valid by longest target path; invalid last."""
    order, counts = _collect(tmp_path, sort=True)
    assert order == ["short", "long", "multi", "invalid", "single"]
    assert counts == {LARGE_GROUP: 4, SMALL_GROUP: 1}


def test_without_chain_sorting_only_the_group_order_applies(
    tmp_path: Path,
) -> None:
    """`--wirex-no-sort-by-chain-length` orders a group by node ID."""
    order, counts = _collect(tmp_path, sort=False)
    assert order == ["invalid", "long", "multi", "short", "single"]
    assert counts == {LARGE_GROUP: 4, SMALL_GROUP: 1}
