"""
The [Engine API] under the Amsterdam fork.

The consensus layer drives the execution layer through versioned
methods — `engine_newPayloadV1`…`V6`, `engine_forkchoiceUpdatedV1`…`V4`, `engine_getPayloadV1`…`V7`, `engine_notifyBlockAccessListV1` — each a thin
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
    get_payload_v7,
)
from .new_payload import (
    is_valid_block_hash,
    is_valid_versioned_hashes,
    new_payload_v1,
    new_payload_v2,
    new_payload_v3,
    new_payload_v4,
    new_payload_v5,
    new_payload_v6,
    validate_execution_requests,
    verify_and_notify_new_payload,
)
from .notify_block_access_list import notify_block_access_list_v1
from .types import (
    BlobsBundleV1,
    BlobsBundleV2,
    ExecutionEngine,
    ExecutionPayloadV1,
    ExecutionPayloadV2,
    ExecutionPayloadV3,
    ExecutionPayloadV4,
    ExecutionPayloadV5,
    ForkchoiceStateV1,
    ForkchoiceUpdatedResponse,
    GetPayloadResponseV2,
    GetPayloadResponseV3,
    GetPayloadResponseV4,
    GetPayloadResponseV5,
    GetPayloadResponseV6,
    GetPayloadResponseV7,
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
    "ExecutionPayloadV5",
    "ForkchoiceStateV1",
    "ForkchoiceUpdatedResponse",
    "GetPayloadResponseV2",
    "GetPayloadResponseV3",
    "GetPayloadResponseV4",
    "GetPayloadResponseV5",
    "GetPayloadResponseV6",
    "GetPayloadResponseV7",
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
    "get_payload_v7",
    "is_valid_block_hash",
    "is_valid_versioned_hashes",
    "new_payload_v1",
    "new_payload_v2",
    "new_payload_v3",
    "new_payload_v4",
    "new_payload_v5",
    "new_payload_v6",
    "notify_block_access_list_v1",
    "notify_forkchoice_updated",
    "validate_execution_requests",
    "verify_and_notify_new_payload",
]
