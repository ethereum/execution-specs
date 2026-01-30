"""
Engine API Specification (Prague)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Executable specification for engine_newPayloadV4 validation.
Extends Cancun (V3) with execution requests (EIP-7685).
"""
__all__ = (
    "ExecutionPayloadV3",
    "NewPayloadRequestV4",
    "Valid",
    "ValidationError",
    "InvalidBlockHash",
    "InvalidTransactionEncoding",
    "InvalidGasUsed",
    "InvalidStateRoot",
    "InvalidReceiptsRoot",
    "InvalidLogsBloom",
    "InvalidBlobVersionedHashes",
    "InvalidExecutionRequests",
    "ValidationResult",
    "payload_to_header",
    "verify_block_hash",
    "verify_blob_versioned_hashes",
    "verify_execution_requests",
    "decode_transactions",
    "compute_transactions_root",
    "compute_withdrawals_root",
    "validate_execution_payload",
)

from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

from ethereum_rlp import rlp

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32, keccak256

# Re-export common types
from ethereum.forks.paris.engine import (
    Valid,
    ValidationError,
    InvalidBlockHash,
    InvalidTransactionEncoding,
    InvalidGasUsed,
    InvalidStateRoot,
    InvalidReceiptsRoot,
    InvalidLogsBloom,
    compute_transactions_root,
    decode_transactions,
)
from ethereum.forks.shanghai.engine import compute_withdrawals_root
from ethereum.forks.cancun.engine import (
    ExecutionPayloadV3,
    InvalidBlobVersionedHashes,
    extract_blob_versioned_hashes,
    verify_blob_versioned_hashes,
)

from . import vm
from .blocks import Header, Withdrawal
from .bloom import logs_bloom
from .fork import apply_body, EMPTY_OMMER_HASH
from .fork_types import Address, Bloom, Root, VersionedHash
from .requests import compute_requests_hash
from .state import State, state_root
from .trie import Trie, root as trie_root, trie_set


class InvalidExecutionRequests(ValidationError):
    """
    Execution requests commitment doesn't match header.

    This is an instant validation that runs even during sync.
    """

    pass


@slotted_freezable
@dataclass
class NewPayloadRequestV4:
    """
    Request wrapper for engine_newPayloadV4.

    Adds execution requests per EIP-7685.
    """

    payload: ExecutionPayloadV3  # Same payload structure as V3
    expected_blob_versioned_hashes: Tuple[VersionedHash, ...]
    parent_beacon_block_root: Hash32
    execution_requests: Tuple[Bytes, ...]
    """Execution layer requests (deposits, withdrawals, consolidations)."""


def verify_execution_requests(
    execution_requests: Tuple[Bytes, ...],
    expected_hash: Hash32,
) -> Optional[InvalidExecutionRequests]:
    """
    Verify execution requests commitment matches expected hash.

    This is an instant validation.
    """
    computed_hash = compute_requests_hash(list(execution_requests))

    if computed_hash != expected_hash:
        return InvalidExecutionRequests(
            f"execution requests hash mismatch: expected {expected_hash.hex()}, "
            f"got {computed_hash.hex()}"
        )

    return None


def payload_to_header(
    payload: ExecutionPayloadV3,
    parent_beacon_block_root: Hash32,
    requests_hash: Hash32,
) -> Header:
    """Construct a Prague Header from ExecutionPayloadV3."""
    transactions_root = compute_transactions_root(payload.transactions)
    withdrawals_root = compute_withdrawals_root(payload.withdrawals)

    return Header(
        parent_hash=payload.parent_hash,
        ommers_hash=EMPTY_OMMER_HASH,
        coinbase=payload.fee_recipient,
        state_root=payload.state_root,
        transactions_root=transactions_root,
        receipt_root=payload.receipts_root,
        bloom=payload.logs_bloom,
        difficulty=Uint(0),
        number=payload.block_number,
        gas_limit=payload.gas_limit,
        gas_used=payload.gas_used,
        timestamp=payload.timestamp,
        extra_data=payload.extra_data,
        prev_randao=payload.prev_randao,
        nonce=b"\x00\x00\x00\x00\x00\x00\x00\x00",
        base_fee_per_gas=payload.base_fee_per_gas,
        withdrawals_root=withdrawals_root,
        blob_gas_used=payload.blob_gas_used,
        excess_blob_gas=payload.excess_blob_gas,
        parent_beacon_block_root=parent_beacon_block_root,
        requests_hash=requests_hash,
    )


