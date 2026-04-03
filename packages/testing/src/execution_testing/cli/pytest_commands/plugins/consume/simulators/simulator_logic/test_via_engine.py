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

from execution_testing.exceptions import UndefinedException
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
from ..helpers.timing import TimingData

logger = get_logger(__name__)


def test_blockchain_via_engine(
    timing_data: TimingData,
    eth_rpc: EthRPC,
    engine_rpc: EngineRPC,
    fixture: Union[BlockchainEngineFixture, BlockchainEngineXFixture],
    strict_exception_matching: bool,
    genesis_header: FixtureHeader,
) -> None:
    """
    Execute blockchain test fixtures against a client using the Engine API.

    This function supports two modes:

    1. **Engine Mode** (`BlockchainEngineFixture`):
       - Uses per-test clients (started fresh for each test).
       - Always performs initial FCU to genesis.
       - Always performs FCU after valid payloads.
       - genesis_header comes from fixture.genesis (via fixture).
       - needs_genesis_init is always True (via fixture).

    2. **EngineX Mode** (`BlockchainEngineXFixture`):
       - Reuses clients across tests with same pre-alloc group.
       - Skips initial FCU for reused clients.
       - Skips FCU after valid payloads to keep client at genesis.
       - genesis_header comes from separate pre_alloc_group fixture.
       - needs_genesis_init is False for reused clients.

    Steps:
    1. Check the client genesis block hash matches genesis_header.block_hash
    2. Execute test fixture blocks using engine_newPayloadVX
    3. For valid payloads, perform forkchoice update to finalize chain
       (unless client is being reused, in which case skip FCU)
    """
    if isinstance(fixture, BlockchainEngineFixture):
        with timing_data.time("Initial forkchoice update"):
            logger.info(
                "Sending initial forkchoice update to genesis block..."
            )
            try:
                response = engine_rpc.forkchoice_updated_with_retry(
                    forkchoice_state=ForkchoiceState(
                        head_block_hash=fixture.genesis.block_hash,
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
                            if isinstance(
                                payload_response.validation_error,
                                UndefinedException,
                            ):
                                message = (
                                    "Undefined exception message: "
                                    f"expected exception: "
                                    f'"{payload.validation_error}", '
                                    f"returned exception: "
                                    f'"{payload_response.validation_error}" '
                                    f"(mapper: "
                                    f'"{payload_response.validation_error.mapper_name}")'  # noqa: E501
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
                                        "Client returned unexpected "
                                        "validation error: "
                                        f"got: "
                                        f'"{payload_response.validation_error}" '  # noqa: E501
                                        f"expected: "
                                        f'"{payload.validation_error}"'
                                    )
                                    if strict_exception_matching:
                                        raise LoggedError(message)
                                    else:
                                        logger.warning(message)

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

                if payload.valid() and isinstance(
                    fixture, BlockchainEngineFixture
                ):
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
                            status = forkchoice_response.payload_status.status
                            raise LoggedError(
                                f"unexpected status: want "
                                f"{PayloadStatusEnum.VALID}, got {status}"
                            )
        logger.info("All payloads processed successfully.")
