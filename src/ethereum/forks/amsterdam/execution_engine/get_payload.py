"""
Payload build storage and retrieval helpers.
"""

from .types import (
    GetPayloadResponse,
    PayloadId,
)


def get_payload(_payload_id: PayloadId) -> GetPayloadResponse:
    """
    Return a prepared payload response for a previously returned
    ``PayloadId``.
    """
    raise NotImplementedError