def verify_block_hash(
    payload: ExecutionPayloadV3,
    parent_beacon_block_root: Hash32,
    requests_hash: Hash32,
) -> Optional[InvalidBlockHash]:
    """Verify the payload's block_hash matches the computed header hash."""
    header = payload_to_header(payload, parent_beacon_block_root, requests_hash)
    computed_hash = keccak256(rlp.encode(header))

    if computed_hash != payload.block_hash:
        return InvalidBlockHash(
            f"block hash mismatch: expected {computed_hash.hex()}, "
            f"got {payload.block_hash.hex()}"
        )

    return None


ValidationResult = Union[Valid, ValidationError]


def validate_execution_payload(
    request: NewPayloadRequestV4,
    parent_header: Header,
    state: State,
    chain_id: U64,
    block_hashes: List[Hash32],
) -> ValidationResult:
    """
    Validate an execution payload (V4).

    Adds execution requests verification.
    """
    payload = request.payload

    # Compute requests hash first (needed for block hash verification)
    requests_hash = Hash32(compute_requests_hash(list(request.execution_requests)))

    # Step 1: Verify block hash (instant)
    hash_error = verify_block_hash(
        payload, request.parent_beacon_block_root, requests_hash
    )
    if hash_error is not None:
        return hash_error

    # Step 2: Decode and validate transactions (instant)
    tx_error = decode_transactions(payload.transactions)
    if tx_error is not None:
        return tx_error

    # Step 3: Verify blob versioned hashes (instant)
    blob_error = verify_blob_versioned_hashes(
        payload, request.expected_blob_versioned_hashes
    )
    if blob_error is not None:
        return blob_error

    # Step 4: Execute payload
    block_env = vm.BlockEnvironment(
        chain_id=chain_id,
        state=state,
        block_gas_limit=payload.gas_limit,
        block_hashes=block_hashes,
        coinbase=payload.fee_recipient,
        number=payload.block_number,
        base_fee_per_gas=payload.base_fee_per_gas,
        time=payload.timestamp,
        prev_randao=payload.prev_randao,
        excess_blob_gas=payload.excess_blob_gas,
        parent_beacon_block_root=request.parent_beacon_block_root,
    )

    block_output = apply_body(
        block_env=block_env,
        transactions=payload.transactions,
        withdrawals=payload.withdrawals,
    )

    # Step 5: Verify computed outputs
    computed_gas_used = block_output.block_gas_used
    if computed_gas_used != payload.gas_used:
        return InvalidGasUsed(payload.gas_used, computed_gas_used)

    computed_state_root = state_root(block_env.state)
    if computed_state_root != payload.state_root:
        return InvalidStateRoot(
            f"state root mismatch: expected {payload.state_root.hex()}, "
            f"got {computed_state_root.hex()}"
        )

    computed_receipts_root = trie_root(block_output.receipts_trie)
    if computed_receipts_root != payload.receipts_root:
        return InvalidReceiptsRoot(
            f"receipts root mismatch: expected {payload.receipts_root.hex()}, "
            f"got {computed_receipts_root.hex()}"
        )

    computed_logs_bloom = logs_bloom(block_output.block_logs)
    if computed_logs_bloom != payload.logs_bloom:
        return InvalidLogsBloom("logs bloom mismatch")

    # Step 6: Verify execution requests match computed requests
    computed_requests = tuple(block_output.requests)
    if computed_requests != request.execution_requests:
        return InvalidExecutionRequests(
            f"execution requests mismatch: expected {len(request.execution_requests)} "
            f"requests, computed {len(computed_requests)} requests"
        )

    return Valid(
        state_root=computed_state_root,
        receipts_root=computed_receipts_root,
        logs_bloom=computed_logs_bloom,
        gas_used=computed_gas_used,
    )
