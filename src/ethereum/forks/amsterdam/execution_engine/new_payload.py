"""
Payload verification.
"""

from typing import Sequence, Tuple

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes

from ethereum.crypto.hash import keccak256

from ..fork import state_transition
from ..fork_types import Root, VersionedHash
from ..transactions import BlobTransaction, decode_transaction
from ..trie import copy_trie
from .types import ExecutionEngine, ExecutionPayload, NewPayloadRequest
from .validation_helpers import _payload_block, _payload_header


def is_valid_block_hash(
    execution_payload: ExecutionPayload,
    parent_beacon_block_root: Root,
    execution_requests_list: Sequence[bytes],
) -> bool:
    """
    Return ``True`` if and only if ``execution_payload.block_hash`` is
    computed correctly.
    """
    try:
        header = _payload_header(
            execution_payload,
            parent_beacon_block_root,
            tuple(execution_requests_list),
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


def notify_new_payload(
    chain: ExecutionEngine,
    execution_payload: ExecutionPayload,
    parent_beacon_block_root: Root,
    execution_requests: Tuple[Bytes, ...],
) -> bool:
    """
    Execute a payload by converting it to an execution-layer block
    and applying the fork's canonical ``state_transition``.

    On success, keep the applied state and appended block.
    On failure, restore state and block history snapshots and return ``False``.
    """
    # TODO: Create snapshots, so we can rollback.
    # This is inefficient. Check if we can remove this
    # or how the rest of the code handles partial mutation
    # when the block is invalid.
    state_main_trie_snapshot = copy_trie(chain.state._main_trie)
    state_storage_tries_snapshot = {
        address: copy_trie(storage_trie)
        for address, storage_trie in chain.state._storage_tries.items()
    }
    created_accounts_snapshot = chain.state.created_accounts.copy()
    blocks_snapshot = list(chain.blocks)

    try:
        block = _payload_block(
            execution_payload,
            parent_beacon_block_root,
            # Note: `verify_and_notify_new_payload` calls
            #  `is_valid_block_hash` which also recomputes
            # the `execution_requests_root`. We do this to
            # stay conformant with the API from the consensus-specs.
            execution_requests,
        )
        # Note: it seems `state_transition` does not check
        # the `block_hash` in the header is correct value.
        # This is currently done in with `is_valid_block_hash`
        state_transition(chain, block)
    except Exception:
        # Any failure during state transition invalidates the
        # payload; restore pre-execution snapshots.
        chain.state._main_trie = state_main_trie_snapshot
        chain.state._storage_tries = state_storage_tries_snapshot
        chain.state.created_accounts = created_accounts_snapshot
        chain.blocks = blocks_snapshot
        return False

    return True


def verify_and_notify_new_payload(
    chain: ExecutionEngine,
    new_payload_request: NewPayloadRequest,
) -> bool:
    """
    Validate the payload and, if valid, apply it to the chain.
    """
    payload = new_payload_request.execution_payload
    parent_beacon_block_root = new_payload_request.parent_beacon_block_root
    execution_requests_list = new_payload_request.execution_requests

    if b"" in payload.transactions:
        return False

    if not is_valid_block_hash(
        payload,
        parent_beacon_block_root,
        execution_requests_list,
    ):
        return False

    if not is_valid_versioned_hashes(new_payload_request):
        return False

    if not notify_new_payload(
        chain,
        payload,
        parent_beacon_block_root,
        tuple(execution_requests_list),
    ):
        return False

    return True
