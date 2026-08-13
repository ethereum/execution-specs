"""
Payload verification and execution.
"""

from ethereum_rlp import rlp

from ethereum.crypto.hash import keccak256
from ethereum.exceptions import EthereumException

from ..fork import state_transition
from .types import ExecutionEngine, ExecutionPayload, NewPayloadRequest
from .validation_helpers import _payload_block, _payload_header


def is_valid_block_hash(
    execution_payload: ExecutionPayload,
) -> bool:
    """
    Return `True` if and only if `execution_payload.block_hash` is
    computed correctly.
    """
    try:
        header = _payload_header(
            execution_payload,
        )
    except Exception:
        # Any decoding or conversion failure means the payload
        # cannot produce a valid header.
        return False
    return keccak256(rlp.encode(header)) == execution_payload.block_hash


def notify_new_payload(
    engine: ExecutionEngine,
    new_payload_request: NewPayloadRequest,
) -> bool:
    """
    Execute the payload against the chain head and return `True` if and
    only if it forms a valid block.

    The payload is converted into a [`Block`] and applied with
    [`state_transition`], which appends it to the chain on success.
    Valid blocks are remembered so a later forkchoice update can select
    them as head.

    [`Block`]: ref:ethereum.forks.shanghai.blocks.Block
    [`state_transition`]: ref:ethereum.forks.shanghai.fork.state_transition
    """
    block = _payload_block(
        new_payload_request.execution_payload,
    )

    try:
        state_transition(engine.chain, block)
    except EthereumException:
        return False

    engine.validated_blocks[keccak256(rlp.encode(block.header))] = block
    return True


def verify_and_notify_new_payload(
    engine: ExecutionEngine,
    new_payload_request: NewPayloadRequest,
) -> bool:
    """
    Validate the payload and, if valid, apply it to the chain.

    Mirrors the consensus-layer `verify_and_notify_new_payload` method
    of the `ExecutionEngine`: the payload must carry a correctly
    computed `block_hash` before it
    is executed by [`notify_new_payload`].

    [`notify_new_payload`]:
        ref:ethereum.forks.shanghai.execution_engine.new_payload.notify_new_payload
    """  # noqa: E501
    payload = new_payload_request.execution_payload

    if b"" in payload.transactions:
        return False

    if not is_valid_block_hash(
        payload,
    ):
        return False

    return notify_new_payload(engine, new_payload_request)
