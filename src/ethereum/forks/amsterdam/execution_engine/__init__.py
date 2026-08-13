"""
The [Engine API] under the Amsterdam fork.

The consensus layer drives the execution layer through versioned
methods — `engine_newPayloadV1`…`V5`, `engine_forkchoiceUpdatedV1`…`V4`, `engine_getPayloadV1`…`V6` — each a thin
wrapper over the shared validation and forkchoice cores. Versions are
additive: every version up to the newest exists here, and versions
superseded by Amsterdam answer with an unsupported-fork error, so this
module is the complete engine surface a Amsterdam client presents.

[Engine API]: https://github.com/ethereum/execution-apis/blob/main/src/engine/amsterdam.md
"""  # noqa: E501

from .forkchoice_update import (
    forkchoice_updated_v1,
    forkchoice_updated_v2,
    forkchoice_updated_v3,
    forkchoice_updated_v4,
    notify_forkchoice_updated,
)
from .get_payload import (
    get_payload_v1,
    get_payload_v2,
    get_payload_v3,
    get_payload_v4,
    get_payload_v5,
    get_payload_v6,
)
from .new_payload import (
    is_valid_block_hash,
    is_valid_versioned_hashes,
    new_payload_v1,
    new_payload_v2,
    new_payload_v3,
    new_payload_v4,
    new_payload_v5,
    validate_execution_requests,
    verify_and_notify_new_payload,
)
from .types import (
    BlobsBundleV1,
    BlobsBundleV2,
    ExecutionEngine,
    ExecutionPayloadV1,
    ExecutionPayloadV2,
    ExecutionPayloadV3,
    ExecutionPayloadV4,
    ForkchoiceStateV1,
    ForkchoiceUpdatedResponse,
    GetPayloadResponseV2,
    GetPayloadResponseV3,
    GetPayloadResponseV4,
    GetPayloadResponseV5,
    GetPayloadResponseV6,
    PayloadAttributesV1,
    PayloadAttributesV2,
    PayloadAttributesV3,
    PayloadAttributesV4,
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
    "ExecutionPayloadV4",
    "ForkchoiceStateV1",
    "ForkchoiceUpdatedResponse",
    "GetPayloadResponseV2",
    "GetPayloadResponseV3",
    "GetPayloadResponseV4",
    "GetPayloadResponseV5",
    "GetPayloadResponseV6",
    "PayloadAttributesV1",
    "PayloadAttributesV2",
    "PayloadAttributesV3",
    "PayloadAttributesV4",
    "PayloadId",
    "PayloadStatus",
    "PayloadStatusV1",
    "create_execution_engine",
    "forkchoice_updated_v1",
    "forkchoice_updated_v2",
    "forkchoice_updated_v3",
    "forkchoice_updated_v4",
    "get_payload_v1",
    "get_payload_v2",
    "get_payload_v3",
    "get_payload_v4",
    "get_payload_v5",
    "get_payload_v6",
    "is_valid_block_hash",
    "is_valid_versioned_hashes",
    "new_payload_v1",
    "new_payload_v2",
    "new_payload_v3",
    "new_payload_v4",
    "new_payload_v5",
    "notify_forkchoice_updated",
    "validate_execution_requests",
    "verify_and_notify_new_payload",
]
