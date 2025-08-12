"""
A hive based simulator that executes blocks against clients using the `engine_newPayloadV*` method
from the Engine API with sync testing. The simulator uses the `BlockchainEngineSyncFixtures` to
test against clients with client synchronization.

This simulator:
1. Spins up two clients: one as the client under test and another as the sync client
2. Executes payloads on the client under test
3. Has the sync client synchronize from the client under test
4. Verifies that the sync was successful
"""

import time

import pytest

from ethereum_test_base_types import Hash
from ethereum_test_exceptions import UndefinedException
from ethereum_test_fixtures import BlockchainEngineSyncFixture
from ethereum_test_rpc import AdminRPC, EngineRPC, EthRPC, NetRPC
from ethereum_test_rpc.types import (
    ForkchoiceState,
    JSONRPCError,
    PayloadStatusEnum,
)

from ....logging import get_logger
from ..helpers.exceptions import GenesisBlockMismatchExceptionError
from ..helpers.timing import TimingData

logger = get_logger(__name__)


class LoggedError(Exception):
    """Exception that uses the logger to log the failure."""

    def __init__(self, *args: object) -> None:
        """Initialize the exception and log the failure."""
        super().__init__(*args)
        logger.fail(str(self))


def wait_for_sync(
    sync_eth_rpc: EthRPC,
    sync_engine_rpc: EngineRPC,
    expected_block_hash: str | Hash,
    timeout: int = 10,
    poll_interval: float = 1.0,
) -> bool:
    """Wait for the sync client to reach the expected block hash."""
    start_time = time.time()
    last_block_number = 0
    no_progress_count = 0

    while time.time() - start_time < timeout:
        try:
            # First check if we have the expected block
            block = sync_eth_rpc.get_block_by_hash(Hash(expected_block_hash))
            if block is not None:
                logger.info(f"Sync complete! Client has block {expected_block_hash}")
                return True

            # Check current sync progress
            current_block = sync_eth_rpc.get_block_by_number("latest")
            if current_block:
                current_number = int(current_block.get("number", "0x0"), 16)
                current_hash = current_block.get("hash", "unknown")
                if current_number > last_block_number:
                    logger.info(f"Sync progress: block {current_number} (hash: {current_hash})")
                    last_block_number = current_number
                    no_progress_count = 0
                else:
                    no_progress_count += 1
                    if no_progress_count == 1:
                        logger.info(
                            f"Sync client is at block {current_number} (hash: {current_hash})"
                        )
                    elif no_progress_count % 10 == 0:
                        logger.debug(
                            f"No sync progress for {no_progress_count} polls, "
                            f"still at block {current_number}"
                        )

        except Exception as e:
            logger.debug(f"Error checking sync status: {e}")

        time.sleep(poll_interval)

    # Log final state
    try:
        final_block = sync_eth_rpc.get_block_by_number("latest")
        if final_block:
            logger.warning(
                f"Sync timeout! Final block: {final_block.get('number', 'unknown')} "
                f"(hash: {final_block.get('hash', 'unknown')})"
            )
    except Exception:
        pass

    return False


