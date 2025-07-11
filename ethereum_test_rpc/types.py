"""Types used in the RPC module for `eth` and `engine` namespaces' requests."""

import json
from binascii import crc32
from enum import Enum
from hashlib import sha256
from typing import Annotated, Any, Dict, List, Self

from pydantic import AliasChoices, Field, model_validator

from ethereum_test_base_types import (
    Address,
    Bytes,
    CamelModel,
    EthereumTestRootModel,
    ForkBlobSchedule,
    ForkHash,
    Hash,
    HexNumber,
)
from ethereum_test_exceptions import (
    BlockException,
    ExceptionMapperValidator,
    ExceptionWithMessage,
    TransactionException,
    UndefinedException,
)
from ethereum_test_fixtures.blockchain import FixtureExecutionPayload
from ethereum_test_types import EOA, Transaction, Withdrawal


class JSONRPCError(Exception):
    """Model to parse a JSON RPC error response."""

    code: int
    message: str

    def __init__(self, code: int | str, message: str, **kwargs):
        """Initialize the JSONRPCError."""
        self.code = int(code)
        self.message = message

    def __str__(self) -> str:
        """Return string representation of the JSONRPCError."""
        return f"JSONRPCError(code={self.code}, message={self.message})"


class TransactionByHashResponse(Transaction):
    """Represents the response of a transaction by hash request."""

    block_hash: Hash | None = None
    block_number: HexNumber | None = None

    gas_limit: HexNumber = Field(HexNumber(21_000), alias="gas")
    transaction_hash: Hash = Field(..., alias="hash")
    sender: EOA | None = Field(None, alias="from")

    # The to field can have different names in different clients, so we use AliasChoices.
    to: Address | None = Field(..., validation_alias=AliasChoices("to_address", "to", "toAddress"))

    v: HexNumber = Field(0, validation_alias=AliasChoices("v", "yParity"))  # type: ignore

    @model_validator(mode="before")
    @classmethod
    def adapt_clients_response(cls, data: Any) -> Any:
        """
        Perform modifications necessary to adapt the response returned by clients
        so it can be parsed by our model.
        """
        if isinstance(data, dict):
            if "gasPrice" in data and "maxFeePerGas" in data:
                # Keep only one of the gas price fields.
                del data["gasPrice"]
        return data

    def model_post_init(self, __context):
        """
        Check that the transaction hash returned by the client matches the one calculated by
        us.
        """
        Transaction.model_post_init(self, __context)
        assert self.transaction_hash == self.hash


class ForkchoiceState(CamelModel):
    """Represents the forkchoice state of the beacon chain."""

    head_block_hash: Hash = Field(Hash(0))
    safe_block_hash: Hash = Field(Hash(0))
    finalized_block_hash: Hash = Field(Hash(0))


class PayloadStatusEnum(str, Enum):
    """Represents the status of a payload after execution."""

    VALID = "VALID"
    INVALID = "INVALID"
    SYNCING = "SYNCING"
    ACCEPTED = "ACCEPTED"
    INVALID_BLOCK_HASH = "INVALID_BLOCK_HASH"


class BlockTransactionExceptionWithMessage(
    ExceptionWithMessage[BlockException | TransactionException]  # type: ignore
):
    """Exception returned from the execution client with a message."""

    pass


class PayloadStatus(CamelModel):
    """Represents the status of a payload after execution."""

    status: PayloadStatusEnum
    latest_valid_hash: Hash | None
    validation_error: (
        Annotated[
            BlockTransactionExceptionWithMessage | UndefinedException, ExceptionMapperValidator
        ]
        | None
    )


class ForkchoiceUpdateResponse(CamelModel):
    """Represents the response of a forkchoice update."""

    payload_status: PayloadStatus
    payload_id: Bytes | None


class PayloadAttributes(CamelModel):
    """Represents the attributes of a payload."""

    timestamp: HexNumber
    prev_randao: Hash
    suggested_fee_recipient: Address
    withdrawals: List[Withdrawal] | None = None
    parent_beacon_block_root: Hash | None = None


class BlobsBundle(CamelModel):
    """Represents the bundle of blobs."""

    commitments: List[Bytes]
    proofs: List[Bytes]
    blobs: List[Bytes]

    def blob_versioned_hashes(self, versioned_hash_version: int = 1) -> List[Hash]:
        """Return versioned hashes of the blobs."""
        versioned_hashes: List[Hash] = []
        for commitment in self.commitments:
            commitment_hash = sha256(commitment).digest()
            versioned_hash = Hash(bytes([versioned_hash_version]) + commitment_hash[1:])
            versioned_hashes.append(versioned_hash)
        return versioned_hashes


class BlobAndProofV1(CamelModel):
    """Represents a blob and single-proof structure (< Osaka)."""

    blob: Bytes
    proof: Bytes


class BlobAndProofV2(CamelModel):
    """Represents a blob and cell proof structure (>= Osaka)."""

    blob: Bytes
    proofs: List[Bytes]


class GetPayloadResponse(CamelModel):
    """Represents the response of a get payload request."""

    execution_payload: FixtureExecutionPayload
    blobs_bundle: BlobsBundle | None = None
    execution_requests: List[Bytes] | None = None


class GetBlobsResponse(EthereumTestRootModel):
    """Represents the response of a get blobs request."""

    root: List[BlobAndProofV1 | BlobAndProofV2 | None]

    def __len__(self) -> int:
        """Return the number of blobs in the response."""
        return len(self.root)

    def __getitem__(self, index: int) -> BlobAndProofV1 | BlobAndProofV2 | None:
        """Return the blob at the given index."""
        return self.root[index]


class ForkConfigBlobSchedule(CamelModel):
    """Representation of the blob schedule of a given fork."""

    target_blobs_per_block: int = Field(..., alias="target")
    max_blobs_per_block: int = Field(..., alias="max")
    base_fee_update_fraction: int

    @classmethod
    def from_fork_blob_schedule(cls, fork_blob_schedule: ForkBlobSchedule) -> Self:
        """Create a ForkConfigBlobSchedule from a ForkBlobSchedule."""
        return cls(
            target_blobs_per_block=fork_blob_schedule.target_blobs_per_block,
            max_blobs_per_block=fork_blob_schedule.max_blobs_per_block,
            base_fee_update_fraction=fork_blob_schedule.base_fee_update_fraction,
        )


class ForkConfig(CamelModel):
    """Current or next fork config information."""

    activation_time: int
    blob_schedule: ForkConfigBlobSchedule | None = None
    chain_id: HexNumber
    precompiles: Dict[Address, str]
    system_contracts: Dict[str, Address]

    def get_hash(self) -> ForkHash:
        """Return the hash of the fork config."""
        obj = self.model_dump(mode="json", by_alias=True, exclude_none=True)
        return ForkHash(crc32(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()))


class EthConfigResponse(CamelModel):
    """Response of the `eth_config` RPC endpoint."""

    current: ForkConfig
    current_hash: ForkHash
    current_fork_id: ForkHash
    next: ForkConfig | None = None
    next_hash: ForkHash | None = None
    next_fork_id: ForkHash | None = None
    last: ForkConfig | None = None
    last_hash: ForkHash | None = None
    last_fork_id: ForkHash | None = None
