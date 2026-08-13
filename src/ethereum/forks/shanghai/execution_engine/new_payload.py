"""
The `engine_newPayload` family of methods.

Each version is a thin wrapper carrying its own validity rules; the
shared [`verify_and_notify_new_payload`] core validates and executes
the payload on the branch of its parent. A new payload never moves the
canonical head — only a forkchoice update does.

[`verify_and_notify_new_payload`]:
    ref:ethereum.forks.shanghai.execution_engine.new_payload.verify_and_notify_new_payload
"""  # noqa: E501


from ethereum_rlp import rlp

from ethereum.crypto.hash import keccak256
from ethereum.exceptions import (
    EthereumException,
    UnsupportedForkError,
)

from ..fork import state_transition
from .types import (
    ExecutionEngine,
    ExecutionPayloadV1,
    ExecutionPayloadV2,
    PayloadStatus,
    PayloadStatusV1,
)
from .validation_helpers import _payload_block, _payload_header, chain_of


def is_valid_block_hash(
    execution_payload: ExecutionPayloadV2,
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
        # Any decoding or conversion failure means the payload cannot
        # produce a valid header.
        return False
    return keccak256(rlp.encode(header)) == execution_payload.block_hash


def verify_and_notify_new_payload(
    engine: ExecutionEngine,
    execution_payload: ExecutionPayloadV2,
) -> PayloadStatusV1:
    """
    Validate and execute a payload; remember it when valid.

    The payload must reproduce its declared block hash. A payload whose parent is unknown cannot be
    validated and reports `SYNCING`. Otherwise the block is executed on
    the branch of its parent — re-built from genesis, since only
    canonical state is kept — and recorded on success. The canonical
    head does not change; [`notify_forkchoice_updated`] moves it.

    [`notify_forkchoice_updated`]:
        ref:ethereum.forks.shanghai.execution_engine.forkchoice_update.notify_forkchoice_updated
    """  # noqa: E501
    if b"" in execution_payload.transactions:
        return PayloadStatusV1(
            status=PayloadStatus.INVALID,
            latest_valid_hash=None,
            validation_error="empty transaction in payload",
        )

    if not is_valid_block_hash(
        execution_payload,
    ):
        return PayloadStatusV1(
            status=PayloadStatus.INVALID,
            latest_valid_hash=None,
            validation_error="invalid block hash",
        )

    if execution_payload.parent_hash not in engine.validated_blocks:
        return PayloadStatusV1(
            status=PayloadStatus.SYNCING,
            latest_valid_hash=None,
            validation_error=None,
        )

    block = _payload_block(
        execution_payload,
    )
    branch = chain_of(engine, execution_payload.parent_hash)
    try:
        state_transition(branch, block)
    except EthereumException as e:
        return PayloadStatusV1(
            status=PayloadStatus.INVALID,
            latest_valid_hash=execution_payload.parent_hash,
            validation_error=f"{type(e).__name__}: {e}",
        )

    engine.validated_blocks[execution_payload.block_hash] = block
    engine.states[execution_payload.block_hash] = branch.state
    return PayloadStatusV1(
        status=PayloadStatus.VALID,
        latest_valid_hash=execution_payload.block_hash,
        validation_error=None,
    )


def new_payload_v1(
    _engine: ExecutionEngine,
    _execution_payload: ExecutionPayloadV1,
) -> PayloadStatusV1:
    """
    `engine_newPayloadV1` serves forks before Shanghai; once Shanghai is
    active it must not be used.
    """
    raise UnsupportedForkError(
        "engine_newPayloadV1 does not serve the active fork"
    )


def new_payload_v2(
    engine: ExecutionEngine,
    execution_payload: ExecutionPayloadV2,
) -> PayloadStatusV1:
    """
    `engine_newPayloadV2`: validate and execute a Shanghai payload.
    """
    return verify_and_notify_new_payload(
        engine,
        execution_payload,
    )
