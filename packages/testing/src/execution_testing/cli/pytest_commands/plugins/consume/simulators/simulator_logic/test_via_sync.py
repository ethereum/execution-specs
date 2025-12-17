"""
A hive based simulator that executes blocks against clients using the
`engine_newPayloadV*` method from the Engine API with sync testing. The
simulator uses the `BlockchainEngineSyncFixtures` to test against clients with
client synchronization.

This simulator:
1. Spins up two clients: one as the client under test and another as the sync
   client
2. Executes payloads on the client under test
3. Has the sync client synchronize from the client under test
4. Verifies that the sync was successful
"""

import pytest

from execution_testing.exceptions import UndefinedException
from execution_testing.fixtures import BlockchainEngineSyncFixture
from execution_testing.logging import get_logger
from execution_testing.rpc import (
    AdminRPC,
    BlockNotAvailableError,
    EngineRPC,
    EthRPC,
    ForkchoiceUpdateTimeoutError,
    NetRPC,
    PeerConnectionTimeoutError,
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
from ..helpers.timing import TimingData

logger = get_logger(__name__)


def test_blockchain_via_sync(
    timing_data: TimingData,
    eth_rpc: EthRPC,
    engine_rpc: EngineRPC,
    net_rpc: NetRPC,
    sync_eth_rpc: EthRPC,
    sync_engine_rpc: EngineRPC,
    sync_net_rpc: NetRPC,
    sync_admin_rpc: AdminRPC,
    client_enode_url: str,
    fixture: BlockchainEngineSyncFixture,
    strict_exception_matching: bool,
) -> None:
    """
    Test blockchain synchronization between two clients.

    1. Initialize the client under test with the genesis block
    2. Execute all payloads on the client under test
    3. Initialize the sync client with the genesis block
    4. Send sync payload and forkchoice_updated to the sync client to trigger
       synchronization
    5. Verify that the sync client successfully syncs to the same state
    """
    # Initialize client under test
    with timing_data.time("Initialize client under test"):
        logger.info("Initializing client under test with genesis block...")
        try:
            response = engine_rpc.forkchoice_updated_with_retry(
                forkchoice_state=ForkchoiceState(
                    head_block_hash=fixture.genesis.block_hash,
                ),
                forkchoice_version=fixture.payloads[
                    0
                ].forkchoice_updated_version,
                max_attempts=4,
                wait_fixed=0.5,
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

    # Verify genesis block on client under test
    with timing_data.time("Verify genesis on client under test"):
        logger.info("Verifying genesis block on client under test...")
        genesis_block = eth_rpc.get_block_by_number(0)
        assert genesis_block is not None, "genesis_block is None"
        if genesis_block["hash"] != str(fixture.genesis.block_hash):
            expected = fixture.genesis.block_hash
            got = genesis_block["hash"]
            logger.fail(
                f"Genesis block hash mismatch. Expected: {expected}, Got: {got}"
            )
            raise GenesisBlockMismatchExceptionError(
                expected_header=fixture.genesis,
                got_genesis_block=genesis_block,
            )

    # Execute all payloads on client under test
    last_valid_block_hash = fixture.genesis.block_hash
    with timing_data.time(
        "Execute payloads on client under test"
    ) as total_payload_timing:
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
                    logger.info(
                        f"Sending engine_newPayloadV{payload.new_payload_version}..."
                    )
                    # Note: This is similar to the logic in test_via_engine.py
                    try:
                        payload_response = engine_rpc.new_payload(
                            *payload.params,
                            version=payload.new_payload_version,
                        )
                        logger.info(
                            f"Payload response status: {payload_response.status}"
                        )
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
                                f"Client failed to raise expected Engine API error code: "
                                f"{payload.error_code}"
                            )
                        elif (
                            payload_response.status
                            == PayloadStatusEnum.INVALID
                        ):
                            if payload_response.validation_error is None:
                                raise LoggedError(
                                    "Client returned INVALID but no validation error was provided."
                                )
                            if isinstance(
                                payload_response.validation_error,
                                UndefinedException,
                            ):
                                message = (
                                    "Undefined exception message: "
                                    f'expected exception: "{payload.validation_error}", '
                                    f'returned exception: "{payload_response.validation_error}" '
                                    f'(mapper: "{payload_response.validation_error.mapper_name}")'
                                )
                                if strict_exception_matching:
                                    raise LoggedError(message)
                                else:
                                    logger.warning(message)
                            else:
                                if (
                                    payload.validation_error
                                    not in payload_response.validation_error
                                ):
                                    message = (
                                        "Client returned unexpected validation error: "
                                        f'got: "{payload_response.validation_error}" '
                                        f'expected: "{payload.validation_error}"'
                                    )
                                    if strict_exception_matching:
                                        raise LoggedError(message)
                                    else:
                                        logger.warning(message)

                    except JSONRPCError as e:
                        logger.info(
                            f"JSONRPC error encountered: {e.code} - {e.message}"
                        )
                        if payload.error_code is None:
                            raise LoggedError(
                                f"Unexpected error: {e.code} - {e.message}"
                            ) from e
                        if e.code != payload.error_code:
                            raise LoggedError(
                                f"Unexpected error code: {e.code}, expected: {payload.error_code}"
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
                            forkchoice_state=ForkchoiceState(
                                head_block_hash=payload.params[0].block_hash,
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
                            raise LoggedError(
                                f"unexpected status: want {PayloadStatusEnum.VALID},"
                                f" got {forkchoice_response.payload_status.status}"
                            )
                        last_valid_block_hash = payload.params[0].block_hash

        logger.info(
            "All payloads processed successfully on client under test."
        )

    # sync_payload creates the final block that the sync client will sync to
    if not fixture.sync_payload:
        pytest.fail(
            "Sync tests require a syncPayload that is not present in this test."
        )

    with timing_data.time("Send sync payload to client under test"):
        logger.info(
            "Sending sync payload (empty block) to client under test..."
        )
        try:
            sync_response = engine_rpc.new_payload(
                *fixture.sync_payload.params,
                version=fixture.sync_payload.new_payload_version,
            )
            logger.info(
                f"Client sync payload response status: {sync_response.status}"
            )

            if sync_response.status == PayloadStatusEnum.VALID:
                # Update forkchoice on client under test to include sync block
                forkchoice_response = engine_rpc.forkchoice_updated(
                    forkchoice_state=ForkchoiceState(
                        head_block_hash=fixture.sync_payload.params[
                            0
                        ].block_hash,
                    ),
                    payload_attributes=None,
                    version=fixture.sync_payload.forkchoice_updated_version,
                )
                status = forkchoice_response.payload_status.status
                logger.info(
                    f"Client forkchoice update to sync block: {status}"
                )
                last_valid_block_hash = fixture.sync_payload.params[
                    0
                ].block_hash
            else:
                logger.error(
                    f"Sync payload was not valid: {sync_response.status}"
                )
                raise LoggedError(
                    f"Sync payload validation failed: {sync_response.status}"
                )
        except JSONRPCError as e:
            logger.error(
                f"Error sending sync payload to client under test: {e.code} - {e.message}"
            )
            raise

    # Initialize sync client
    with timing_data.time("Initialize sync client"):
        logger.info("Initializing sync client with genesis block...")
        try:
            response = sync_engine_rpc.forkchoice_updated_with_retry(
                forkchoice_state=ForkchoiceState(
                    head_block_hash=fixture.genesis.block_hash,
                ),
                forkchoice_version=fixture.payloads[
                    0
                ].forkchoice_updated_version,
                max_attempts=4,
                wait_fixed=0.5,
            )
            if response.payload_status.status != PayloadStatusEnum.VALID:
                raise LoggedError(
                    f"Unexpected status on sync client forkchoice updated to genesis: "
                    f"{response.payload_status.status}"
                )
        except ForkchoiceUpdateTimeoutError as e:
            raise LoggedError(
                f"Timed out waiting for sync client forkchoice update to genesis: {e}"
            ) from None

    # Add peer using admin_addPeer This seems to be required... TODO: we can
    # maybe improve flow here if not required
    logger.info(f"Adding peer: {client_enode_url}")
    assert sync_admin_rpc is not None, "sync_admin_rpc is required"
    try:
        add_result = sync_admin_rpc.add_peer(client_enode_url)
        logger.info(f"admin_addPeer result: {add_result}")
    except Exception as e:
        raise LoggedError(f"admin_addPeer failed: {e}") from e

    # Wait for peer connection to establish
    try:
        sync_net_rpc.wait_for_peer_connection()
        logger.info("Peer connection established on sync client")
    except PeerConnectionTimeoutError:
        try:
            net_rpc.wait_for_peer_connection()
            logger.info("Peer connection established on client under test")
        except PeerConnectionTimeoutError as e:
            raise LoggedError(
                f"No P2P connection established between clients: {e}"
            ) from e

    # Trigger sync by sending the target block via newPayload followed by
    # forkchoice update
    logger.info(f"Triggering sync to block {last_valid_block_hash}")

    # Find the last valid payload to send to sync client
    last_valid_payload = None
    if (
        fixture.sync_payload
        and last_valid_block_hash == fixture.sync_payload.params[0].block_hash
    ):
        last_valid_payload = fixture.sync_payload
    else:
        # Find the payload that matches last_valid_block_hash
        for payload in fixture.payloads:
            if (
                payload.params[0].block_hash == last_valid_block_hash
                and payload.valid()
            ):
                last_valid_payload = payload
                break

    if last_valid_payload:
        last_valid_block_forkchoice_state = ForkchoiceState(
            head_block_hash=last_valid_block_hash,
            safe_block_hash=last_valid_block_hash,
            finalized_block_hash=fixture.genesis.block_hash,
        )

        try:
            # log version used for debugging
            version = last_valid_payload.new_payload_version
            logger.info(
                f"Sending target payload via engine_newPayloadV{version}"
            )

            # send the payload to sync client
            assert sync_engine_rpc is not None, "sync_engine_rpc is required"
            sync_payload_response = sync_engine_rpc.new_payload(
                *last_valid_payload.params,
                version=last_valid_payload.new_payload_version,
            )
            logger.info(
                f"Sync client newPayload response: {sync_payload_response.status}"
            )

            # send forkchoice update pointing to latest block
            logger.info(
                "Sending forkchoice update with last valid block to trigger sync..."
            )
            sync_forkchoice_response = sync_engine_rpc.forkchoice_updated(
                forkchoice_state=last_valid_block_forkchoice_state,
                payload_attributes=None,
                version=last_valid_payload.forkchoice_updated_version,
            )
            status = sync_forkchoice_response.payload_status.status
            logger.info(f"Sync trigger forkchoice response: {status}")

            if (
                sync_forkchoice_response.payload_status.status
                == PayloadStatusEnum.SYNCING
            ):
                logger.info("Sync client is now syncing!")
            elif (
                sync_forkchoice_response.payload_status.status
                == PayloadStatusEnum.ACCEPTED
            ):
                logger.info(
                    "Sync client accepted the block, may start syncing ancestors"
                )

            # Wait for P2P connections after sync starts
            # Note: Reth does not report peer count but still syncs successfully
            try:
                assert sync_net_rpc is not None, "sync_net_rpc is required"
                sync_net_rpc.wait_for_peer_connection()
                logger.debug(
                    "Peer connection verified on sync client after sync trigger"
                )
            except PeerConnectionTimeoutError:
                try:
                    net_rpc.wait_for_peer_connection()
                    logger.debug(
                        "Peer connection verified on client under test"
                    )
                except PeerConnectionTimeoutError as e:
                    logger.debug(
                        f"Peer connection not verified (may still sync): {e}"
                    )

        except Exception as e:
            logger.warning(
                f"Failed to trigger sync with newPayload/forkchoice update: {e}"
            )
    else:
        logger.warning(
            f"Could not find payload for block {last_valid_block_hash} to send to sync client"
        )

    # Wait for synchronization with continuous forkchoice updates
    with timing_data.time("Wait for synchronization"):
        # Get the target block number for logging
        target_block = eth_rpc.get_block_by_hash(last_valid_block_hash)
        target_block_number = (
            int(target_block["number"], 16) if target_block else "unknown"
        )
        logger.info(
            f"Waiting for sync client to reach block #{target_block_number} "
            f"(hash: {last_valid_block_hash})"
        )

        try:
            response = sync_engine_rpc.forkchoice_updated_with_retry(
                forkchoice_state=last_valid_block_forkchoice_state,
                forkchoice_version=fixture.sync_payload.forkchoice_updated_version
                if fixture.sync_payload
                else fixture.payloads[-1].forkchoice_updated_version,
                max_attempts=30,
                wait_fixed=0.5,
            )
            if response.payload_status.status != PayloadStatusEnum.VALID:
                raise LoggedError(
                    f"Sync client failed to sync to block {last_valid_block_hash}: "
                    f"unexpected status {response.payload_status.status}"
                )
        except ForkchoiceUpdateTimeoutError as e:
            raise LoggedError(
                f"Sync client timed out syncing to block {last_valid_block_hash}: {e}"
            ) from None

        logger.info("Sync verification successful! FCU returned VALID.")

        # Verify the final state by fetching blocks from both clients
        # Note: Block unavailability is acceptable - FCU VALID is authoritative
        client_block = None
        sync_block = None

        try:
            client_block = eth_rpc.get_block_by_hash_with_retry(
                last_valid_block_hash,
                max_attempts=5,
                wait_fixed=1.0,
            )
        except BlockNotAvailableError as e:
            logger.debug(
                f"Block not available on client under test (acceptable): {e}"
            )

        try:
            sync_block = sync_eth_rpc.get_block_by_hash_with_retry(
                last_valid_block_hash,
                max_attempts=5,
                wait_fixed=1.0,
            )
        except BlockNotAvailableError as e:
            logger.debug(
                f"Block not available on sync client (acceptable): {e}"
            )

        if sync_block is not None and client_block is not None:
            if sync_block["stateRoot"] != client_block["stateRoot"]:
                raise LoggedError(
                    f"State root mismatch after sync. "
                    f"Sync client: {sync_block['stateRoot']}, "
                    f"Client under test: {client_block['stateRoot']}"
                )

            # Verify against expected post-state hash if provided
            if fixture.post_state_hash:
                if sync_block["stateRoot"] != str(fixture.post_state_hash):
                    raise LoggedError(
                        f"Final state root mismatch. "
                        f"Expected: {fixture.post_state_hash}, "
                        f"Got: {sync_block['stateRoot']}"
                    )

            logger.info(
                f"Block state verified via eth_getBlockByHash: "
                f"{sync_block['stateRoot']}"
            )

    logger.info("Sync test completed successfully!")
