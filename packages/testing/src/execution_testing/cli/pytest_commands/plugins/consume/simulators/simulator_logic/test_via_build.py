"""
A hive based simulator that tests block building correctness via the
``testing_buildBlockV1`` endpoint.

For each valid payload in a fixture, transactions and block attributes
are sent to the block building endpoint. The resulting block is validated
field-by-field against the fixture's expected block, then imported back
into the client via ``engine_newPayloadVX`` and
``engine_forkchoiceUpdatedVX`` to advance the chain.
"""

import json
from difflib import unified_diff
from typing import List

from execution_testing.base_types import Bytes
from execution_testing.fixtures import BlockchainEngineFixture
from execution_testing.fixtures.blockchain import (
    FixtureEngineNewPayload,
    FixtureExecutionPayload,
    FixtureHeader,
)
from execution_testing.logging import get_logger
from execution_testing.rpc import (
    EngineRPC,
    EthRPC,
    ForkchoiceUpdateTimeoutError,
    TestingRPC,
)
from execution_testing.rpc.rpc_types import (
    ForkchoiceState,
    PayloadAttributes,
    PayloadStatusEnum,
)
from execution_testing.test_types.block_access_list import BlockAccessList

from ..helpers.exceptions import (
    GenesisBlockMismatchExceptionError,
    LoggedError,
)
from ..helpers.timing import TimingData

logger = get_logger(__name__)

# Execution-dependent fields that must match exactly between the built
# and expected payloads.  Excluded:
# - gas_limit: testing_buildBlockV1 doesn't accept it; the client
#   picks its own via EIP-1559 (validated separately by range check).
# - block_hash: depends on gas_limit, so it will differ too.
_VALIDATED_FIELDS = (
    "state_root",
    "receipts_root",
    "gas_used",
    "logs_bloom",
    "base_fee_per_gas",
    "blob_gas_used",
    "excess_blob_gas",
    "block_access_list",
    "fee_recipient",
    "number",
    "timestamp",
    "extra_data",
    "prev_randao",
    "parent_hash",
    "transactions",
    "withdrawals",
)


def _format_block_access_list_diff(
    expected_rlp: bytes | None,
    built_rlp: bytes | None,
) -> str:
    """Return a readable diff for a BAL mismatch."""
    if expected_rlp is None or built_rlp is None:
        return f"expected {expected_rlp!r}, got {built_rlp!r}"

    try:
        expected_bal = BlockAccessList.from_rlp(Bytes(expected_rlp))
        built_bal = BlockAccessList.from_rlp(Bytes(built_rlp))
    except Exception as exc:
        return (
            f"expected {expected_rlp!r}, got {built_rlp!r} "
            f"(BAL decode failed: {exc})"
        )

    expected_json = json.dumps(
        expected_bal.model_dump(mode="json"),
        indent=2,
        sort_keys=True,
    )
    built_json = json.dumps(
        built_bal.model_dump(mode="json"),
        indent=2,
        sort_keys=True,
    )
    diff = "\n".join(
        unified_diff(
            expected_json.splitlines(),
            built_json.splitlines(),
            fromfile="expected_bal",
            tofile="client_built_bal",
            lineterm="",
        )
    )
    return (
        f"expected {expected_rlp!r}, got {built_rlp!r}\n"
        "decoded BAL diff relative to expected BAL:\n"
        "  '-' lines are present in the expected BAL but missing from the "
        "client-built BAL.\n"
        "  '+' lines are extra or changed in the client-built BAL compared "
        "to the expected BAL.\n"
        f"{diff}"
    )


def _payload_attributes(
    payload: FixtureEngineNewPayload,
) -> PayloadAttributes:
    """Extract PayloadAttributes from a fixture payload."""
    execution_payload = payload.params[0]
    parent_beacon_block_root = (
        payload.params[2] if len(payload.params) >= 3 else None
    )
    return PayloadAttributes(
        timestamp=execution_payload.timestamp,
        prev_randao=execution_payload.prev_randao,
        suggested_fee_recipient=execution_payload.fee_recipient,
        withdrawals=execution_payload.withdrawals,
        parent_beacon_block_root=parent_beacon_block_root,
    )


def _validate_gas_limit(
    built: FixtureExecutionPayload,
    parent_gas_limit: int,
) -> None:
    """Validate the built block's gas limit is within EIP-1559 range."""
    built_gas_limit = int(built.gas_limit)
    max_delta = parent_gas_limit // 1024

    if abs(built_gas_limit - parent_gas_limit) >= max_delta:
        raise LoggedError(
            f"Gas limit for block {built.number} outside "
            f"EIP-1559 range: parent={parent_gas_limit} "
            f"(±{max_delta}), got {built.gas_limit}"
        )


