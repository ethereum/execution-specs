"""Genesis handshake shared by the engine-family hive simulators."""

from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.logging import get_logger
from execution_testing.rpc import (
    EngineRPC,
    EthRPC,
    ForkchoiceUpdateTimeoutError,
)
from execution_testing.rpc.rpc_types import ForkchoiceState, PayloadStatusEnum

from .exceptions import GenesisBlockMismatchExceptionError, LoggedError
from .timing import TimingData

logger = get_logger(__name__)


def send_forkchoice_update_to_genesis(
    engine_rpc: EngineRPC,
    *,
    genesis_header: FixtureHeader,
    forkchoice_version: int,
    timing_data: TimingData,
) -> None:
    """Send `engine_forkchoiceUpdatedVX` to genesis and require VALID."""
    with timing_data.time("Initial forkchoice update"):
        logger.info("Sending initial forkchoice update to genesis block...")
        try:
            response = engine_rpc.forkchoice_updated_with_retry(
                forkchoice_state=ForkchoiceState(
                    head_block_hash=genesis_header.block_hash,
                ),
                forkchoice_version=forkchoice_version,
                max_attempts=30,
                wait_fixed=1.0,
            )
            if response.payload_status.status != PayloadStatusEnum.VALID:
                raise LoggedError(
                    "Unexpected status on forkchoice updated to genesis: "
                    f"{response.payload_status.status}"
                )
        except ForkchoiceUpdateTimeoutError as e:
            raise LoggedError(
                f"Timed out waiting for forkchoice update to genesis: {e}"
            ) from None


def verify_genesis_block_hash(
    eth_rpc: EthRPC,
    genesis_header: FixtureHeader,
    timing_data: TimingData,
) -> None:
    """Verify the client's genesis block hash matches the fixture's."""
    with timing_data.time("Get genesis block"):
        logger.info("Calling getBlockByNumber to get genesis block...")
        genesis_block = eth_rpc.get_block_by_number(0)
        assert genesis_block is not None, "genesis_block is None"
        if genesis_block["hash"] != str(genesis_header.block_hash):
            expected = genesis_header.block_hash
            got = genesis_block["hash"]
            logger.fail(
                "Genesis block hash mismatch. "
                f"Expected: {expected}, Got: {got}"
            )
            raise GenesisBlockMismatchExceptionError(
                expected_header=genesis_header,
                got_genesis_block=genesis_block,
            )
