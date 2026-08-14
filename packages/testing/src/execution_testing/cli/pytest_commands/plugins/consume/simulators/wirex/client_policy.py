"""
The wirex client replacement policy.

This module overrides the shared `client` fixture and must therefore be
the *last* entry in the wirex conftest's ``pytest_plugins``: the
conftest module itself is registered before the plugins it declares, so
a same-named fixture defined in the conftest would be shadowed by
`multi_test_client`'s - pytest resolves duplicate plugin fixtures in
favor of the most recently registered plugin.
"""

import logging
from typing import TYPE_CHECKING, Generator

import pytest
from hive.client import Client, ClientType
from hive.testing import HiveTest

from execution_testing.devp2p.chain import Chain
from execution_testing.fixtures import BlockchainEngineXFixture
from execution_testing.rpc import EthRPC

from ..helpers.test_tracker import make_group_identifier
from ..multi_test_client import MultiTestClientManager, group_client
from ..simulator_logic.test_via_wirex import expects_rejection

if TYPE_CHECKING:
    from ..timing_data import TimingData

logger = logging.getLogger(__name__)


def client_head_number(client: Client) -> int:
    """Return the block number of `client`'s current head."""
    with EthRPC(f"http://{client.ip}:8545") as rpc:
        head_block = rpc.get_block_by_number("latest")
    return 0 if head_block is None else int(head_block["number"], 16)


@pytest.fixture(scope="function")
def client(
    multi_test_hive_test: HiveTest,
    multi_test_client_manager: MultiTestClientManager,
    fixture: BlockchainEngineXFixture,
    client_type: ClientType,
    environment: dict,
    client_genesis: dict,
    total_timing_data: "TimingData",
    request: pytest.FixtureRequest,
    chain: Chain,
) -> Generator[Client, None, None]:
    """
    Provide the group's client, replaced with a fresh one when reuse
    would starve a rejection verdict.

    A rejection target strictly below the reused client's head cannot
    be judged over devp2p: the sync machinery of geth-like clients
    refuses to walk its head backwards, so the target's ancestry never
    arrives and the head stays unjudgeable. Delivering that ancestry
    over the Engine API instead would take the verdict off the sync
    path, which is exactly the coverage this simulator exists to
    state - so the group's client is discarded and the test gets a
    fresh one, at genesis, for which the whole chain (invalid block
    included) is above the head and travels the wire. Tests that
    follow in the same group reuse the replacement.

    The default ordering (valid chains before invalid ones, each by
    ascending chain length) makes the replacement rare: at most one
    per group, at the valid-to-invalid boundary, and only when the
    group's tallest valid chain outgrows its shortest invalid one.
    Equal-height targets sync fine and keep the reused client.
    """
    if expects_rejection(fixture):
        group_identifier = make_group_identifier(
            fixture.pre_hash, client_type.name
        )
        running = multi_test_client_manager.get_client(group_identifier)
        if running is not None:
            head_number = client_head_number(running)
            if chain.head.number < head_number:
                logger.info(
                    f"Rejection target {chain.head.number} is below the "
                    f"reused client's head {head_number}; replacing the "
                    "client so the verdict stays on the sync path"
                )
                multi_test_client_manager.discard_client(group_identifier)
    yield from group_client(
        multi_test_hive_test,
        multi_test_client_manager,
        fixture,
        client_type,
        environment,
        client_genesis,
        total_timing_data,
        request,
    )
