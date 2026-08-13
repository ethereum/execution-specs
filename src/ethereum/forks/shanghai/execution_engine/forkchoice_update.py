"""
The `engine_forkchoiceUpdated` family of methods.

The consensus layer selects the canonical head among the validated
blocks; the safe and finalized hashes carry no execution semantics in
this model and clients use them for pruning and reorg limits.
"""

from typing import Optional

from ethereum_rlp import rlp

from ethereum.crypto.hash import Hash32, keccak256

from .types import (
    ExecutionEngine,
    ForkchoiceStateV1,
    ForkchoiceUpdatedResponse,
    PayloadAttributesV1,
    PayloadAttributesV2,
    PayloadStatus,
    PayloadStatusV1,
)
from .validation_helpers import chain_of


def notify_forkchoice_updated(
    engine: ExecutionEngine, head_block_hash: Hash32
) -> PayloadStatusV1:
    """
    Make the validated block `head_block_hash` the canonical head.

    The canonical chain becomes the ancestry of the chosen head,
    re-executed from genesis. A head that never passed payload
    validation cannot be adopted and reports `SYNCING`.
    """
    if head_block_hash not in engine.validated_blocks:
        return PayloadStatusV1(
            status=PayloadStatus.SYNCING,
            latest_valid_hash=None,
            validation_error=None,
        )

    current_head = keccak256(rlp.encode(engine.chain.blocks[-1].header))
    if head_block_hash != current_head:
        engine.chain = chain_of(engine, head_block_hash)

    return PayloadStatusV1(
        status=PayloadStatus.VALID,
        latest_valid_hash=head_block_hash,
        validation_error=None,
    )


def forkchoice_updated_v1(
    engine: ExecutionEngine,
    forkchoice_state: ForkchoiceStateV1,
    payload_attributes: Optional[PayloadAttributesV1],
) -> ForkchoiceUpdatedResponse:
    """
    `engine_forkchoiceUpdatedV1`: adopt the given head.

    Payload building (non-`None` attributes) is not implemented.
    """
    if payload_attributes is not None:
        raise NotImplementedError

    return ForkchoiceUpdatedResponse(
        payload_status=notify_forkchoice_updated(
            engine, forkchoice_state.head_block_hash
        ),
        payload_id=None,
    )


def forkchoice_updated_v2(
    engine: ExecutionEngine,
    forkchoice_state: ForkchoiceStateV1,
    payload_attributes: Optional[PayloadAttributesV2],
) -> ForkchoiceUpdatedResponse:
    """
    `engine_forkchoiceUpdatedV2`: adopt the given head.

    Payload building (non-`None` attributes) is not implemented.
    """
    if payload_attributes is not None:
        raise NotImplementedError

    return ForkchoiceUpdatedResponse(
        payload_status=notify_forkchoice_updated(
            engine, forkchoice_state.head_block_hash
        ),
        payload_id=None,
    )
