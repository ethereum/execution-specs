"""
The `engine_getPayload` family of methods.

Payload building is outside this specification; the method signatures
and response structures document the interface.
"""

from .types import (
    ExecutionPayloadV1,
    PayloadId,
)


def get_payload_v1(_payload_id: PayloadId) -> ExecutionPayloadV1:
    """
    `engine_getPayloadV1`: return a payload built for a previously
    returned [`PayloadId`]. Payload building is not implemented.

    [`PayloadId`]: ref:ethereum.forks.paris.execution_engine.types.PayloadId
    """
    raise NotImplementedError
