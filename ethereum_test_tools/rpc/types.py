"""
Types used in the RPC module for `eth` and `engine` namespaces' requests.
"""

from enum import Enum

from pydantic import Field

from ethereum_test_base_types import CamelModel, Hash, HexNumber


class ForkchoiceState(CamelModel):
    """
    Represents the forkchoice state of the beacon chain.
    """

    head_block_hash: Hash = Field(Hash(0))
    safety_block_hash: Hash = Field(Hash(0))
    justified_block_hash: Hash = Field(Hash(0))


class PayloadStatusEnum(str, Enum):
    """
    Represents the status of a payload after execution.
    """

    VALID = "VALID"
    INVALID = "INVALID"
    SYNCING = "SYNCING"
    ACCEPTED = "ACCEPTED"
    INVALID_BLOCK_HASH = "INVALID_BLOCK_HASH"


class PayloadStatus(CamelModel):
    """
    Represents the status of a payload after execution.
    """

    status: PayloadStatusEnum
    latest_valid_hash: Hash | None
    validation_error: str | None


class ForkchoiceUpdateResponse(CamelModel):
    """
    Represents the response of a forkchoice update.
    """

    payload_status: PayloadStatus
    payload_id: HexNumber | None
