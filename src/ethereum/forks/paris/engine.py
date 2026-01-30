"""
Engine API Specification
^^^^^^^^^^^^^^^^^^^^^^^^

Executable specification for engine_newPayload validation.
This module defines the types and validation logic for the Engine API
as specified in https://github.com/ethereum/execution-apis.
"""
__all__ = (
    "ExecutionPayloadV1",
    "NewPayloadRequestV1",
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
    "validate_execution_payload",
)

from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

from ethereum_rlp import rlp

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import EthereumException

from . import vm
from .blocks import Header
from .bloom import logs_bloom
from .fork import apply_body, EMPTY_OMMER_HASH
from .fork_types import Address, Bloom, Root
from .state import State, state_root
from .transactions import (
    LegacyTransaction,
    decode_transaction,
)
from .trie import Trie, root as trie_root, trie_set


@slotted_freezable
@dataclass
class ExecutionPayloadV1:
    """
    Execution payload for engine_newPayloadV1 (Paris/The Merge).

    Contains all data needed to execute a block, received from the
    consensus layer. The transactions field contains RLP-encoded
    transaction bytes, not decoded Transaction objects.
    """

    parent_hash: Hash32
    """Hash of the parent block."""

    fee_recipient: Address
    """Address to receive priority fees (coinbase)."""

    state_root: Root
    """Claimed state root after execution."""

    receipts_root: Root
    """Claimed receipts trie root."""

    logs_bloom: Bloom
    """Claimed logs bloom filter."""

    prev_randao: Bytes32
    """RANDAO value from beacon chain."""

    block_number: Uint
    """Block number (height)."""

    gas_limit: Uint
    """Maximum gas for this block."""

    gas_used: Uint
    """Claimed gas used by all transactions."""

    timestamp: U256
    """Block timestamp."""

    extra_data: Bytes
    """Arbitrary extra data (max 32 bytes)."""

    base_fee_per_gas: Uint
    """Base fee per gas for EIP-1559."""

    block_hash: Hash32
    """Claimed block hash."""

    transactions: Tuple[Bytes, ...]
    """RLP-encoded transactions."""


@slotted_freezable
@dataclass
class NewPayloadRequestV1:
    """
    Request wrapper for engine_newPayloadV1.

    For V1, this simply wraps the payload. Later versions add
    additional parameters like expected blob hashes.
    """

    payload: ExecutionPayloadV1


@slotted_freezable
@dataclass
class Valid:
    """
    Successful validation result with computed values.

    Contains all values computed during payload execution,
    which have been verified to match the payload's claims.
    """

    state_root: Root
    """Computed state root after execution."""

    receipts_root: Root
    """Computed receipts trie root."""

    logs_bloom: Bloom
    """Computed logs bloom filter."""

    gas_used: Uint
    """Computed total gas used."""


class ValidationError(EthereumException):
    """
    Base class for all payload validation errors.

    Subclasses represent specific validation failures that can occur
    during engine_newPayload processing.
    """

    pass


class InvalidBlockHash(ValidationError):
    """
    The payload's block_hash doesn't match keccak256(rlp(header)).

    This is an instant validation failure - checked before execution.
    """

    pass


class InvalidTransactionEncoding(ValidationError):
    """
    A transaction in the payload failed to decode or is empty.

    This is an instant validation failure - checked before execution.
    """

    pass


class InvalidGasUsed(ValidationError):
    """
    Computed gas_used doesn't match the payload's claimed gas_used.
    """

    expected: Uint
    actual: Uint

    def __init__(self, expected: Uint, actual: Uint) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(f"gas used mismatch: expected {expected}, got {actual}")


class InvalidStateRoot(ValidationError):
    """
    Computed state_root doesn't match the payload's claimed state_root.
    """

    pass


class InvalidReceiptsRoot(ValidationError):
    """
    Computed receipts_root doesn't match the payload's claimed receipts_root.
    """

    pass


class InvalidLogsBloom(ValidationError):
    """
    Computed logs_bloom doesn't match the payload's claimed logs_bloom.
    """

    pass


