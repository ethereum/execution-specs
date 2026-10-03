"""
Execution Engine.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

The execution engine is the interface defined by the consensus layer
in the consensus-specs for calling the execution layer.
It provides methods for the consensus-specs to verify and apply
new payloads to the execution layer state.

These methods correspond to the ``ExecutionEngine`` abstraction in the
consensus-specs and can change over forks.
"""

from .forkchoice_update import notify_forkchoice_updated
from .get_payload import get_payload
from .new_payload import (
    is_valid_block_hash,
    is_valid_versioned_hashes,
    verify_and_notify_new_payload,
)
from .types import (
    BlobsBundle,
    ExecutionEngine,
    ExecutionPayload,
    ExecutionRequests,
    GetPayloadResponse,
    NewPayloadRequest,
    PayloadAttributes,
    PayloadId,
)

__all__ = [
    "BlobsBundle",
    "ExecutionEngine",
    "ExecutionPayload",
    "ExecutionRequests",
    "GetPayloadResponse",
    "NewPayloadRequest",
    "PayloadAttributes",
    "PayloadId",
    "get_payload",
    "is_valid_block_hash",
    "is_valid_versioned_hashes",
    "notify_forkchoice_updated",
    "verify_and_notify_new_payload",
]
