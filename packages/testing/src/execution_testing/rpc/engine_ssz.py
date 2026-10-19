"""Encode REST Engine envelopes."""

from typing import Annotated, Sequence

from execution_testing.base_types import Bytes, Hash
from execution_testing.base_types.ssz import SSZForkSchema, byte_list, ssz_list
from execution_testing.fixtures.blockchain import (
    FixtureExecutionPayload,
    ForkScopedSSZModel,
)
from execution_testing.forks import Amsterdam, Fork

MAX_BAL_BYTES = 2**30
"""REST Engine API bound, independent of the fixture SSZ bound."""
MAX_BYTES_PER_EXECUTION_REQUEST = 2**30
MAX_EXECUTION_REQUESTS_PER_PAYLOAD = 256


class _RESTExecutionPayload(FixtureExecutionPayload):
    """Use the REST BAL bound with the existing payload field order."""

    block_access_list: Annotated[Bytes, byte_list(MAX_BAL_BYTES)] | None = None


class _RESTExecutionPayloadEnvelope(ForkScopedSSZModel):
    """Declare the Amsterdam REST request fields in SSZ wire order."""

    payload: _RESTExecutionPayload
    parent_beacon_block_root: Hash
    execution_requests: Annotated[
        list[Annotated[Bytes, byte_list(MAX_BYTES_PER_EXECUTION_REQUEST)]],
        ssz_list(MAX_EXECUTION_REQUESTS_PER_PAYLOAD),
    ]

    __ssz_schema__ = SSZForkSchema(
        base_fork=Amsterdam,
        base=("payload", "parent_beacon_block_root", "execution_requests"),
        appended={},
    )


def encode_witness_request(
    payload: FixtureExecutionPayload,
    parent_beacon_block_root: Hash,
    execution_requests: Sequence[Bytes],
    fork: Fork,
) -> bytes:
    """Encode the Amsterdam envelope using the REST payload schema."""
    if fork != Amsterdam:
        raise ValueError(f"Unsupported REST witness schema: {fork}")
    envelope = _RESTExecutionPayloadEnvelope(
        payload=_RESTExecutionPayload.model_validate(payload.model_dump()),
        parent_beacon_block_root=parent_beacon_block_root,
        execution_requests=list(execution_requests),
    )
    return envelope.ssz_encode(fork)