def compute_transactions_root(transactions: Tuple[Bytes, ...]) -> Root:
    """
    Compute the transactions trie root from raw transaction bytes.

    Parameters
    ----------
    transactions :
        RLP-encoded transaction bytes.

    Returns
    -------
    transactions_root :
        The root hash of the transactions trie.
    """
    trie: Trie[Bytes, Bytes] = Trie(secured=False, default=b"")
    for i, tx_bytes in enumerate(transactions):
        trie_set(trie, rlp.encode(Uint(i)), tx_bytes)
    return trie_root(trie)


def payload_to_header(payload: ExecutionPayloadV1) -> Header:
    """
    Construct a block Header from an ExecutionPayload.

    This is used to verify the payload's block_hash claim by computing
    keccak256(rlp(header)) and comparing.

    Parameters
    ----------
    payload :
        The execution payload to convert.

    Returns
    -------
    header :
        A Header with fields populated from the payload.
    """
    transactions_root = compute_transactions_root(payload.transactions)

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
    )


def verify_block_hash(payload: ExecutionPayloadV1) -> Optional[InvalidBlockHash]:
    """
    Verify the payload's block_hash matches the computed header hash.

    This is an instant validation that runs before execution.

    Parameters
    ----------
    payload :
        The execution payload to verify.

    Returns
    -------
    error :
        None if valid, InvalidBlockHash if the hash doesn't match.
    """
    header = payload_to_header(payload)
    computed_hash = keccak256(rlp.encode(header))

    if computed_hash != payload.block_hash:
        return InvalidBlockHash(
            f"block hash mismatch: expected {computed_hash.hex()}, "
            f"got {payload.block_hash.hex()}"
        )

    return None


def decode_transactions(
    raw_transactions: Tuple[Bytes, ...]
) -> Optional[InvalidTransactionEncoding]:
    """
    Validate that all transactions can be decoded.

    This is an instant validation - runs before execution.
    Each transaction must be non-empty and successfully decode.

    Per EIP-2718, transactions in the Engine API are raw bytes where:
    - First byte >= 0xc0: RLP-encoded legacy transaction
    - First byte < 0x7f: Typed transaction (type prefix + payload)

    Parameters
    ----------
    raw_transactions :
        Tuple of RLP-encoded transaction bytes.

    Returns
    -------
    error :
        None if all valid, InvalidTransactionEncoding on first failure.
    """
    for i, tx_bytes in enumerate(raw_transactions):
        if len(tx_bytes) == 0:
            return InvalidTransactionEncoding(
                f"transaction {i} is empty"
            )
        try:
            # Per EIP-2718: first byte >= 0xc0 means RLP list (legacy tx)
            if tx_bytes[0] >= 0xC0:
                rlp.decode_to(LegacyTransaction, tx_bytes)
            else:
                decode_transaction(tx_bytes)
        except Exception as e:
            return InvalidTransactionEncoding(
                f"transaction {i} failed to decode: {e}"
            )

    return None


ValidationResult = Union[Valid, ValidationError]


def validate_execution_payload(
    request: NewPayloadRequestV1,
    parent_header: Header,
    state: State,
    chain_id: U64,
    block_hashes: List[Hash32],
) -> ValidationResult:
    """
    Validate an execution payload.

    This is the core validation function for engine_newPayloadV1.
    It performs instant checks (block hash, transaction encoding) and
    then executes the payload to verify computed values match claims.

    Parameters
    ----------
    request :
        The newPayload request containing the execution payload.
    parent_header :
        Header of the parent block.
    state :
        Pre-state to execute against (will be modified).
    chain_id :
        Chain ID for transaction signature verification.
    block_hashes :
        Recent block hashes for BLOCKHASH opcode.

    Returns
    -------
    result :
        Valid with computed values, or a ValidationError subtype.
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

    # Step 3: Execute payload
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

    # Step 5: Return Valid with computed values
    return Valid(
        state_root=computed_state_root,
        receipts_root=computed_receipts_root,
        logs_bloom=computed_logs_bloom,
        gas_used=computed_gas_used,
    )
