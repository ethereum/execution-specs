"""
Forkchoice update and payload build signal.
"""

from typing import Optional

from ethereum_rlp import rlp

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.state_mpt import copy_state

from ..fork import BlockChain, state_transition
from .types import (
    ExecutionEngine,
    PayloadAttributes,
    PayloadId,
)


def notify_forkchoice_updated(
    engine: ExecutionEngine,
    head_block_hash: Hash32,
    _safe_block_hash: Hash32,
    _finalized_block_hash: Hash32,
    payload_attributes: Optional[PayloadAttributes],
) -> Optional[PayloadId]:
    """
    Make the validated block `head_block_hash` the canonical head.

    The canonical chain is the ancestry of the chosen head: selecting a
    head outside the current chain rebuilds the chain by re-executing
    the head's ancestry from genesis. The consensus layer only selects
    blocks that already passed [`verify_and_notify_new_payload`].

    The safe and finalized hashes carry no execution semantics in this
    model; clients use them for pruning and reorg limits. Payload
    building (a non-`None` `payload_attributes`) is not implemented, so
    no [`PayloadId`] is ever returned.

    [`verify_and_notify_new_payload`]:
        ref:ethereum.forks.cancun.execution_engine.new_payload.verify_and_notify_new_payload
    [`PayloadId`]: ref:ethereum.forks.cancun.execution_engine.types.PayloadId
    """  # noqa: E501
    if payload_attributes is not None:
        raise NotImplementedError

    current_head = keccak256(rlp.encode(engine.chain.blocks[-1].header))
    if head_block_hash == current_head:
        return None

    branch = []
    cursor = head_block_hash
    genesis_hash = keccak256(rlp.encode(engine.genesis_block.header))
    while cursor != genesis_hash:
        block = engine.validated_blocks[cursor]
        branch.append(block)
        cursor = block.header.parent_hash

    engine.chain = BlockChain(
        blocks=[engine.genesis_block],
        state=copy_state(engine.genesis_state),
        chain_id=engine.chain.chain_id,
    )
    for block in reversed(branch):
        state_transition(engine.chain, block)
    return None
