"""
The wirex client policy: group reuse, replacement, and isolation.

This module overrides the shared `client` fixture and must therefore be
the *last* entry in the wirex conftest's ``pytest_plugins``: the
conftest module itself is registered before the plugins it declares, so
a same-named fixture defined in the conftest would be shadowed by
`multi_test_client`'s - pytest resolves duplicate plugin fixtures in
favor of the most recently registered plugin.

Three policies live here:

- A single-target fixture runs on the pre-allocation group's reused
  client, exactly as `consume enginex` would run it.
- A single-target rejection whose head sits below the reused client's
  is handed a fresh client under the group's identifier, because reuse
  would starve the verdict (see `client`).
- A fixture announcing several sync targets runs each target on its
  own isolated client: the fill side orders rejected targets first and
  the valid target last, but a client that has synced a chain with a
  bad block has been observed to back off in ways that starve the next
  sync, so isolation is the safe policy until repeated mixed-validity
  smokes prove reuse harmless. The authored ancestry is never
  delivered over the Engine API to make reuse work - that would take
  the coverage off the wire this simulator exists to state.
"""

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, ContextManager, Generator, Iterator

import pytest
from hive.client import Client, ClientType
from hive.testing import HiveTest

from execution_testing.devp2p.peer import MockPeer
from execution_testing.exceptions import ExceptionMapper
from execution_testing.fixtures import BlockchainEngineXFixture
from execution_testing.rpc import EngineRPC, EthRPC

from ..helpers.test_tracker import make_group_identifier
from ..multi_test_client import (
    MultiTestClientManager,
    boot_managed_client,
    group_client,
)
from .conftest import dial_mock_peer
from .sync_targets import SyncTargetCase

if TYPE_CHECKING:
    from ..timing_data import TimingData

logger = logging.getLogger(__name__)


def isolated_identifier(group_identifier: str, index: int) -> str:
    """
    Return the client identifier for one sync target's isolated client.

    The suffix is the target's stable position in the fixture's
    announcement order, so logs and Hive artifacts name which branch a
    client served. Targets of one fixture run strictly one after
    another and the identifier is released when its target completes,
    so the key never collides within a session.
    """
    return f"{group_identifier}-t{index}"


def client_head_number(client: Client) -> int:
    """Return the block number of `client`'s current head."""
    with EthRPC(f"http://{client.ip}:8545") as rpc:
        head_block = rpc.get_block_by_number("latest")
    return 0 if head_block is None else int(head_block["number"], 16)


def build_engine_rpc(
    client: Client, exception_mapper: ExceptionMapper | None
) -> EngineRPC:
    """Return an Engine RPC handle for `client`, mapper attached."""
    if exception_mapper:
        return EngineRPC(
            f"http://{client.ip}:8551",
            response_validation_context={
                "exception_mapper": exception_mapper,
            },
        )
    return EngineRPC(f"http://{client.ip}:8551")


