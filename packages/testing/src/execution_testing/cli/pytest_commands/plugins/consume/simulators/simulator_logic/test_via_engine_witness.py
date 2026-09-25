"""Hive simulator for witness-emitting payload execution."""

import pytest

from execution_testing.exceptions import EngineAPIError
from execution_testing.fixtures import BlockchainEngineFixture
from execution_testing.fixtures.blockchain import (
    FixtureEngineNewPayload,
    FixtureHeader,
)
from execution_testing.forks import Amsterdam, Fork
from execution_testing.logging import get_logger
from execution_testing.rpc import (
    EngineRPC,
    EngineSSZRPC,
    EngineWitnessEndpointNotImplementedError,
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

_JSONRPC_METHOD_NOT_FOUND = -32601


def _witness_endpoint_label(
    payload: FixtureEngineNewPayload,
    *,
    use_ssz_transport: bool,
    fork: Fork = Amsterdam,
) -> str:
    """Return the timing label for the selected witness endpoint."""
    if use_ssz_transport:
        if fork < Amsterdam:
            return f"engine_newPayloadV{payload.new_payload_version}"
        return "POST /engine/v1/payloads/witness"
    return f"engine_newPayloadWithWitnessV{payload.new_payload_version}"


def _send_payload_with_witness(
    *,
    use_ssz_transport: bool,
    engine_rpc: EngineRPC,
    engine_ssz_rpc: EngineSSZRPC,
    payload: FixtureEngineNewPayload,
    fork: Fork = Amsterdam,
) -> NewPayloadWithWitnessResponse | JSONRPCError:
    """
    Execute one payload through the configured witness endpoint.

    Return the response, or the caught Engine API error for the assertion to
    validate against the fixture's expected ``error_code``.
    """
    try:
        if use_ssz_transport:
            if fork < Amsterdam:
                # Import transition setup blocks through the ordinary API:
                # the witness endpoint is only available from Amsterdam.
                result = engine_rpc.new_payload(
                    *payload.params, version=payload.new_payload_version
                )
                return NewPayloadWithWitnessResponse(
                    status=result.status,
                    latest_valid_hash=result.latest_valid_hash,
                    validation_error=(
                        str(result.validation_error)
                        if result.validation_error is not None
                        else None
                    ),
                )
            return engine_ssz_rpc.new_payload_with_witness(
                *payload.params, fork=fork
            )
        return engine_rpc.new_payload_with_witness(
            *payload.params,
            version=payload.new_payload_version,
        )
    except EngineWitnessEndpointNotImplementedError as e:
        pytest.skip(str(e))
    except JSONRPCError as e:
        # An unimplemented endpoint is a transport skip, but only when no
        # error was expected; otherwise the error is a result to assert.
        if (
            not use_ssz_transport
            and payload.error_code is None
            and e.code == _JSONRPC_METHOD_NOT_FOUND
        ):
            pytest.skip(
                "client does not support "
                f"engine_newPayloadWithWitnessV"
                f"{payload.new_payload_version}: {e.message}"
            )
        return e


def _assert_witness_response(
    *,
    payload: FixtureEngineNewPayload,
    payload_number: int,
    result: NewPayloadWithWitnessResponse | JSONRPCError,
    payload_timing: TimingData,
    use_ssz_transport: bool,
    expect_witness: bool = True,
) -> None:
    """Assert one witness result (response or error) matches the fixture."""
    if isinstance(result, JSONRPCError):
        # The client raised an Engine API error; a negative test expects it.
        if payload.error_code is None:
            raise LoggedError(
                f"Payload {payload_number}: unexpected error: "
                f"{result.code} - {result.message}"
            )
        if result.code != payload.error_code:
            raise LoggedError(
                f"Payload {payload_number}: unexpected error code: "
                f"got {result.code}, expected {payload.error_code}"
            )
        return

    if payload.error_code is not None:
        # Negative test expected an Engine API error, but got a response.
        raise LoggedError(
            f"Payload {payload_number}: client did not raise the expected "
            f"Engine API error code {payload.error_code}"
        )

    response = result
    expected_status = (
        PayloadStatusEnum.VALID
        if payload.valid()
        else PayloadStatusEnum.INVALID
    )
    if response.status != expected_status:
        raise LoggedError(
            f"unexpected status: want {expected_status}, got {response.status}"
        )

    if response.status != PayloadStatusEnum.VALID:
        if use_ssz_transport and response.witness is not None:
            raise LoggedError(
                f"Payload {payload_number}: {response.status} status but "
                "client returned a non-empty witness; the REST+SSZ endpoint "
                "requires an empty witness when not VALID"
            )
        return

    expected_hash = payload.params[0].block_hash
    if response.latest_valid_hash != expected_hash:
        raise LoggedError(
            f"Payload {payload_number}: unexpected latest valid hash: "
            f"got {response.latest_valid_hash}, expected {expected_hash}"
        )
    if response.validation_error is not None:
        raise LoggedError(
            f"Payload {payload_number}: VALID status with a validation error: "
            f"{response.validation_error!r}"
        )
    if not expect_witness:
        return

    expected_witness = payload.execution_witness
    if expected_witness is None:
        logger.warning(
            f"Payload {payload_number}: fixture has no executionWitness; "
            "skipping witness diff"
        )
        return

    actual_witness = response.witness
    if actual_witness is None:
        raise LoggedError(
            f"Payload {payload_number}: VALID status but client returned "
            "no witness"
        )

    with payload_timing.time("Witness diff"):
        try:
            assert_witness_matches(
                expected=expected_witness,
                actual=actual_witness,
            )
        except WitnessMismatchError as e:
            raise LoggedError(str(e)) from e


def _advance_forkchoice_to_payload(
    *,
    engine_rpc: EngineRPC,
    payload: FixtureEngineNewPayload,
) -> None:
    """Advance the client forkchoice to one valid payload."""
    response = engine_rpc.forkchoice_updated(
        forkchoice_state=ForkchoiceState(
            head_block_hash=payload.params[0].block_hash,
        ),
        payload_attributes=None,
        version=payload.forkchoice_updated_version,
    )
    status = response.payload_status.status
    if status != PayloadStatusEnum.VALID:
        raise LoggedError(
            f"unexpected forkchoice status: want {PayloadStatusEnum.VALID}, "
            f"got {status}"
        )


def test_blockchain_via_engine_witness(
    timing_data: TimingData,
    eth_rpc: EthRPC,
    engine_rpc: EngineRPC,
    engine_ssz_rpc: EngineSSZRPC,
    fixture: BlockchainEngineFixture,
    genesis_header: FixtureHeader,
    use_ssz_transport: bool,
) -> None:
    """Execute blockchain-engine fixtures through a witness endpoint."""
    if any(p.execution_witness_mutated for p in fixture.payloads):
        pytest.skip("fixture contains a deliberately mutated executionWitness")

    if not any(p.execution_witness is not None for p in fixture.payloads):
        pytest.skip("fixture has no executionWitness on any payload")

    transport_label = "REST+SSZ" if use_ssz_transport else "JSON-RPC+RLP"
    logger.info(f"Using {transport_label} witness transport")

    payload_forks = [
        fixture.fork.fork_at(
            block_number=payload.params[0].number,
            timestamp=payload.params[0].timestamp,
        )
        for payload in fixture.payloads
    ]
    if use_ssz_transport:
        for payload, fork in zip(fixture.payloads, payload_forks, strict=True):
            if (
                fork >= Amsterdam
                and payload.error_code == EngineAPIError.InvalidParams
                and payload.params[0].block_access_list is None
            ):
                pytest.skip(
                    "JSON-only missing BAL field test cannot be encoded "
                    "as an Amsterdam SSZ payload; malformed SSZ requests "
                    "are tested separately"
                )
        witness_forks = {fork for fork in payload_forks if fork >= Amsterdam}
        if not witness_forks:
            pytest.skip("fixture has no Amsterdam or later payloads")
        try:
            for fork in witness_forks:
                engine_ssz_rpc.check_witness_capability(fork)
        except EngineWitnessEndpointNotImplementedError as e:
            pytest.skip(str(e))

        with timing_data.time("Malformed SSZ requests"):
            for body in (b"", b"\x28", bytes(40)):
                _assert_malformed_witness_request(engine_ssz_rpc, body)

    with timing_data.time("Initial forkchoice update"):
        logger.info("Sending initial forkchoice update to genesis block...")
        try:
            forkchoice_response = engine_rpc.forkchoice_updated_with_retry(
                forkchoice_state=ForkchoiceState(
                    head_block_hash=fixture.genesis.block_hash,
                ),
                forkchoice_version=(
                    fixture.payloads[0].forkchoice_updated_version
                ),
                max_attempts=30,
                wait_fixed=1.0,
            )
        except ForkchoiceUpdateTimeoutError as e:
            raise LoggedError(
                f"Timed out waiting for forkchoice update to genesis: {e}"
            ) from None

        status = forkchoice_response.payload_status.status
        if status != PayloadStatusEnum.VALID:
            raise LoggedError(
                f"Unexpected status on forkchoice updated to genesis: {status}"
            )

    with timing_data.time("Get genesis block"):
        genesis_block = eth_rpc.get_block_by_number(0)
        assert genesis_block is not None, "genesis_block is None"
        if genesis_block["hash"] != str(genesis_header.block_hash):
            raise GenesisBlockMismatchExceptionError(
                expected_header=genesis_header,
                got_genesis_block=genesis_block,
            )

    with timing_data.time("Payloads execution") as total_payload_timing:
        payload_count = len(fixture.payloads)
        logger.info(f"Starting execution of {payload_count} payloads...")
        for payload_number, (payload, active_fork) in enumerate(
            zip(fixture.payloads, payload_forks, strict=True), start=1
        ):
            expect_witness = not use_ssz_transport or active_fork >= Amsterdam
            logger.info(
                f"Processing payload {payload_number}/{payload_count}..."
            )
            with total_payload_timing.time(
                f"Payload {payload_number}"
            ) as payload_timing:
                with payload_timing.time(
                    _witness_endpoint_label(
                        payload,
                        use_ssz_transport=use_ssz_transport,
                        fork=active_fork,
                    )
                ):
                    witness_result = _send_payload_with_witness(
                        use_ssz_transport=use_ssz_transport,
                        engine_rpc=engine_rpc,
                        engine_ssz_rpc=engine_ssz_rpc,
                        payload=payload,
                        fork=active_fork,
                    )

                _assert_witness_response(
                    payload=payload,
                    payload_number=payload_number,
                    result=witness_result,
                    payload_timing=payload_timing,
                    use_ssz_transport=use_ssz_transport,
                    expect_witness=expect_witness,
                )

                if (
                    use_ssz_transport
                    and expect_witness
                    and payload.valid()
                    and not isinstance(witness_result, JSONRPCError)
                ):
                    with payload_timing.time("Already-known payload witness"):
                        repeated_result = _send_payload_with_witness(
                            use_ssz_transport=True,
                            engine_rpc=engine_rpc,
                            engine_ssz_rpc=engine_ssz_rpc,
                            payload=payload,
                            fork=active_fork,
                        )
                        _assert_witness_response(
                            payload=payload,
                            payload_number=payload_number,
                            result=repeated_result,
                            payload_timing=payload_timing,
                            use_ssz_transport=True,
                        )

                # A raised error means the block was rejected, so there is no
                # canonical block to advance the forkchoice to.
                if (
                    not isinstance(witness_result, JSONRPCError)
                    and payload.valid()
                ):
                    with payload_timing.time(
                        f"engine_forkchoiceUpdatedV"
                        f"{payload.forkchoice_updated_version}"
                    ):
                        _advance_forkchoice_to_payload(
                            engine_rpc=engine_rpc,
                            payload=payload,
                        )
        logger.info("All payloads processed successfully.")


def _assert_malformed_witness_request(
    engine_ssz_rpc: EngineSSZRPC,
    body: bytes,
) -> None:
    """Require malformed SSZ requests to fail at the HTTP decoding layer."""
    response = engine_ssz_rpc.post_witness_request(body, fork=Amsterdam)
    if response.status_code != 400:
        raise LoggedError(
            "Malformed SSZ request: expected HTTP 400, "
            f"got {response.status_code}"
        )
    content_type = response.headers.get("Content-Type", "").split(";", 1)[0]
    if content_type != "application/problem+json":
        raise LoggedError(
            "Malformed SSZ request: expected application/problem+json, "
            f"got {content_type!r}"
        )
    problem = response.json()
    accepted_types = {
        "/engine-api/errors/parse-error",
        "/engine-api/errors/ssz-decode-error",
    }
    if not body:
        # An absent body can fail HTTP request validation before SSZ decoding.
        accepted_types.add("/engine-api/errors/invalid-request")
    if problem.get("type") not in accepted_types:
        raise LoggedError(
            f"Malformed SSZ request: unexpected problem type {problem!r}"
        )
