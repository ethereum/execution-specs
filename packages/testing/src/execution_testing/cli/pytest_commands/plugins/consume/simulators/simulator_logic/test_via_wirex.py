"""
A hive based simulator that makes clients full sync fixture blocks.

Where `consume rlp` hands a client its blocks through a client specific
offline import mode, and `consume engine` hands them over one
`engine_newPayload` call at a time, this simulator makes the client
fetch them itself, from a mock peer speaking the production devp2p
protocols.

The control plane and the data plane are deliberately separate:

- The control plane is the Engine API. A post-merge client does not
  choose its own head, so it is told which block to sync to. That takes
  one `engine_newPayload` for the head block, which gives the client the
  header, and one `engine_forkchoiceUpdated` naming that head.
- The data plane is devp2p. Every block before the head is downloaded
  from the mock peer over RLPx and executed by the client's full sync
  path.

Because only the blocks before the announced head are guaranteed to
travel over devp2p - whether a client also re-fetches the head's body
from a peer is an implementation choice, and measured clients go both
ways - the filler gives every eligible engine_x chain one extra empty
block, placed by the chain's own structure. A fully valid chain gets
it *appended*, out-of-chain in the fixture's `syncPayload` field: this
simulator announces that trailer instead of the test's own head, which
makes every one of the test's blocks an ancestor whose header and body
a full-syncing client must fetch from the peer, on every client, by
chain structure rather than client courtesy. A single expected-invalid
block gets the extra block *prepended* in-chain instead (tagged with
the `sync` phase), giving the sync a reason to start below the block
the client is expected to refuse. Chains still too short to put any
block on the wire - single-block fixtures the extra block cannot
survive - are skipped here, where the limitation actually lives.
"""

import time

import pytest
from hive.client import Client

from execution_testing.devp2p.chain import Block, Chain
from execution_testing.devp2p.peer import MockPeer
from execution_testing.fixtures import BlockchainEngineXFixture
from execution_testing.fixtures.blockchain import (
    FixtureEngineNewPayload,
    FixtureHeader,
)
from execution_testing.logging import get_logger
from execution_testing.rpc import (
    EngineRPC,
    EthRPC,
    ForkchoiceUpdateTimeoutError,
)
from execution_testing.rpc.rpc_types import ForkchoiceState, PayloadStatusEnum

from ..helpers.exceptions import (
    GenesisBlockMismatchExceptionError,
    LoggedError,
)
from ..helpers.timing import TimingData

logger = get_logger(__name__)


def announced_payload(
    fixture: BlockchainEngineXFixture,
) -> FixtureEngineNewPayload:
    """
    Return the payload this simulator announces as the sync target.

    The appended sync payload when the fixture carries one - the
    trailer exists precisely to be announced, so that every payload of
    the test's own chain is an ancestor the client must fetch from the
    peer - and the chain's own head otherwise (prepend-class fixtures
    must announce the test's block: their assertion is the client's
    judgement of it).
    """
    return fixture.sync_payload or fixture.payloads[-1]


def required_wire_bodies(chain: Chain) -> list[Block]:
    """
    Return the blocks whose bodies must have traveled the wire.

    Every block below the announced head, except those whose body a
    client may derive from the header alone (empty transactions trie,
    empty withdrawals root). The head itself is exempt by protocol:
    its payload arrives through the Engine API, and whether a client
    also re-fetches its body from a peer is an implementation choice
    that measured clients answer both ways.
    """
    return [
        block
        for block in chain.blocks[:-1]
        if block.transactions or block.withdrawals
    ]


