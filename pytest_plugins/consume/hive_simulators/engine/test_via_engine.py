"""
A hive based simulator that executes blocks against clients using the `engine_newPayloadVX` method
from the Engine API. The simulator uses the `BlockchainEngineFixtures` to test against clients.

Each `engine_newPayloadVX` is verified against the appropriate VALID/INVALID responses.
"""

from ethereum_test_fixtures import BlockchainEngineFixture
from ethereum_test_rpc import EngineRPC, EthRPC
from ethereum_test_rpc.types import ForkchoiceState, JSONRPCError, PayloadStatusEnum
from pytest_plugins.consume.hive_simulators.exceptions import GenesisBlockMismatchExceptionError

from ...decorator import fixture_format
from ..timing import TimingData


@fixture_format(BlockchainEngineFixture)
def test_via_engine(
    timing_data: TimingData,
    eth_rpc: EthRPC,
    engine_rpc: EngineRPC,
    blockchain_fixture: BlockchainEngineFixture,
):
    """
    1. Check the client genesis block hash matches `blockchain_fixture.genesis.block_hash`.
    2. Execute the test case fixture blocks against the client under test using the
    `engine_newPayloadVX` method from the Engine API.
    3. For valid payloads a forkchoice update is performed to finalize the chain.
    """
    # Send a initial forkchoice update
    with timing_data.time("Initial forkchoice update"):
        forkchoice_response = engine_rpc.forkchoice_updated(
            forkchoice_state=ForkchoiceState(
                head_block_hash=blockchain_fixture.genesis.block_hash,
            ),
            payload_attributes=None,
            version=blockchain_fixture.payloads[0].forkchoice_updated_version,
        )
        assert forkchoice_response.payload_status.status == PayloadStatusEnum.VALID, (
            f"unexpected status on forkchoice updated to genesis: {forkchoice_response}"
        )

    with timing_data.time("Get genesis block"):
        genesis_block = eth_rpc.get_block_by_number(0)
        if genesis_block["hash"] != str(blockchain_fixture.genesis.block_hash):
            raise GenesisBlockMismatchExceptionError(
                expected_header=blockchain_fixture.genesis,
                got_genesis_block=genesis_block,
            )

    with timing_data.time("Payloads execution") as total_payload_timing:
        for i, payload in enumerate(blockchain_fixture.payloads):
            with total_payload_timing.time(f"Payload {i + 1}") as payload_timing:
                with payload_timing.time(f"engine_newPayloadV{payload.new_payload_version}"):
                    try:
                        payload_response = engine_rpc.new_payload(
                            *payload.params,
                            version=payload.new_payload_version,
                        )
                        assert payload_response.status == (
                            PayloadStatusEnum.VALID
                            if payload.valid()
                            else PayloadStatusEnum.INVALID
                        ), f"unexpected status: {payload_response}"
                        if payload.error_code is not None:
                            raise Exception(
                                "Client failed to raise expected Engine API error code: "
                                f"{payload.error_code}"
                            )
                    except JSONRPCError as e:
                        if payload.error_code is None:
                            raise Exception(f"unexpected error: {e.code} - {e.message}") from e
                        if e.code != payload.error_code:
                            raise Exception(
                                f"unexpected error code: {e.code}, expected: {payload.error_code}"
                            ) from e

                if payload.valid():
                    with payload_timing.time(
                        f"engine_forkchoiceUpdatedV{payload.forkchoice_updated_version}"
                    ):
                        # Send a forkchoice update to the engine
                        forkchoice_response = engine_rpc.forkchoice_updated(
                            forkchoice_state=ForkchoiceState(
                                head_block_hash=payload.params[0].block_hash,
                            ),
                            payload_attributes=None,
                            version=payload.forkchoice_updated_version,
                        )
                        assert (
                            forkchoice_response.payload_status.status == PayloadStatusEnum.VALID
                        ), f"unexpected status: {forkchoice_response}"
