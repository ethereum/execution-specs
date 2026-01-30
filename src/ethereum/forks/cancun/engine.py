"""
Engine API Specification (Cancun)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Executable specification for engine_newPayloadV3 validation.
Extends Shanghai (V2) with blob support (EIP-4844).
"""
__all__ = (
    "ExecutionPayloadV3",
    "NewPayloadRequestV3",
    "Valid",
    "ValidationError",
    "InvalidBlockHash",
    "InvalidTransactionEncoding",
    "InvalidGasUsed",
    "InvalidStateRoot",
    "InvalidReceiptsRoot",
    "InvalidLogsBloom",
    "InvalidBlobVersionedHashes",
    "ValidationResult",
    "payload_to_header",
    "verify_block_hash",
    "verify_blob_versioned_hashes",
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

from . import vm
from .blocks import Header, Withdrawal
from .bloom import logs_bloom
from .fork import apply_body, EMPTY_OMMER_HASH
from .fork_types import Address, Bloom, Root, VersionedHash
from .state import State, state_root
from .transactions import BlobTransaction, decode_transaction
from .trie import Trie, root as trie_root, trie_set


class InvalidBlobVersionedHashes(ValidationError):
    """
    Expected blob versioned hashes don't match those in transactions.

    This is an instant validation that runs even during sync.
    """

    pass


@slotted_freezable
@dataclass
class ExecutionPayloadV3:
    """
    Execution payload for engine_newPayloadV3 (Cancun).

    Extends V2 with blob gas fields (EIP-4844).
    """

    parent_hash: Hash32
    fee_recipient: Address
    state_root: Root
    receipts_root: Root
    logs_bloom: Bloom
    prev_randao: Bytes32
    block_number: Uint
    gas_limit: Uint
    gas_used: Uint
    timestamp: U256
    extra_data: Bytes
    base_fee_per_gas: Uint
    block_hash: Hash32
    transactions: Tuple[Bytes, ...]
    withdrawals: Tuple[Withdrawal, ...]
    blob_gas_used: U64
    """Total blob gas consumed by blob transactions."""
    excess_blob_gas: U64
    """Excess blob gas for blob base fee calculation."""


@slotted_freezable
@dataclass
class NewPayloadRequestV3:
    """
    Request wrapper for engine_newPayloadV3.

    Adds expected blob hashes and parent beacon block root.
    """

    payload: ExecutionPayloadV3
    expected_blob_versioned_hashes: Tuple[VersionedHash, ...]
    """Expected blob versioned hashes from CL."""
    parent_beacon_block_root: Hash32
    """Root of parent beacon block for EIP-4788."""


def extract_blob_versioned_hashes(
    transactions: Tuple[Bytes, ...]
) -> Tuple[VersionedHash, ...]:
    """
    Extract all blob versioned hashes from blob transactions.

    Concatenates hashes from all blob transactions in order.
    """
    hashes: List[VersionedHash] = []
    for tx_bytes in transactions:
        if len(tx_bytes) == 0:
            continue
        # Type 3 = blob transaction
        if tx_bytes[0] == 0x03:
            try:
                tx = decode_transaction(tx_bytes)
                if isinstance(tx, BlobTransaction):
                    hashes.extend(tx.blob_versioned_hashes)
            except Exception:
                pass  # Invalid tx will be caught by decode_transactions
    return tuple(hashes)


def verify_blob_versioned_hashes(
    payload: ExecutionPayloadV3,
    expected: Tuple[VersionedHash, ...],
) -> Optional[InvalidBlobVersionedHashes]:
    """
    Verify blob versioned hashes match expected.

    This is an instant validation - runs even during sync.
    """
    actual = extract_blob_versioned_hashes(payload.transactions)

    if actual != expected:
        return InvalidBlobVersionedHashes(
            f"blob versioned hashes mismatch: expected {len(expected)}, got {len(actual)}"
        )

    return None


def payload_to_header(
    payload: ExecutionPayloadV3, parent_beacon_block_root: Hash32
) -> Header:
    """Construct a Header from ExecutionPayloadV3."""
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
    )


def verify_block_hash(
    payload: ExecutionPayloadV3,
    parent_beacon_block_root: Hash32,
) -> Optional[InvalidBlockHash]:
    """Verify the payload's block_hash matches the computed header hash."""
    header = payload_to_header(payload, parent_beacon_block_root)
    computed_hash = keccak256(rlp.encode(header))

    if computed_hash != payload.block_hash:
        return InvalidBlockHash(
            f"block hash mismatch: expected {computed_hash.hex()}, "
            f"got {payload.block_hash.hex()}"
        )

    return None


ValidationResult = Union[Valid, ValidationError]


def validate_execution_payload(
    request: NewPayloadRequestV3,
    parent_header: Header,
    state: State,
    chain_id: U64,
    block_hashes: List[Hash32],
) -> ValidationResult:
    """
    Validate an execution payload (V3).

    Adds blob versioned hash verification.
    """
    payload = request.payload

    # Step 1: Verify block hash (instant)
    hash_error = verify_block_hash(payload, request.parent_beacon_block_root)
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

    return Valid(
        state_root=computed_state_root,
        receipts_root=computed_receipts_root,
        logs_bloom=computed_logs_bloom,
        gas_used=computed_gas_used,
    )