def _validate_built_block(
    built: FixtureExecutionPayload,
    expected: FixtureExecutionPayload,
    parent_gas_limit: int,
) -> None:
    """
    Validate the built block against the fixture's expected block.

    Check all execution-dependent fields for exact match and verify
    the gas limit is within the valid EIP-1559 range.
    """
    _validate_gas_limit(built, parent_gas_limit)

    mismatches: List[str] = []
    for field in _VALIDATED_FIELDS:
        built_val = getattr(built, field)
        expected_val = getattr(expected, field)
        if built_val != expected_val:
            if field == "block_access_list":
                mismatches.append(
                    "  block_access_list:\n"
                    + _format_block_access_list_diff(expected_val, built_val)
                )
                continue
            mismatches.append(
                f"  {field}: expected {expected_val}, got {built_val}"
            )

    if mismatches:
        detail = "\n".join(mismatches)
        raise LoggedError(
            f"Block validation failed for block {expected.number}:\n{detail}"
        )

    logger.info(f"Block validated for block {expected.number}.")


def test_blockchain_via_build(
    timing_data: TimingData,
    eth_rpc: EthRPC,
    engine_rpc: EngineRPC,
    testing_rpc: TestingRPC,
    fixture: BlockchainEngineFixture,
    genesis_header: FixtureHeader,
) -> None:
    """
    Test block building correctness against a client.

    For each valid payload in the fixture:
    1. Build a block via ``testing_buildBlockV1``
    2. Validate execution-dependent fields + gas limit range
    3. Import the fixture block via ``engine_newPayloadVX``
    4. Advance the chain via ``engine_forkchoiceUpdatedVX``
    """
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
                    "Unexpected status on forkchoice updated to "
                    f"genesis: {response.payload_status.status}"
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

    with timing_data.time("Block building") as total_build_timing:
        valid_payloads = [p for p in fixture.payloads if p.valid()]
        logger.info(
            f"Starting block building for {len(valid_payloads)} "
            f"valid payload(s) "
            f"(of {len(fixture.payloads)} total)..."
        )
        parent_gas_limit = int(genesis_header.gas_limit)
        for i, payload in enumerate(valid_payloads):
            expected_payload = payload.params[0]
            logger.info(
                f"Building block {i + 1}/{len(valid_payloads)} "
                f"(number {expected_payload.number})..."
            )
            with total_build_timing.time(f"Block {i + 1}") as block_timing:
                # 1. Build the block
                with block_timing.time("testing_buildBlockV1"):
                    attributes = _payload_attributes(payload)
                    build_response = testing_rpc.build_block(
                        parent_block_hash=(expected_payload.parent_hash),
                        payload_attributes=attributes,
                        transactions=(expected_payload.transactions),
                        extra_data=expected_payload.extra_data,
                    )

                # 2. Validate fields + gas limit range
                _validate_built_block(
                    built=build_response.execution_payload,
                    expected=expected_payload,
                    parent_gas_limit=parent_gas_limit,
                )

                # 3. Import the fixture block (not the built block)
                #    so the chain advances with the expected gas limit
                #    and block hash.
                with block_timing.time(
                    f"engine_newPayloadV{payload.new_payload_version}"
                ):
                    logger.info(
                        "Importing block via "
                        "engine_newPayloadV"
                        f"{payload.new_payload_version}..."
                    )
                    import_response = engine_rpc.new_payload(
                        *payload.params,
                        version=payload.new_payload_version,
                    )
                    if import_response.status != PayloadStatusEnum.VALID:
                        raise LoggedError(
                            "Unexpected status importing "
                            f"block: {import_response.status}"
                        )

                # 4. Advance the chain via forkchoice update
                with block_timing.time(
                    "engine_forkchoiceUpdatedV"
                    f"{payload.forkchoice_updated_version}"
                ):
                    v = payload.forkchoice_updated_version
                    logger.info(f"Sending engine_forkchoiceUpdatedV{v}...")
                    fcu_response = engine_rpc.forkchoice_updated(
                        forkchoice_state=ForkchoiceState(
                            head_block_hash=(expected_payload.block_hash),
                        ),
                        payload_attributes=None,
                        version=v,
                    )
                    fcu_status = fcu_response.payload_status.status
                    if fcu_status != PayloadStatusEnum.VALID:
                        raise LoggedError(
                            "Unexpected status on forkchoice "
                            f"update: want "
                            f"{PayloadStatusEnum.VALID}, "
                            f"got {fcu_status}"
                        )

            # Use the fixture's gas limit since we import the
            # fixture block, not the built one.
            parent_gas_limit = int(expected_payload.gas_limit)

        logger.info("All blocks built and verified successfully.")
