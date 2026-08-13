"""
A hive based simulator that executes blocks against clients using the
`engine_newPayloadVX` method from the Engine API.

The unified test function in this module supports both:
- `BlockchainEngineFixtures`, the original engine mode with a
  1-to-1 relationship between client instance and test, i.e.,
  each test is executed against a fresh client instance.
- `BlockchainEngineXFixtures`, enginex mode with client reuse
  across tests with shared pre-alloc groups.

Each `engine_newPayloadVX` is verified against the appropriate VALID/INVALID
responses.
"""

from typing import Union

from hive.client import Client

from execution_testing.base_types import Hash
from execution_testing.fixtures import (
    BlockchainEngineFixture,
    BlockchainEngineXFixture,
)
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.logging import get_logger
from execution_testing.rpc import (
    EngineRPC,
    EthRPC,
    ForkchoiceUpdateTimeoutError,
)
from execution_testing.rpc.rpc_types import (
    ForkchoiceState,
    JSONRPCError,
    PayloadStatusEnum,
)

from ..helpers.exceptions import (
    GenesisBlockMismatchExceptionError,
    LoggedError,
)
from ..helpers.rejected_blocks import (
    BlockRejectionTracker,
    verify_block_rejection,
)
from ..helpers.rpc_expectations import verify_rpc_expectations
from ..helpers.timing import TimingData

logger = get_logger(__name__)


def forkchoice_state(
    fixture: Union[BlockchainEngineFixture, BlockchainEngineXFixture],
    head_block_hash: Hash,
    final: bool,
) -> ForkchoiceState:
    """
    Return the forkchoice state to send after importing one payload.

    Every update names the head. The final one also names the safe and
    finalized blocks when the fixture declares them, because those two are
    not derivable from the chain — the consensus layer tells the client
    what they are, and here the fixture speaks for the consensus layer.
    Without the declaration both stay zero, which is what every other test
    wants: a test that reorgs must not have pinned a finalized block.

    The declared head is checked against the payload's rather than trusted,
    since a mismatch would mean the fixture's tags describe a different
    chain from the one just imported.
    """
    declared = fixture.rpc_forkchoice
    if declared is None or not final:
        return ForkchoiceState(head_block_hash=head_block_hash)
    if declared.head_block_hash != head_block_hash:
        raise LoggedError(
            f"fixture declares head {declared.head_block_hash} but the "
            f"last valid payload is {head_block_hash}"
        )
    return ForkchoiceState(
        head_block_hash=head_block_hash,
        safe_block_hash=declared.safe_block_hash,
        finalized_block_hash=declared.finalized_block_hash,
    )


