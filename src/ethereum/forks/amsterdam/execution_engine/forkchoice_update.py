"""
Forkchoice update and payload build signal.
"""

from typing import Optional

from ethereum_rlp import rlp

from ethereum.crypto.hash import Hash32, keccak256

from ..blocks import Block
from .types import (
    _ZERO_HASH32,
    ExecutionEngine,
    PayloadAttributes,
    PayloadId,
)


def _block_hash(block: Block) -> Hash32:
    """
    Compute the hash of a block header.
    """
    return keccak256(rlp.encode(block.header))


def find_block_by_hash(
    chain: ExecutionEngine, block_hash: Hash32
) -> Optional[Block]:
    """
    Find a block in the local chain by its hash.
    """
    for block in reversed(chain.blocks):
        if _block_hash(block) == block_hash:
            return block
    return None


def notify_forkchoice_updated(
    chain: ExecutionEngine,
    head_block_hash: Hash32,
    safe_block_hash: Hash32,
    finalized_block_hash: Hash32,
    payload_attributes: Optional[PayloadAttributes],
) -> Optional[PayloadId]:
    """
    Notify the execution engine about the latest fork-choice state.
    """
    parent_block = find_block_by_hash(chain, head_block_hash)
    if parent_block is None:
        return None

    if safe_block_hash != _ZERO_HASH32:
        if find_block_by_hash(chain, safe_block_hash) is None:
            return None

    if finalized_block_hash != _ZERO_HASH32:
        if find_block_by_hash(chain, finalized_block_hash) is None:
            return None

    if payload_attributes is None:
        return None

    # TODO: Build and store a payload for later retrieval via
    # ``get_payload``.  Requires payload build state on the
    # ``ExecutionEngine`` instance.
    raise NotImplementedError