def test_blockchain_via_sync(
    timing_data: TimingData,
    eth_rpc: EthRPC,
    engine_rpc: EngineRPC,
    net_rpc: NetRPC,
    admin_rpc: AdminRPC,
    sync_eth_rpc: EthRPC,
    sync_engine_rpc: EngineRPC,
    sync_net_rpc: NetRPC,
    sync_admin_rpc: AdminRPC,
    client_enode_url: str,
    fixture: BlockchainEngineSyncFixture,
    strict_exception_matching: bool,
):
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

        # Send initial forkchoice update to client under test
        delay = 0.5
        for attempt in range(3):
            forkchoice_response = engine_rpc.forkchoice_updated(
                forkchoice_state=ForkchoiceState(
                    head_block_hash=fixture.genesis.block_hash,
                ),
                payload_attributes=None,
                version=fixture.payloads[0].forkchoice_updated_version,
            )
            status = forkchoice_response.payload_status.status
            logger.info(f"Initial forkchoice update response attempt {attempt + 1}: {status}")
            if status != PayloadStatusEnum.SYNCING:
                break
            if attempt < 2:
                time.sleep(delay)
                delay *= 2

        if forkchoice_response.payload_status.status != PayloadStatusEnum.VALID:
            logger.error(
                f"Client under test failed to initialize properly after 3 attempts, "
                f"final status: {forkchoice_response.payload_status.status}"
            )
            raise LoggedError(
                f"unexpected status on forkchoice updated to genesis: {forkchoice_response}"
            )

    # Verify genesis block on client under test
    with timing_data.time("Verify genesis on client under test"):
        logger.info("Verifying genesis block on client under test...")
        genesis_block = eth_rpc.get_block_by_number(0)
        if genesis_block["hash"] != str(fixture.genesis.block_hash):
            expected = fixture.genesis.block_hash
            got = genesis_block["hash"]
            logger.fail(f"Genesis block hash mismatch. Expected: {expected}, Got: {got}")
            raise GenesisBlockMismatchExceptionError(
                expected_header=fixture.genesis,
                got_genesis_block=genesis_block,
            )

    # Execute all payloads on client under test
    last_valid_block_hash = fixture.genesis.block_hash
    with timing_data.time("Execute payloads on client under test") as total_payload_timing:
        logger.info(f"Starting execution of {len(fixture.payloads)} payloads...")
        for i, payload in enumerate(fixture.payloads):
            logger.info(f"Processing payload {i + 1}/{len(fixture.payloads)}...")
            with total_payload_timing.time(f"Payload {i + 1}") as payload_timing:
                with payload_timing.time(f"engine_newPayloadV{payload.new_payload_version}"):
                    logger.info(f"Sending engine_newPayloadV{payload.new_payload_version}...")
                    # Note: This is similar to the logic in test_via_engine.py
                    try:
                        payload_response = engine_rpc.new_payload(
                            *payload.params,
                            version=payload.new_payload_version,
                        )
                        logger.info(f"Payload response status: {payload_response.status}")
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
                        elif payload_response.status == PayloadStatusEnum.INVALID:
                            if payload_response.validation_error is None:
                                raise LoggedError(
                                    "Client returned INVALID but no validation error was provided."
                                )
                            if isinstance(payload_response.validation_error, UndefinedException):
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
                        logger.info(f"JSONRPC error encountered: {e.code} - {e.message}")
                        if payload.error_code is None:
                            raise LoggedError(f"Unexpected error: {e.code} - {e.message}") from e
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
                        logger.info(f"Sending engine_forkchoiceUpdatedV{version}...")
                        forkchoice_response = engine_rpc.forkchoice_updated(
                            forkchoice_state=ForkchoiceState(
                                head_block_hash=payload.params[0].block_hash,
                            ),
                            payload_attributes=None,
                            version=payload.forkchoice_updated_version,
                        )
                        status = forkchoice_response.payload_status.status
                        logger.info(f"Forkchoice update response: {status}")
                        if forkchoice_response.payload_status.status != PayloadStatusEnum.VALID:
                            raise LoggedError(
                                f"unexpected status: want {PayloadStatusEnum.VALID},"
                                f" got {forkchoice_response.payload_status.status}"
                            )
                        last_valid_block_hash = payload.params[0].block_hash

        logger.info("All payloads processed successfully on client under test.")

    # sync_payload creates the final block that the sync client will sync to
    if not fixture.sync_payload:
        pytest.fail("Sync tests require a syncPayload that is not present in this test.")

    with timing_data.time("Send sync payload to client under test"):
        logger.info("Sending sync payload (empty block) to client under test...")
        try:
            sync_response = engine_rpc.new_payload(
                *fixture.sync_payload.params,
                version=fixture.sync_payload.new_payload_version,
            )
            logger.info(f"Client sync payload response status: {sync_response.status}")

            if sync_response.status == PayloadStatusEnum.VALID:
                # Update forkchoice on client under test to include sync block
                forkchoice_response = engine_rpc.forkchoice_updated(
                    forkchoice_state=ForkchoiceState(
                        head_block_hash=fixture.sync_payload.params[0].block_hash,
                    ),
                    payload_attributes=None,
                    version=fixture.sync_payload.forkchoice_updated_version,
                )
                status = forkchoice_response.payload_status.status
                logger.info(f"Client forkchoice update to sync block: {status}")
                last_valid_block_hash = fixture.sync_payload.params[0].block_hash
            else:
                logger.error(f"Sync payload was not valid: {sync_response.status}")
                raise LoggedError(f"Sync payload validation failed: {sync_response.status}")
        except JSONRPCError as e:
            logger.error(
                f"Error sending sync payload to client under test: {e.code} - {e.message}"
            )
            raise

    # Initialize sync client
    with timing_data.time("Initialize sync client"):
        logger.info("Initializing sync client with genesis block...")

        # Send initial forkchoice update to sync client
        delay = 0.5
        for attempt in range(3):
            forkchoice_response = sync_engine_rpc.forkchoice_updated(
                forkchoice_state=ForkchoiceState(
                    head_block_hash=fixture.genesis.block_hash,
                ),
                payload_attributes=None,
                version=fixture.payloads[0].forkchoice_updated_version,
            )
            status = forkchoice_response.payload_status.status
            logger.info(f"Sync client forkchoice update response attempt {attempt + 1}: {status}")
            if status != PayloadStatusEnum.SYNCING:
                break
            if attempt < 2:
                time.sleep(delay)
                delay *= 2

        if forkchoice_response.payload_status.status != PayloadStatusEnum.VALID:
            logger.error(
                f"Sync client failed to initialize properly after 3 attempts, "
                f"final status: {forkchoice_response.payload_status.status}"
            )
            raise LoggedError(
                f"Unexpected status on sync client forkchoice updated to genesis: "
                f"{forkchoice_response}"
            )

    # Add peer using admin_addPeer
    # This seems to be required... TODO: we can maybe improve flow here if not required
    logger.info(f"Adding peer: {client_enode_url}")
    assert sync_admin_rpc is not None, "sync_admin_rpc is required"
    try:
        add_result = sync_admin_rpc.add_peer(client_enode_url)
        logger.info(f"admin_addPeer result: {add_result}")
    except Exception as e:
        raise LoggedError(f"admin_addPeer failed: {e}") from e

    time.sleep(1)  # quick sleep to allow for connection - TODO: is this necessary?

    try:
        sync_peer_count = sync_net_rpc.peer_count()
        client_peer_count = net_rpc.peer_count()
        logger.info(
            f"Peer count: sync_client={sync_peer_count}, client_under_test={client_peer_count}"
        )

        if sync_peer_count == 0 and client_peer_count == 0:
            raise LoggedError("No P2P connection established between clients")
    except Exception as e:
        logger.warning(f"Could not verify peer connection: {e}")

    # Trigger sync by sending the target block via newPayload followed by forkchoice update
    logger.info(f"Triggering sync to block {last_valid_block_hash}")

    # Find the last valid payload to send to sync client
    last_valid_payload = None
    if fixture.sync_payload and last_valid_block_hash == fixture.sync_payload.params[0].block_hash:
        last_valid_payload = fixture.sync_payload
    else:
        # Find the payload that matches last_valid_block_hash
        for payload in fixture.payloads:
            if payload.params[0].block_hash == last_valid_block_hash and payload.valid():
                last_valid_payload = payload
                break

    if last_valid_payload:
        last_valid_block_forkchoice_state = ForkchoiceState(
            head_block_hash=last_valid_block_hash,
            safe_block_hash=last_valid_block_hash,
            finalized_block_hash=fixture.genesis.block_hash,
        )

        try:
            version = last_valid_payload.new_payload_version  # log version used for debugging
            logger.info(f"Sending target payload via engine_newPayloadV{version}")

            # send the payload to sync client
            assert sync_engine_rpc is not None, "sync_engine_rpc is required"
            sync_payload_response = sync_engine_rpc.new_payload(
                *last_valid_payload.params,
                version=last_valid_payload.new_payload_version,
            )
            logger.info(f"Sync client newPayload response: {sync_payload_response.status}")

            # send forkchoice update pointing to latest block
            logger.info("Sending forkchoice update with last valid block to trigger sync...")
            sync_forkchoice_response = sync_engine_rpc.forkchoice_updated(
                forkchoice_state=last_valid_block_forkchoice_state,
                payload_attributes=None,
                version=last_valid_payload.forkchoice_updated_version,
            )
            status = sync_forkchoice_response.payload_status.status
            logger.info(f"Sync trigger forkchoice response: {status}")

            if sync_forkchoice_response.payload_status.status == PayloadStatusEnum.SYNCING:
                logger.info("Sync client is now syncing!")
            elif sync_forkchoice_response.payload_status.status == PayloadStatusEnum.ACCEPTED:
                logger.info("Sync client accepted the block, may start syncing ancestors")

            # Give a moment for P2P connections to establish after sync starts
            time.sleep(1)

            # Check peer count after triggering sync
            # Note: Reth does not actually raise the peer count but doesn't seem
            # to need this to sync.
            try:
                assert sync_net_rpc is not None, "sync_net_rpc is required"
                client_peer_count = net_rpc.peer_count()
                sync_peer_count = sync_net_rpc.peer_count()
                if sync_peer_count > 0 or client_peer_count > 0:
                    logger.debug(
                        f"Peers connected: client_under_test={client_peer_count}, "
                        f"sync_client={sync_peer_count}"
                    )
            except Exception as e:
                logger.debug(f"Could not check peer count: {e}")

        except Exception as e:
            logger.warning(f"Failed to trigger sync with newPayload/forkchoice update: {e}")
    else:
        logger.warning(
            f"Could not find payload for block {last_valid_block_hash} to send to sync client"
        )

    # Wait for synchronization with continuous forkchoice updates
    with timing_data.time("Wait for synchronization"):
        # Get the target block number for logging
        target_block = eth_rpc.get_block_by_hash(last_valid_block_hash)
        target_block_number = int(target_block["number"], 16) if target_block else "unknown"
        logger.info(
            f"Waiting for sync client to reach block #{target_block_number} "
            f"(hash: {last_valid_block_hash})"
        )

        # Start monitoring sync progress
        sync_start_time = time.time()
        last_forkchoice_time = time.time()
        forkchoice_interval = 2.0  # Send forkchoice updates every 2 seconds

        while time.time() - sync_start_time < 10:  # 10 second timeout
            # Send periodic forkchoice updates to keep sync alive
            if time.time() - last_forkchoice_time >= forkchoice_interval:
                try:
                    # Send forkchoice update to sync client to trigger/maintain sync
                    assert sync_engine_rpc is not None, "sync_engine_rpc is required"
                    sync_fc_response = sync_engine_rpc.forkchoice_updated(
                        forkchoice_state=last_valid_block_forkchoice_state,
                        payload_attributes=None,
                        version=fixture.sync_payload.forkchoice_updated_version
                        if fixture.sync_payload
                        else fixture.payloads[-1].forkchoice_updated_version,
                    )
                    status = sync_fc_response.payload_status.status
                    logger.debug(f"Periodic forkchoice update status: {status}")
                    if status.VALID:
                        break
                    last_forkchoice_time = time.time()
                except Exception as fc_err:
                    logger.debug(f"Periodic forkchoice update failed: {fc_err}")
            time.sleep(0.5)
        else:
            raise LoggedError(
                f"Sync client failed to synchronize to block {last_valid_block_hash} "
                f"within timeout"
            )

        # Final verification
        assert sync_eth_rpc is not None, "sync_eth_rpc is required"
        assert sync_engine_rpc is not None, "sync_engine_rpc is required"
        if wait_for_sync(sync_eth_rpc, sync_engine_rpc, last_valid_block_hash, timeout=5):
            logger.info("Sync verification successful!")

            # Verify the final state
            sync_block = sync_eth_rpc.get_block_by_hash(last_valid_block_hash)
            client_block = eth_rpc.get_block_by_hash(last_valid_block_hash)

            if sync_block["stateRoot"] != client_block["stateRoot"]:
                raise LoggedError(
                    f"State root mismatch after sync. "
                    f"Sync client: {sync_block['stateRoot']}, "
                    f"Client under test: {client_block['stateRoot']}"
                )

            # Verify post state if available
            if fixture.post_state_hash:
                if sync_block["stateRoot"] != str(fixture.post_state_hash):
                    raise LoggedError(
                        f"Final state root mismatch. "
                        f"Expected: {fixture.post_state_hash}, "
                        f"Got: {sync_block['stateRoot']}"
                    )
        else:
            raise LoggedError(
                f"Sync client failed to synchronize to block {last_valid_block_hash} "
                f"within timeout"
            )

    logger.info("Sync test completed successfully!")