def test_blockchain_via_engine(
    timing_data: TimingData,
    eth_rpc: EthRPC,
    engine_rpc: EngineRPC,
    client: Client,
    genesis_verified_clients: set[str],
    block_rejection_tracker: BlockRejectionTracker,
    fixture: Union[BlockchainEngineFixture, BlockchainEngineXFixture],
    strict_exception_matching: bool,
    genesis_header: FixtureHeader,
) -> None:
    """
    Execute blockchain test fixtures against a client using the Engine API.

    This function supports both engine mode (`BlockchainEngineFixture`)
    with per-test clients and enginex mode (`BlockchainEngineXFixture`)
    with client reuse across tests sharing a pre-alloc group.

    Both modes follow the same test sequence for equivalence:

    1. Send initial FCU to genesis to establish the chain head.
    2. Verify the client genesis block hash matches genesis_header. Genesis
       is immutable per client, so in shared-client (enginex) mode this is
       done once per client and skipped for later tests in the group.
    3. Execute test fixture blocks using engine_newPayloadVX.
    4. For valid payloads, send FCU to advance the chain head.

    The last of those forkchoice updates also carries the safe and
    finalized hashes when the fixture declares them, which is what makes
    the `safe` and `finalized` block tags answerable afterwards. Only the
    last one does: the blocks a tag names have to already be in the
    client, and an earlier update would be overwritten by the next
    head-only one anyway.

    A client's bad-block cache persists across the tests of a pre-alloc
    group in enginex mode: a block that an earlier test already got
    rejected may be rejected again with a generic cache error (e.g. reth's
    "links to previously rejected block") instead of being re-validated.
    When the returned error does not match the expected exception, it is
    therefore verified against the error from the client's first rejection
    of the same block before failing the test.
    """
    with timing_data.time("Initial forkchoice update"):
        logger.info("Sending initial forkchoice update to genesis block...")
        try:
            response = engine_rpc.forkchoice_updated_with_retry(
                forkchoice_state=ForkchoiceState(
                    head_block_hash=genesis_header.block_hash,
                ),
                forkchoice_version=fixture.payloads[
                    0
                ].forkchoice_updated_version,
                max_attempts=30,
                wait_fixed=1.0,
            )
            if response.payload_status.status != PayloadStatusEnum.VALID:
                raise LoggedError(
                    f"Unexpected status on forkchoice updated to genesis: "
                    f"{response.payload_status.status}"
                )
        except ForkchoiceUpdateTimeoutError as e:
            raise LoggedError(
                f"Timed out waiting for forkchoice update to genesis: {e}"
            ) from None

    if client.id not in genesis_verified_clients:
        with timing_data.time("Get genesis block"):
            logger.info("Calling getBlockByNumber to get genesis block...")
            genesis_block = eth_rpc.get_block_by_number(0)
            assert genesis_block is not None, "genesis_block is None"
            if genesis_block["hash"] != str(genesis_header.block_hash):
                expected = genesis_header.block_hash
                got = genesis_block["hash"]
                logger.fail(
                    f"Genesis block hash mismatch. "
                    f"Expected: {expected}, Got: {got}"
                )
                raise GenesisBlockMismatchExceptionError(
                    expected_header=genesis_header,
                    got_genesis_block=genesis_block,
                )
        # Genesis is immutable per client, so verify it once per client. In
        # shared-client (enginex) mode the same client serves every test in a
        # pre-alloc group, so later tests skip the redundant getBlockByNumber
        # round-trip; per-test clients get a fresh id each test and re-verify.
        genesis_verified_clients.add(client.id)

    last_valid_payload = max(
        (
            index
            for index, payload in enumerate(fixture.payloads)
            if payload.valid()
        ),
        default=-1,
    )
    with timing_data.time("Payloads execution") as total_payload_timing:
        logger.info(
            f"Starting execution of {len(fixture.payloads)} payloads..."
        )
        for i, payload in enumerate(fixture.payloads):
            logger.info(
                f"Processing payload {i + 1}/{len(fixture.payloads)}..."
            )
            with total_payload_timing.time(
                f"Payload {i + 1}"
            ) as payload_timing:
                with payload_timing.time(
                    f"engine_newPayloadV{payload.new_payload_version}"
                ):
                    version = payload.new_payload_version
                    logger.info(f"Sending engine_newPayloadV{version}...")
                    try:
                        payload_response = engine_rpc.new_payload(
                            *payload.params,
                            version=payload.new_payload_version,
                        )
                        status = payload_response.status
                        logger.info(f"Payload response status: {status}")
                        expected_validity = (
                            PayloadStatusEnum.VALID
                            if payload.valid()
                            else PayloadStatusEnum.INVALID
                        )
                        if payload_response.status != expected_validity:
                            raise LoggedError(
                                f"unexpected status: want {expected_validity},"
                                f" got {payload_response.status}"
                            )
                        if payload.error_code is not None:
                            raise LoggedError(
                                "Client failed to raise expected Engine API "
                                f"error code: {payload.error_code}"
                            )
                        elif (
                            payload_response.status
                            == PayloadStatusEnum.INVALID
                        ):
                            if payload_response.validation_error is None:
                                raise LoggedError(
                                    "Client returned INVALID but no "
                                    "validation error was provided."
                                )
                            block_hash = payload.params[0].block_hash
                            first_rejection = block_rejection_tracker.track(
                                client.id,
                                block_hash,
                                payload_response.validation_error,
                            )
                            verify_block_rejection(
                                payload.validation_error,
                                payload_response.validation_error,
                                first_rejection,
                                block_hash,
                                strict_exception_matching,
                            )

                    except JSONRPCError as e:
                        logger.info(
                            f"JSONRPC error encountered: "
                            f"{e.code} - {e.message}"
                        )
                        if payload.error_code is None:
                            raise LoggedError(
                                f"Unexpected error: {e.code} - {e.message}"
                            ) from e
                        if e.code != payload.error_code:
                            raise LoggedError(
                                f"Unexpected error code: {e.code}, "
                                f"expected: {payload.error_code}"
                            ) from e

                if payload.valid():
                    with payload_timing.time(
                        f"engine_forkchoiceUpdatedV{payload.forkchoice_updated_version}"
                    ):
                        # Send a forkchoice update to the engine
                        version = payload.forkchoice_updated_version
                        logger.info(
                            f"Sending engine_forkchoiceUpdatedV{version}..."
                        )
                        forkchoice_response = engine_rpc.forkchoice_updated(
                            forkchoice_state=forkchoice_state(
                                fixture,
                                payload.params[0].block_hash,
                                final=i == last_valid_payload,
                            ),
                            payload_attributes=None,
                            version=payload.forkchoice_updated_version,
                        )
                        status = forkchoice_response.payload_status.status
                        logger.info(f"Forkchoice update response: {status}")
                        if (
                            forkchoice_response.payload_status.status
                            != PayloadStatusEnum.VALID
                        ):
                            status = forkchoice_response.payload_status.status
                            raise LoggedError(
                                f"unexpected status: want "
                                f"{PayloadStatusEnum.VALID}, got {status}"
                            )
        logger.info("All payloads processed successfully.")
    with timing_data.time("Verify RPC expectations"):
        verify_rpc_expectations(eth_rpc, fixture)
