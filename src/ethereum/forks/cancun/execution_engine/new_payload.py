"""
Payload verification and execution.
"""


from ethereum_rlp import rlp

from ethereum.crypto.hash import keccak256
from ethereum.exceptions import EthereumException
from ethereum.state import Root

from ..fork import state_transition
from ..fork_types import VersionedHash
from ..transactions import (
    BlobTransaction,
    LegacyTransaction,
    decode_transaction,
)
from .types import ExecutionEngine, ExecutionPayload, NewPayloadRequest
from .validation_helpers import _payload_block, _payload_header


def is_valid_block_hash(
    execution_payload: ExecutionPayload,
    parent_beacon_block_root: Root,
) -> bool:
    """
    Return `True` if and only if `execution_payload.block_hash` is
    computed correctly.
    """
    try:
        header = _payload_header(
            execution_payload,
            parent_beacon_block_root,
        )
    except Exception:
        # Any decoding or conversion failure means the payload
        # cannot produce a valid header.
        return False
    return keccak256(rlp.encode(header)) == execution_payload.block_hash


def is_valid_versioned_hashes(
    new_payload_request: NewPayloadRequest,
) -> bool:
    """
    Return `True` if and only if the versioned hashes computed by blob
    transactions in `new_payload_request.execution_payload` match
    `new_payload_request.versioned_hashes`.
    """
    computed_versioned_hashes: list[VersionedHash] = []

    try:
        for encoded_tx in new_payload_request.execution_payload.transactions:
            if encoded_tx and encoded_tx[0] >= 0xC0:
                tx: object = rlp.decode_to(LegacyTransaction, encoded_tx)
            else:
                tx = decode_transaction(encoded_tx)
            if isinstance(tx, BlobTransaction):
                computed_versioned_hashes.extend(tx.blob_versioned_hashes)
    except Exception:
        # Any decoding failure means versioned hashes cannot be
        # verified.
        return False

    return tuple(computed_versioned_hashes) == (
        new_payload_request.versioned_hashes
    )


def notify_new_payload(
    chain: ExecutionEngine,
    new_payload_request: NewPayloadRequest,
) -> bool:
    """
    Execute the payload against the chain head and return `True` if and
    only if it forms a valid block.

    The payload is converted into a [`Block`] and applied with
    [`state_transition`], which appends it to the chain on success.

    [`Block`]: ref:ethereum.forks.cancun.blocks.Block
    [`state_transition`]: ref:ethereum.forks.cancun.fork.state_transition
    """
    block = _payload_block(
        new_payload_request.execution_payload,
        new_payload_request.parent_beacon_block_root,
    )

    try:
        state_transition(chain, block)
    except EthereumException:
        return False

    return True


def verify_and_notify_new_payload(
    chain: ExecutionEngine,
    new_payload_request: NewPayloadRequest,
) -> bool:
    """
    Validate the payload and, if valid, apply it to the chain.

    Mirrors the consensus-layer `verify_and_notify_new_payload` method
    of the `ExecutionEngine`: the payload must carry a correctly
    computed `block_hash` and matching blob versioned hashes before it
    is executed by [`notify_new_payload`].

    [`notify_new_payload`]:
        ref:ethereum.forks.cancun.execution_engine.new_payload.notify_new_payload
    """  # noqa: E501
    payload = new_payload_request.execution_payload

    if b"" in payload.transactions:
        return False

    if not is_valid_block_hash(
        payload,
        new_payload_request.parent_beacon_block_root,
    ):
        return False

    if not is_valid_versioned_hashes(new_payload_request):
        return False

    return notify_new_payload(chain, new_payload_request)
