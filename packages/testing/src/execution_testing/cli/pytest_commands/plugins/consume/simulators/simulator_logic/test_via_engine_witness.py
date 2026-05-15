"""
A hive based simulator that executes blocks against clients using either:

- `engine_newPayloadWithWitnessVX` JSON-RPC (geth-style, RLP witness) — default
- `POST /new-payload-with-witness` REST+SSZ (execution-apis PR #773) — `--ssz`

Both paths converge on a common verification: status matches the fixture
expectation, and when VALID the client-emitted witness exactly matches
`fixture.execution_witness` on state/codes/headers.
"""

import pytest

from execution_testing.fixtures import BlockchainEngineFixture
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.logging import get_logger
from execution_testing.rpc import (
    EngineRPC,
    EngineWitnessEndpointNotImplementedError,
    EngineWitnessRPC,
    EthRPC,
    ForkchoiceUpdateTimeoutError,
)
from execution_testing.rpc.rpc_types import (
    ForkchoiceState,
    JSONRPCError,
    NewPayloadWithWitnessResponse,
    PayloadStatusEnum,
)

from ..helpers.exceptions import (
    GenesisBlockMismatchExceptionError,
    LoggedError,
)
from ..helpers.timing import TimingData
from ..helpers.witness_diff import (
    WitnessMismatchError,
    assert_witness_matches,
)

logger = get_logger(__name__)


def _call_endpoint(
    *,
    use_ssz: bool,
    engine_rpc: EngineRPC,
    engine_witness_rpc: EngineWitnessRPC,
    payload_params: tuple,
    version: int,
) -> NewPayloadWithWitnessResponse:
    """Dispatch to the SSZ REST or RLP JSON-RPC witness endpoint."""
    if use_ssz:
        return engine_witness_rpc.new_payload_with_witness(*payload_params)
    return engine_rpc.new_payload_with_witness(
        *payload_params, version=version
    )


def test_blockchain_via_engine_witness(
    timing_data: TimingData,
    eth_rpc: EthRPC,
    engine_rpc: EngineRPC,
    engine_witness_rpc: EngineWitnessRPC,
    fixture: BlockchainEngineFixture,
    genesis_header: FixtureHeader,
    use_ssz_transport: bool,
) -> None:
    """
    Execute blockchain-engine fixtures and assert the client-emitted witness
    matches the fixture witness.

    Per payload:
    1. Call the witness-emitting endpoint (RLP JSON-RPC or REST+SSZ).
    2. Assert status matches fixture expectation.
    3. On VALID, compare the client-emitted witness exactly to
       fixture.execution_witness per field (state, codes, headers).
    4. On VALID, issue an engine_forkchoiceUpdatedVX to advance the head.

    Skip the whole fixture if no payload carries an executionWitness, or if
    the SSZ endpoint is missing (HTTP 404/405) when `--ssz` is requested.
    """
    if not any(p.execution_witness is not None for p in fixture.payloads):
        pytest.skip("fixture has no executionWitness on any payload")

    transport_label = "REST+SSZ" if use_ssz_transport else "JSON-RPC+RLP"
    logger.info(f"Using {transport_label} witness transport")

    with timing_data.time("Initial forkchoice update"):
        logger.info("Sending initial forkchoice update to genesis block...")
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
        genesis_block = eth_rpc.get_block_by_number(0)
        assert genesis_block is not None, "genesis_block is None"
        if genesis_block["hash"] != str(genesis_header.block_hash):
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
                timing_label = (
                    "POST /new-payload-with-witness"
                    if use_ssz_transport
                    else f"engine_newPayloadWithWitnessV"
                    f"{payload.new_payload_version}"
                )
                with payload_timing.time(timing_label):
                    try:
                        response = _call_endpoint(
                            use_ssz=use_ssz_transport,
                            engine_rpc=engine_rpc,
                            engine_witness_rpc=engine_witness_rpc,
                            payload_params=payload.params,
                            version=payload.new_payload_version,
                        )
                    except EngineWitnessEndpointNotImplementedError as e:
                        pytest.skip(str(e))
                    except JSONRPCError as e:
                        # geth returns -32601 Method not found when
                        # engine_newPayloadWithWitness is not registered.
                        if e.code == -32601:
                            pytest.skip(
                                "client does not support "
                                f"engine_newPayloadWithWitnessV"
                                f"{payload.new_payload_version}: {e.message}"
                            )
                        raise

                expected_validity = (
                    PayloadStatusEnum.VALID
                    if payload.valid()
                    else PayloadStatusEnum.INVALID
                )
                if response.status != expected_validity:
                    raise LoggedError(
                        f"unexpected status: want {expected_validity}, "
                        f"got {response.status}"
                    )

                if response.status == PayloadStatusEnum.VALID:
                    if payload.execution_witness is None:
                        logger.warning(
                            f"Payload {i + 1}: fixture has no "
                            "executionWitness; skipping witness diff"
                        )
                    elif response.witness is None:
                        raise LoggedError(
                            f"Payload {i + 1}: VALID status but client "
                            "returned no witness"
                        )
                    else:
                        with payload_timing.time("Witness diff"):
                            try:
                                assert_witness_matches(
                                    expected=payload.execution_witness,
                                    actual=response.witness,
                                )
                            except WitnessMismatchError as e:
                                raise LoggedError(str(e)) from e
                elif use_ssz_transport and response.witness is not None:
                    # PR #773 requires an empty witness when status != VALID.
                    # Geth's JSON-RPC does not mandate this, so only enforce
                    # in SSZ mode.
                    raise LoggedError(
                        f"Payload {i + 1}: {response.status} status but "
                        "client returned a non-empty witness (PR #773 "
                        "requires empty witness when not VALID)"
                    )

                if payload.valid():
                    with payload_timing.time(
                        f"engine_forkchoiceUpdatedV"
                        f"{payload.forkchoice_updated_version}"
                    ):
                        fcu_response = engine_rpc.forkchoice_updated(
                            forkchoice_state=ForkchoiceState(
                                head_block_hash=payload.params[0].block_hash,
                            ),
                            payload_attributes=None,
                            version=payload.forkchoice_updated_version,
                        )
                        status = fcu_response.payload_status.status
                        if status != PayloadStatusEnum.VALID:
                            raise LoggedError(
                                f"unexpected forkchoice status: want "
                                f"{PayloadStatusEnum.VALID}, got {status}"
                            )
        logger.info("All payloads processed successfully.")
