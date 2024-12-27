"""Engine API error defniitions."""

from enum import IntEnum


class EngineAPIError(IntEnum):
    """List of Engine API errors."""

    ParseError = -32700
    InvalidRequest = -32600
    MethodNotFound = -32601
    InvalidParams = -32602
    InternalError = -32603
    ServerError = -32000
    UnknownPayload = -38001
    InvalidForkchoiceState = -38002
    InvalidPayloadAttributes = -38003
    TooLargeRequest = -38004
    UnsupportedFork = -38005
