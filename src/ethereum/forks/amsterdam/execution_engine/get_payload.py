"""
The `engine_getPayload` family of methods.

Payload building is outside this specification; the method signatures
and response structures document the interface.
"""

from .types import (
    ExecutionPayloadV1,
    GetPayloadResponseV2,
    GetPayloadResponseV3,
    GetPayloadResponseV4,
    GetPayloadResponseV5,
    GetPayloadResponseV6,
    GetPayloadResponseV7,
    PayloadId,
)


def get_payload_v1(_payload_id: PayloadId) -> ExecutionPayloadV1:
    """
    `engine_getPayloadV1`: return a payload built for a previously
    returned [`PayloadId`]. Payload building is not implemented.

    [`PayloadId`]:
        ref:ethereum.forks.amsterdam.execution_engine.types.PayloadId
    """
    raise NotImplementedError


def get_payload_v2(_payload_id: PayloadId) -> GetPayloadResponseV2:
    """
    `engine_getPayloadV2`: return a payload built for a previously
    returned [`PayloadId`]. Payload building is not implemented.

    [`PayloadId`]:
        ref:ethereum.forks.amsterdam.execution_engine.types.PayloadId
    """
    raise NotImplementedError


def get_payload_v3(_payload_id: PayloadId) -> GetPayloadResponseV3:
    """
    `engine_getPayloadV3`: return a payload built for a previously
    returned [`PayloadId`]. Payload building is not implemented.

    [`PayloadId`]:
        ref:ethereum.forks.amsterdam.execution_engine.types.PayloadId
    """
    raise NotImplementedError


def get_payload_v4(_payload_id: PayloadId) -> GetPayloadResponseV4:
    """
    `engine_getPayloadV4`: return a payload built for a previously
    returned [`PayloadId`]. Payload building is not implemented.

    [`PayloadId`]:
        ref:ethereum.forks.amsterdam.execution_engine.types.PayloadId
    """
    raise NotImplementedError


def get_payload_v5(_payload_id: PayloadId) -> GetPayloadResponseV5:
    """
    `engine_getPayloadV5`: return a payload built for a previously
    returned [`PayloadId`]. Payload building is not implemented.

    [`PayloadId`]:
        ref:ethereum.forks.amsterdam.execution_engine.types.PayloadId
    """
    raise NotImplementedError


def get_payload_v6(_payload_id: PayloadId) -> GetPayloadResponseV6:
    """
    `engine_getPayloadV6`: return a payload built for a previously
    returned [`PayloadId`]. Payload building is not implemented.

    [`PayloadId`]:
        ref:ethereum.forks.amsterdam.execution_engine.types.PayloadId
    """
    raise NotImplementedError


def get_payload_v7(_payload_id: PayloadId) -> GetPayloadResponseV7:
    """
    `engine_getPayloadV7`: return a payload built for a previously
    returned [`PayloadId`], with its block access list beside it.
    Payload building is not implemented.

    [`PayloadId`]:
        ref:ethereum.forks.amsterdam.execution_engine.types.PayloadId
    """
    raise NotImplementedError
