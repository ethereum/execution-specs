"""
Payload verification.
"""

from typing import Optional, Tuple

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes

from ethereum.crypto.hash import keccak256
from ethereum.exceptions import InvalidBlock
from ethereum.state import (
    BlockDiff,
    PreState,
    Root,
)
from ethereum.state_mpt import apply_changes_to_state

from ..blocks import Block
from ..fork import ChainContext, execute_block, get_last_256_block_hashes
from ..fork_types import VersionedHash
from ..transactions import BlobTransaction, decode_transaction
from .requests import ExecutionRequests
from .types import ExecutionEngine, ExecutionPayload, NewPayloadRequest
from .validation_helpers import _payload_block, _payload_header


def is_valid_block_hash(
    execution_payload: ExecutionPayload,
    parent_beacon_block_root: Root,
    execution_requests: ExecutionRequests,
) -> bool:
    """
    Return ``True`` if and only if ``execution_payload.block_hash`` is
    computed correctly.
    """
    try:
        header = _payload_header(
            execution_payload,
            parent_beacon_block_root,
            execution_requests,
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
    Return ``True`` if and only if the versioned hashes computed by blob
    transactions in ``new_payload_request.execution_payload`` match
    ``new_payload_request.versioned_hashes``.
    """
    computed_versioned_hashes: list[VersionedHash] = []

    try:
        for encoded_tx in new_payload_request.execution_payload.transactions:
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


def execute_new_payload_request(
    new_payload_request: NewPayloadRequest,
    pre_state: PreState,
    chain_context: ChainContext,
    transaction_public_keys: Optional[Tuple[Bytes, ...]] = None,
) -> Tuple[BlockDiff, Block]:
    """
    Validate and execute a payload against ``pre_state``.

    Note: This is conceptually similar to notify_new_payload.
    We however do not return a boolean because we want the caller
    to apply the diff and handle the case where they may need to
    rollback state on an error.

    Parameters
    ----------
    new_payload_request :
        The payload request to validate and execute.
    pre_state :
        Pre-execution state provider.
    chain_context :
        Chain context needed for block execution.
    transaction_public_keys :
        Optional transaction public keys in payload order.

    Returns
    -------
    block_diff : `BlockDiff`
        Account, storage, and code changes produced by execution.
    block : `Block`
        The block derived from the payload.

    """
    payload = new_payload_request.execution_payload
    parent_beacon_block_root = new_payload_request.parent_beacon_block_root
    execution_requests = new_payload_request.execution_requests

    if b"" in payload.transactions:
        raise InvalidBlock("Empty transaction in payload")

    if not is_valid_block_hash(
        payload,
        parent_beacon_block_root,
        execution_requests,
    ):
        raise InvalidBlock("Invalid block hash")

    if not is_valid_versioned_hashes(new_payload_request):
        raise InvalidBlock("Invalid versioned hashes")

    block = _payload_block(
        payload,
        parent_beacon_block_root,
        execution_requests,
    )
    block_diff = execute_block(
        block,
        pre_state,
        chain_context,
        transaction_public_keys=transaction_public_keys,
    )
    return block_diff, block


def verify_and_notify_new_payload(
    chain: ExecutionEngine,
    new_payload_request: NewPayloadRequest,
) -> bool:
    """
    Validate the payload and, if valid, apply it to the chain.
    """
    chain_context = ChainContext(
        chain_id=chain.chain_id,
        block_hashes=get_last_256_block_hashes(chain),
        parent_header=chain.blocks[-1].header,
    )

    try:
        # TODO: This returning a block is a bit weird
        # We could not return the block and then convert
        # the payload into a block below
        block_diff, block = execute_new_payload_request(
            new_payload_request,
            chain.state,
            chain_context,
        )
    except InvalidBlock:
        return False

    apply_changes_to_state(chain.state, block_diff)
    chain.blocks.append(block)
    if len(chain.blocks) > 255:
        chain.blocks = chain.blocks[-255:]

    return True