def test_blockchain_via_wirex(
    timing_data: TimingData,
    eth_rpc: EthRPC,
    engine_rpc: EngineRPC,
    client: Client,
    genesis_verified_clients: set[str],
    fixture: BlockchainEngineXFixture,
    genesis_header: FixtureHeader,
    chain: Chain,
    mock_peer: MockPeer,
    wirex_sync_timeout: float,
    wirex_poll_interval: float,
    wirex_announce_interval: float,
) -> None:
    """
    Make a client full sync one test's chain from the mock peer.

    The sequence is:

    1. Verify the client's genesis matches the group's, once per client.
    2. Deliver the announced head over the Engine API so the client
       knows which chain to sync to, and name it in a forkchoice
       update. For an appended-class fixture that head is the sync
       trailer riding above the test's own chain, so every block the
       test author wrote is an ancestor the client must fetch from the
       peer.
    3. Wait for the client to download and execute the ancestors from the
       mock peer, polling the same forkchoice update until it is VALID.
    4. Check the client's head really is the expected block.

    There is deliberately no rewind between tests. Every test's chain
    forks at genesis, so announcing the new head is all a consensus
    client would do, and a backwards forkchoice update is actively
    harmful to clients that act on it: nethermind moves its head back
    to genesis while its persisted state stays at the previous chain's
    tip, which lands it in a crash-recovery edge case where it fetches
    receipts instead of executing blocks (`BlockDownloader.
    ReceiptEdgeCase`); geth ignores the rewind entirely.
    """
    if any(not payload.valid() for payload in fixture.payloads):
        pytest.skip(
            "fixtures with invalid payloads cannot be served as a canonical "
            "chain: a full syncing client rejects the whole chain rather "
            "than reporting a per-block verdict"
        )

    head_payload = announced_payload(fixture)
    head_hash = head_payload.params[0].block_hash

    if client.id not in genesis_verified_clients:
        with timing_data.time("Verify genesis"):
            genesis_block = eth_rpc.get_block_by_number(0)
            if genesis_block is None:
                raise LoggedError("Client returned no genesis block")
            if genesis_block["hash"] != str(genesis_header.block_hash):
                raise GenesisBlockMismatchExceptionError(
                    expected_header=genesis_header,
                    got_genesis_block=genesis_block,
                )
            genesis_verified_clients.add(client.id)

    expected_head = "0x" + chain.head.block_hash.hex()

    head_state = ForkchoiceState(
        head_block_hash=head_hash,
        safe_block_hash=genesis_header.block_hash,
        finalized_block_hash=genesis_header.block_hash,
    )

    def announce() -> None:
        """Tell the client which block to sync to."""
        engine_rpc.new_payload(
            *head_payload.params, version=head_payload.new_payload_version
        )
        engine_rpc.forkchoice_updated(
            forkchoice_state=head_state,
            payload_attributes=None,
            version=head_payload.forkchoice_updated_version,
        )

    with timing_data.time("Announce sync target"):
        logger.info(
            f"Announcing head block {chain.head.number} to trigger a sync "
            f"of {len(chain.blocks) - 1} ancestor block(s) over devp2p"
        )
        announce()

    with timing_data.time("Sync from peer"):
        # Wait by watching for the block rather than by repeating the
        # forkchoice update. A repeated update restarts the client's sync
        # cycle, and repeating it faster than a cycle takes prevents the
        # sync from ever finishing. The announcement is repeated on a much
        # slower cadence, as a consensus client would each slot, because a
        # client whose sync state was still settling may have ignored the
        # first one.
        deadline = time.monotonic() + wirex_sync_timeout
        next_announcement = time.monotonic() + wirex_announce_interval
        synced = False
        while time.monotonic() < deadline:
            if eth_rpc.get_block_by_hash(head_hash, full_txs=False):
                synced = True
                break
            if time.monotonic() >= next_announcement:
                logger.info("Re-announcing the sync target")
                announce()
                next_announcement = time.monotonic() + wirex_announce_interval
            time.sleep(wirex_poll_interval)
        if not synced:
            raise LoggedError(
                f"Client never imported the fixture head {expected_head} "
                f"within {wirex_sync_timeout}s. Peer transcript: "
                f"{mock_peer.statistics.transcript}"
            )

    with timing_data.time("Confirm head"):
        try:
            response = engine_rpc.forkchoice_updated_with_retry(
                forkchoice_state=head_state,
                forkchoice_version=head_payload.forkchoice_updated_version,
                max_attempts=10,
                wait_fixed=0.5,
            )
        except ForkchoiceUpdateTimeoutError as error:
            raise LoggedError(
                f"Client imported {expected_head} but never made it "
                f"canonical: {error}"
            ) from None
        if response.payload_status.status != PayloadStatusEnum.VALID:
            raise LoggedError(
                f"Client failed to sync to {expected_head}: "
                f"{response.payload_status.status}. Peer transcript: "
                f"{mock_peer.statistics.transcript}"
            )

    with timing_data.time("Verify head"):
        head_block = eth_rpc.get_block_by_number("latest")
        if head_block is None:
            raise LoggedError("Client returned no head block")
        if head_block["hash"] != expected_head:
            raise LoggedError(
                f"Client head is {head_block['hash']}, expected "
                f"{expected_head}"
            )

    statistics = mock_peer.statistics
    logger.info(
        f"Synced to block {chain.head.number}: peer served "
        f"{statistics.headers_served} header(s) in "
        f"{statistics.header_requests} request(s) and "
        f"{statistics.bodies_served} body/bodies in "
        f"{statistics.body_requests} request(s)"
    )
    # Every non-derivable body below the announced head must have
    # traveled the wire, block by block: an aggregate count would let
    # one downloaded body vouch for a chain whose other bodies arrived
    # some other way. The evidence is cumulative per client, not per
    # test: valid chains carry no per-test salt, so two tests of one
    # group may declare byte-identical chains, and the reused client
    # re-syncs nothing for the second - its blocks already traveled
    # the wire during the first.
    required = required_wire_bodies(chain)
    ever_served = mock_peer.body_hashes_ever_served
    missing_bodies = [
        block.number
        for block in required
        if block.block_hash not in ever_served
    ]
    prior_served = sum(
        1
        for block in required
        if block.block_hash not in statistics.body_hashes_served
        and block.block_hash in ever_served
    )
    if prior_served:
        logger.info(
            f"{prior_served} of {len(required)} required body/bodies "
            "already traveled the wire during an earlier test of this "
            "client (byte-identical chain content); the wire-coverage "
            "evidence is cumulative per client"
        )
    if missing_bodies:
        raise LoggedError(
            "The client reached the expected head, but the non-empty "
            "body/bodies of block(s) "
            f"{', '.join(str(n) for n in missing_bodies)} never "
            "traveled this client's wire connection, so those blocks "
            "were not verified over devp2p."
        )
    if statistics.receipt_requests:
        logger.warning(
            f"Client made {statistics.receipt_requests} receipt request(s), "
            "which this peer does not serve; the client may not be "
            "executing the blocks it downloads."
        )
