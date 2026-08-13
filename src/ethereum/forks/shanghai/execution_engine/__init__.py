"""
The [Engine API] under the Shanghai fork.

The consensus layer drives the execution layer through versioned
methods — `engine_newPayloadV1`…`V2`, `engine_forkchoiceUpdatedV1`…`V2`, `engine_getPayloadV1`…`V2` — each a thin
wrapper over the shared validation and forkchoice cores. Versions are
additive: every version up to the newest exists here, and versions
superseded by Shanghai answer with an unsupported-fork error, so this
module is the complete engine surface a Shanghai client presents.

[Engine API]: https://github.com/ethereum/execution-apis/blob/main/src/engine/shanghai.md
"""  # noqa: E501

from .forkchoice_update import (
    forkchoice_updated_v1,
    forkchoice_updated_v2,
    notify_forkchoice_updated,
)
from .get_payload import (
    get_payload_v1,
    get_payload_v2,
)
from .new_payload import (
    is_valid_block_hash,
    new_payload_v1,
    new_payload_v2,
    verify_and_notify_new_payload,
)
from .types import (
    ExecutionEngine,
    ExecutionPayloadV1,
    ExecutionPayloadV2,
    ForkchoiceStateV1,
    ForkchoiceUpdatedResponse,
    GetPayloadResponseV2,
    PayloadAttributesV1,
    PayloadAttributesV2,
    PayloadId,
    PayloadStatus,
    PayloadStatusV1,
    create_execution_engine,
)

__all__ = [
    "ExecutionEngine",
    "ExecutionPayloadV1",
    "ExecutionPayloadV2",
    "ForkchoiceStateV1",
    "ForkchoiceUpdatedResponse",
    "GetPayloadResponseV2",
    "PayloadAttributesV1",
    "PayloadAttributesV2",
    "PayloadId",
    "PayloadStatus",
    "PayloadStatusV1",
    "create_execution_engine",
    "forkchoice_updated_v1",
    "forkchoice_updated_v2",
    "get_payload_v1",
    "get_payload_v2",
    "is_valid_block_hash",
    "new_payload_v1",
    "new_payload_v2",
    "notify_forkchoice_updated",
    "verify_and_notify_new_payload",
]
