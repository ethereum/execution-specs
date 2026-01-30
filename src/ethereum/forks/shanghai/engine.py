"""
Engine API Specification (Shanghai)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Executable specification for engine_newPayloadV2 validation.
Extends Paris (V1) with withdrawals support.
"""
__all__ = (
    "ExecutionPayloadV2",
    "NewPayloadRequestV2",
    "Valid",
    "ValidationError",
    "InvalidBlockHash",
    "InvalidTransactionEncoding",
    "InvalidGasUsed",
    "InvalidStateRoot",
    "InvalidReceiptsRoot",
    "InvalidLogsBloom",
    "ValidationResult",
    "payload_to_header",
    "verify_block_hash",
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

# Re-export common types from Paris
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

from . import vm
from .blocks import Header, Withdrawal
from .bloom import logs_bloom
from .fork import apply_body, EMPTY_OMMER_HASH
from .fork_types import Address, Bloom, Root
from .state import State, state_root
from .trie import Trie, root as trie_root, trie_set


@slotted_freezable
@dataclass
class ExecutionPayloadV2:
    """
    Execution payload for engine_newPayloadV2 (Shanghai).

    Extends V1 with withdrawals from the beacon chain.
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
    """Validator withdrawals from the beacon chain."""


@slotted_freezable
@dataclass
class NewPayloadRequestV2:
    """Request wrapper for engine_newPayloadV2."""

    payload: ExecutionPayloadV2


def compute_withdrawals_root(withdrawals: Tuple[Withdrawal, ...]) -> Root:
    """Compute the withdrawals trie root."""
    trie: Trie[Bytes, Bytes] = Trie(secured=False, default=b"")
    for i, withdrawal in enumerate(withdrawals):
        trie_set(trie, rlp.encode(Uint(i)), rlp.encode(withdrawal))
    return trie_root(trie)


def payload_to_header(payload: ExecutionPayloadV2) -> Header:
    """Construct a Header from ExecutionPayloadV2."""
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
    )


def verify_block_hash(payload: ExecutionPayloadV2) -> Optional[InvalidBlockHash]:
    """Verify the payload's block_hash matches the computed header hash."""
    header = payload_to_header(payload)
    computed_hash = keccak256(rlp.encode(header))

    if computed_hash != payload.block_hash:
        return InvalidBlockHash(
            f"block hash mismatch: expected {computed_hash.hex()}, "
            f"got {payload.block_hash.hex()}"
        )

    return None


ValidationResult = Union[Valid, ValidationError]


def validate_execution_payload(
    request: NewPayloadRequestV2,
    parent_header: Header,
    state: State,
    chain_id: U64,
    block_hashes: List[Hash32],
) -> ValidationResult:
    """
    Validate an execution payload (V2).

    Same as V1 but passes withdrawals to apply_body.
    """
    payload = request.payload

    # Step 1: Verify block hash (instant)
    hash_error = verify_block_hash(payload)
    if hash_error is not None:
        return hash_error

    # Step 2: Decode and validate transactions (instant)
    tx_error = decode_transactions(payload.transactions)
    if tx_error is not None:
        return tx_error

    # Step 3: Execute payload (with withdrawals)
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
    )

    block_output = apply_body(
        block_env=block_env,
        transactions=payload.transactions,
        withdrawals=payload.withdrawals,
    )

    # Step 4: Verify computed outputs
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
