"""
Interface between the consensus layer and the execution layer.

The consensus layer drives the execution layer through a small set of
methods defined as the `ExecutionEngine` abstraction in the
consensus-specs, carried between clients by the [Engine API]. Each new
beacon block carries an [`ExecutionPayload`] that the execution layer
validates and applies to its state with
[`verify_and_notify_new_payload`].

[Engine API]: https://github.com/ethereum/execution-apis/blob/main/src/engine/osaka.md
[`ExecutionPayload`]:
    ref:ethereum.forks.bpo4.execution_engine.types.ExecutionPayload
[`verify_and_notify_new_payload`]:
    ref:ethereum.forks.bpo4.execution_engine.new_payload.verify_and_notify_new_payload
"""  # noqa: E501

from .forkchoice_update import notify_forkchoice_updated
from .get_payload import get_payload
from .new_payload import (
    is_valid_block_hash,
    is_valid_versioned_hashes,
    notify_new_payload,
    verify_and_notify_new_payload,
)
from .types import (
    BlobsBundle,
    ExecutionEngine,
    ExecutionPayload,
    GetPayloadResponse,
    NewPayloadRequest,
    PayloadAttributes,
    PayloadId,
    create_execution_engine,
)

__all__ = [
    "BlobsBundle",
    "ExecutionEngine",
    "ExecutionPayload",
    "GetPayloadResponse",
    "NewPayloadRequest",
    "PayloadAttributes",
    "PayloadId",
    "create_execution_engine",
    "get_payload",
    "is_valid_block_hash",
    "is_valid_versioned_hashes",
    "notify_forkchoice_updated",
    "notify_new_payload",
    "verify_and_notify_new_payload",
]
