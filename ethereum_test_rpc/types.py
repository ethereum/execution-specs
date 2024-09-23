"""
Types used in the RPC module for `eth` and `engine` namespaces' requests.
"""

from enum import Enum
from typing import List

from pydantic import Field

from ethereum_test_base_types import Address, Bytes, CamelModel, Hash, HexNumber
from ethereum_test_fixtures.blockchain import FixtureExecutionPayload
from ethereum_test_types import Withdrawal


class JSONRPCError(CamelModel):
    """
    Model to parse a JSON RPC error response.
    """

    code: int
    message: str

    def __str__(self) -> str:
        """
        Returns a string representation of the JSONRPCError.
        """
        return f"JSONRPCError(code={self.code}, message={self.message})"

    def exception(self, method) -> Exception:
        """
        Returns an exception representation of the JSONRPCError.
        """
        return Exception(
            f"Error calling JSON RPC {method}, code: {self.code}, " f"message: {self.message}"
        )


class TransactionByHashResponse(CamelModel):
    """
    Represents the response of a transaction by hash request.
    """

    block_hash: Hash | None = None
    block_number: HexNumber | None = None

    transaction_hash: Hash = Field(..., alias="hash")
    from_address: Address = Field(..., alias="from")
    to_address: Address | None = Field(..., alias="to")

    ty: HexNumber = Field(..., alias="type")
    gas_limit: HexNumber = Field(..., alias="gas")
    gas_price: HexNumber | None = None
    max_fee_per_gas: HexNumber | None = None
    max_priority_fee_per_gas: HexNumber | None = None
    value: HexNumber
    data: Bytes = Field(..., alias="input")
    nonce: HexNumber
    v: HexNumber
    r: HexNumber
    s: HexNumber


class ForkchoiceState(CamelModel):
    """
    Represents the forkchoice state of the beacon chain.
    """

    head_block_hash: Hash = Field(Hash(0))
    safe_block_hash: Hash = Field(Hash(0))
    finalized_block_hash: Hash = Field(Hash(0))


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
    payload_id: Bytes | None


class PayloadAttributes(CamelModel):
    """
    Represents the attributes of a payload.
    """

    timestamp: HexNumber
    prev_randao: Hash
    suggested_fee_recipient: Address
    withdrawals: List[Withdrawal] | None = None
    parent_beacon_block_root: Hash | None = None


class BlobsBundle(CamelModel):
    """
    Represents the bundle of blobs.
    """

    commitments: List[Bytes]
    proofs: List[Bytes]
    blobs: List[Bytes]

    def blob_versioned_hashes(self) -> List[Hash]:
        """
        Returns the versioned hashes of the blobs.
        """
        return [Hash(b"\1" + commitment[1:]) for commitment in self.commitments]


class GetPayloadResponse(CamelModel):
    """
    Represents the response of a get payload request.
    """

    execution_payload: FixtureExecutionPayload
    blobs_bundle: BlobsBundle | None = None
