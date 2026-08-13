"""
The [Engine API] under the BPO3 fork.

The consensus layer drives the execution layer through versioned
methods — `engine_newPayloadV1`…`V4`, `engine_forkchoiceUpdatedV1`…`V3`, `engine_getPayloadV1`…`V5` — each a thin
wrapper over the shared validation and forkchoice cores. Versions are
additive: every version up to the newest exists here, and versions
superseded by BPO3 answer with an unsupported-fork error, so this
module is the complete engine surface a BPO3 client presents.

[Engine API]: https://github.com/ethereum/execution-apis/blob/main/src/engine/osaka.md
"""  # noqa: E501

from .forkchoice_update import (
    forkchoice_updated_v1,
    forkchoice_updated_v2,
    forkchoice_updated_v3,
    notify_forkchoice_updated,
)
from .get_payload import (
    get_payload_v1,
    get_payload_v2,
    get_payload_v3,
    get_payload_v4,
    get_payload_v5,
)
from .new_payload import (
    is_valid_block_hash,
    is_valid_versioned_hashes,
    new_payload_v1,
    new_payload_v2,
    new_payload_v3,
    new_payload_v4,
    verify_and_notify_new_payload,
)
from .types import (
    BlobsBundleV1,
    BlobsBundleV2,
    ExecutionEngine,
    ExecutionPayloadV1,
    ExecutionPayloadV2,
    ExecutionPayloadV3,
    ForkchoiceStateV1,
    ForkchoiceUpdatedResponse,
    GetPayloadResponseV2,
    GetPayloadResponseV3,
    GetPayloadResponseV4,
    GetPayloadResponseV5,
    PayloadAttributesV1,
    PayloadAttributesV2,
    PayloadAttributesV3,
    PayloadId,
    PayloadStatus,
    PayloadStatusV1,
    create_execution_engine,
)

__all__ = [
    "BlobsBundleV1",
    "BlobsBundleV2",
    "ExecutionEngine",
    "ExecutionPayloadV1",
    "ExecutionPayloadV2",
    "ExecutionPayloadV3",
    "ForkchoiceStateV1",
    "ForkchoiceUpdatedResponse",
    "GetPayloadResponseV2",
    "GetPayloadResponseV3",
    "GetPayloadResponseV4",
    "GetPayloadResponseV5",
    "PayloadAttributesV1",
    "PayloadAttributesV2",
    "PayloadAttributesV3",
    "PayloadId",
    "PayloadStatus",
    "PayloadStatusV1",
    "create_execution_engine",
    "forkchoice_updated_v1",
    "forkchoice_updated_v2",
    "forkchoice_updated_v3",
    "get_payload_v1",
    "get_payload_v2",
    "get_payload_v3",
    "get_payload_v4",
    "get_payload_v5",
    "is_valid_block_hash",
    "is_valid_versioned_hashes",
    "new_payload_v1",
    "new_payload_v2",
    "new_payload_v3",
    "new_payload_v4",
    "notify_forkchoice_updated",
    "verify_and_notify_new_payload",
]
