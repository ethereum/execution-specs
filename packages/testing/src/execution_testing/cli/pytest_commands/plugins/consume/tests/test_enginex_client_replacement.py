"""
Tests for replacing a reused enginex client after a deep chain.

Each enginex test rewinds its group's client to genesis. Clients listed
in `MAX_REUSED_HEAD_NUMBER` are replaced after a test that leaves a
head above their limit, so the next test starts on a fresh client.
"""

from types import SimpleNamespace
from typing import cast

import pytest
from hive.client import Client

from execution_testing.fixtures import BlockchainEngineXFixture

from ..simulators.enginex.conftest import (
    deepest_head_number,
    max_reused_head_number,
)
from ..simulators.helpers.test_tracker import PreAllocGroupTestTracker
from ..simulators.multi_test_client import MultiTestClientManager


def _payload(number: int, valid: bool = True) -> SimpleNamespace:
    """Return the slice of an engine payload the decision reads."""
    return SimpleNamespace(
        params=[SimpleNamespace(number=number)], valid=lambda: valid
    )


def _fixture(*payloads: SimpleNamespace) -> BlockchainEngineXFixture:
    """Return a fixture stub holding `payloads`."""
    return cast(
        BlockchainEngineXFixture, SimpleNamespace(payloads=list(payloads))
    )


def test_deepest_head_is_the_highest_valid_block() -> None:
    """Return the highest valid block number, in any payload order."""
    assert deepest_head_number(_fixture(_payload(2), _payload(257))) == 257


def test_deepest_head_ignores_invalid_payloads() -> None:
    """Return the highest valid block, not an invalid one above it."""
    fixture = _fixture(_payload(1), _payload(2), _payload(300, valid=False))
    assert deepest_head_number(fixture) == 2


def test_deepest_head_is_genesis_without_valid_payloads() -> None:
    """Return 0 when every payload is invalid."""
    assert deepest_head_number(_fixture(_payload(1, valid=False))) == 0


@pytest.mark.parametrize(
    "client_type_name", ["ethrex", "ethrex_default", "ethrex_main"]
)
def test_ethrex_has_a_limit(client_type_name: str) -> None:
    """Limit ethrex to 128 blocks, whatever its Hive name tag."""
    assert max_reused_head_number(client_type_name) == 128


@pytest.mark.parametrize(
    "client_type_name",
    ["go-ethereum_default", "nethermind", "reth_default", "besu"],
)
def test_other_clients_have_no_limit(client_type_name: str) -> None:
    """Always reuse a client that is not listed."""
    assert max_reused_head_number(client_type_name) is None


class _StubClient:
    """A client that only remembers whether it was stopped."""

    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        """Record the stop."""
        self.stopped = True


def test_discard_client_lets_the_group_start_a_fresh_client() -> None:
    """
    Stop the discarded client, keep the group's test count, and stop
    the replacement when the group completes.
    """
    manager = MultiTestClientManager()
    tracker = PreAllocGroupTestTracker()
    tracker.set_group_test_count("group", 2)
    manager.set_test_tracker(tracker)
    first = _StubClient()
    manager.register_client("group", cast(Client, first))

    manager.discard_client("group")
    manager.mark_test_completed("group", "test_deep")
    assert first.stopped
    assert manager.get_client("group") is None

    second = _StubClient()
    manager.register_client("group", cast(Client, second))
    manager.mark_test_completed("group", "test_next")
    assert second.stopped
    assert manager.get_client("group") is None


def test_discard_client_without_a_client_is_a_no_op() -> None:
    """Do nothing when the group has no registered client."""
    MultiTestClientManager().discard_client("group")
