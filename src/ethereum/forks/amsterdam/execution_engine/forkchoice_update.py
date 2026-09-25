"""
Forkchoice update and payload build signal.
"""

from typing import Optional

from ethereum.crypto.hash import Hash32

from .types import (
    ExecutionEngine,
    PayloadAttributes,
    PayloadId,
)


def notify_forkchoice_updated(
    _chain: ExecutionEngine,
    _head_block_hash: Hash32,
    _safe_block_hash: Hash32,
    _finalized_block_hash: Hash32,
    _payload_attributes: Optional[PayloadAttributes],
) -> Optional[PayloadId]:
    """
    Notify the execution engine about the latest fork-choice state.
    """
    raise NotImplementedError
