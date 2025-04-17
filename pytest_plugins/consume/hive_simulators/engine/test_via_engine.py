"""
A hive based simulator that executes blocks against clients using the `engine_newPayloadVX` method
from the Engine API. The simulator uses the `BlockchainEngineFixtures` to test against clients.

Each `engine_newPayloadVX` is verified against the appropriate VALID/INVALID responses.
"""

from ethereum_test_exceptions import UndefinedException
from ethereum_test_fixtures import BlockchainEngineFixture
from ethereum_test_rpc import EngineRPC, EthRPC
from ethereum_test_rpc.types import ForkchoiceState, JSONRPCError, PayloadStatusEnum
from pytest_plugins.consume.hive_simulators.exceptions import GenesisBlockMismatchExceptionError
from pytest_plugins.logging import get_logger

from ..timing import TimingData

logger = get_logger(__name__)


class LoggedError(Exception):
    """Exception that uses the logger to log the failure."""

    def __init__(self, *args: object) -> None:
        """Initialize the exception and log the failure."""
        super().__init__(*args)
        logger.fail(str(self))


def test_blockchain_via_engine(
    timing_data: TimingData,
    eth_rpc: EthRPC,
    engine_rpc: EngineRPC,
    fixture: BlockchainEngineFixture,
    strict_exception_matching: bool,
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
        if forkchoice_response.payload_status.status != PayloadStatusEnum.VALID:
            raise LoggedError(
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
        logger.info("All payloads processed successfully.")
