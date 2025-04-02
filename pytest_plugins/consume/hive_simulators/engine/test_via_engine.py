"""
A hive based simulator that executes blocks against clients using the `engine_newPayloadVX` method
from the Engine API. The simulator uses the `BlockchainEngineFixtures` to test against clients.

Each `engine_newPayloadVX` is verified against the appropriate VALID/INVALID responses.
"""

from ethereum_test_fixtures import BlockchainEngineFixture
from ethereum_test_rpc import EngineRPC, EthRPC
from ethereum_test_rpc.types import ForkchoiceState, JSONRPCError, PayloadStatusEnum
from pytest_plugins.consume.hive_simulators.exceptions import GenesisBlockMismatchExceptionError
from pytest_plugins.logging import get_logger

from ..timing import TimingData

logger = get_logger(__name__)


def test_blockchain_via_engine(
    timing_data: TimingData,
    eth_rpc: EthRPC,
    engine_rpc: EngineRPC,
    fixture: BlockchainEngineFixture,
):
    """
    1. Check the client genesis block hash matches `fixture.genesis.block_hash`.
    2. Execute the test case fixture blocks against the client under test using the
    `engine_newPayloadVX` method from the Engine API.
    3. For valid payloads a forkchoice update is performed to finalize the chain.
    """
    # Send a initial forkchoice update
    with timing_data.time("Initial forkchoice update"):
        logger.info("Sending initial forkchoice update to genesis block...")
        forkchoice_response = engine_rpc.forkchoice_updated(
            forkchoice_state=ForkchoiceState(
                head_block_hash=fixture.genesis.block_hash,
            ),
            payload_attributes=None,
            version=fixture.payloads[0].forkchoice_updated_version,
        )
        status = forkchoice_response.payload_status.status
        logger.info(f"Initial forkchoice update response: {status}")
        assert forkchoice_response.payload_status.status == PayloadStatusEnum.VALID, (
            f"unexpected status on forkchoice updated to genesis: {forkchoice_response}"
        )

    with timing_data.time("Get genesis block"):
        logger.info("Calling getBlockByNumber to get genesis block...")
        genesis_block = eth_rpc.get_block_by_number(0)
        if genesis_block["hash"] != str(fixture.genesis.block_hash):
            expected = fixture.genesis.block_hash
            got = genesis_block["hash"]
            logger.fail(f"Genesis block hash mismatch. Expected: {expected}, Got: {got}")
            raise GenesisBlockMismatchExceptionError(
                expected_header=fixture.genesis,
                got_genesis_block=genesis_block,
            )

    with timing_data.time("Payloads execution") as total_payload_timing:
        logger.info(f"Starting execution of {len(fixture.payloads)} payloads...")
        for i, payload in enumerate(fixture.payloads):
            logger.info(f"Processing payload {i + 1}/{len(fixture.payloads)}...")
            with total_payload_timing.time(f"Payload {i + 1}") as payload_timing:
                with payload_timing.time(f"engine_newPayloadV{payload.new_payload_version}"):
                    logger.info(f"Sending engine_newPayloadV{payload.new_payload_version}...")
                    expected_validity = "VALID" if payload.valid() else "INVALID"
                    logger.info(f"Expected payload validity: {expected_validity}")
                    try:
                        payload_response = engine_rpc.new_payload(
                            *payload.params,
                            version=payload.new_payload_version,
                        )
                        logger.info(f"Payload response status: {payload_response.status}")
                        assert payload_response.status == (
                            PayloadStatusEnum.VALID
                            if payload.valid()
                            else PayloadStatusEnum.INVALID
                        ), f"unexpected status: {payload_response}"
                        if payload.error_code is not None:
                            error_code = payload.error_code
                            logger.fail(
                                f"Client failed to raise expected Engine API error code: "
                                f"{error_code}"
                            )
                            raise Exception(
                                "Client failed to raise expected Engine API error code: "
                                f"{payload.error_code}"
                            )
                    except JSONRPCError as e:
                        logger.info(f"JSONRPC error encountered: {e.code} - {e.message}")
                        if payload.error_code is None:
                            logger.fail(f"Unexpected error: {e.code} - {e.message}")
                            raise Exception(f"unexpected error: {e.code} - {e.message}") from e
                        if e.code != payload.error_code:
                            expected_code = payload.error_code
                            logger.fail(
                                f"Unexpected error code: {e.code}, expected: {expected_code}"
                            )
                            raise Exception(
                                f"unexpected error code: {e.code}, expected: {payload.error_code}"
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
                        assert (
                            forkchoice_response.payload_status.status == PayloadStatusEnum.VALID
                        ), f"unexpected status: {forkchoice_response}"
        logger.info("All payloads processed successfully.")