@dataclass(frozen=True)
class TargetContext:
    """Everything one sync target needs to talk to its own client."""

    client: Client
    eth_rpc: EthRPC
    engine_rpc: EngineRPC
    mock_peer: MockPeer


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
    sync_target_cases: list[SyncTargetCase],
    mock_peers: dict[str, MockPeer],
) -> Generator[Client, None, None]:
    """
    Provide this test's client, per the wirex client policy.

    A fixture announcing several sync targets gets an isolated fresh
    client for its first target - the test body opens equally isolated
    contexts for the rest - and the group's reused client is never
    touched: a rejected branch leaves sync machinery in a backoff
    state that has been observed to starve a following valid sync, and
    a multi-target fixture is precisely a sequence of such branches.
    The test still counts toward its group's completion, so the
    group's client (used by the group's other tests) is torn down on
    time.

    A single-target fixture runs on the group's client, replaced with
    a fresh one when reuse would starve a rejection verdict: a
    rejection target strictly below the reused client's head cannot be
    judged over devp2p - the sync machinery of geth-like clients
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
    group_identifier = make_group_identifier(
        fixture.pre_hash, client_type.name
    )

    if len(sync_target_cases) > 1:
        first_case = sync_target_cases[0]
        identifier = isolated_identifier(
            group_identifier, first_case.path.index
        )
        logger.info(
            f"Fixture announces {first_case.path.total} sync targets; "
            f"running {first_case.name} on an isolated client"
        )
        isolated = boot_managed_client(
            multi_test_hive_test,
            multi_test_client_manager,
            identifier,
            client_type,
            environment,
            client_genesis,
            total_timing_data,
        )
        try:
            yield isolated
        finally:
            peer = mock_peers.pop(isolated.id, None)
            if peer is not None:
                peer.close()
            multi_test_client_manager.discard_client(identifier)
            multi_test_client_manager.mark_test_completed(
                group_identifier, request.node.nodeid
            )
        return

    (case,) = sync_target_cases
    if case.expects_rejection:
        running = multi_test_client_manager.get_client(group_identifier)
        if running is not None:
            head_number = client_head_number(running)
            if case.chain.head.number < head_number:
                logger.info(
                    f"Rejection target {case.chain.head.number} is below "
                    f"the reused client's head {head_number}; replacing "
                    "the client so the verdict stays on the sync path"
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


@pytest.fixture(scope="function")
def target_context_factory(
    multi_test_hive_test: HiveTest,
    hive_test: HiveTest,
    multi_test_client_manager: MultiTestClientManager,
    fixture: BlockchainEngineXFixture,
    client_type: ClientType,
    environment: dict,
    client_genesis: dict,
    total_timing_data: "TimingData",
    wirex_eth_versions: tuple[int, ...],
    client_exception_mapper: ExceptionMapper | None,
) -> Callable[[SyncTargetCase], ContextManager[TargetContext]]:
    """
    Open an isolated client context for one sync target.

    The test body calls this for every target after the first (whose
    context the ordinary fixtures provide): each call boots a fresh
    manager-tracked client at the group's genesis, registers it with
    the Hive test so its logs land in the result, dials it with its
    own mock peer serving the target's chain, and tears everything
    down when the target completes - the peer closed, the client
    stopped and released. A failure inside the context still tears it
    down, and the session-end manager cleanup backstops anything that
    escapes.

    The registration target must be the per-test `hive_test`, never
    the module-scoped test the client was started under: hive's
    multi-test registration installs a copy of the client record
    without the stop authority in the target test, so registering a
    client with its own source test overwrites the original record
    and makes the later stop a silent no-op - the container leaks
    with every call reporting success.
    """
    group_identifier = make_group_identifier(
        fixture.pre_hash, client_type.name
    )

    @contextmanager
    def open_target_context(case: SyncTargetCase) -> Iterator[TargetContext]:
        identifier = isolated_identifier(group_identifier, case.path.index)
        logger.info(f"Running {case.name} on an isolated client")
        target_client = boot_managed_client(
            multi_test_hive_test,
            multi_test_client_manager,
            identifier,
            client_type,
            environment,
            client_genesis,
            total_timing_data,
        )
        peer: MockPeer | None = None
        try:
            hive_test.register_multi_test_client(target_client)
            with (
                EthRPC(f"http://{target_client.ip}:8545") as eth_rpc,
                build_engine_rpc(
                    target_client, client_exception_mapper
                ) as engine_rpc,
            ):
                peer = dial_mock_peer(
                    target_client,
                    case.chain,
                    wirex_eth_versions,
                    total_timing_data,
                )
                yield TargetContext(
                    client=target_client,
                    eth_rpc=eth_rpc,
                    engine_rpc=engine_rpc,
                    mock_peer=peer,
                )
        finally:
            if peer is not None:
                peer.close()
            multi_test_client_manager.discard_client(identifier)

    return open_target_context
