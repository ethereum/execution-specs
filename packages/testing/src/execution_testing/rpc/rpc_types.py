"""Types used in the RPC module for `eth` and `engine` namespaces' requests."""

import json
from binascii import crc32
from enum import Enum
from hashlib import sha256
from typing import Annotated, Any, Dict, List, Protocol, Self

from pydantic import AliasChoices, BaseModel, Field, model_validator

from execution_testing.base_types import (
    Address,
    Bytes,
    CamelModel,
    EthereumTestRootModel,
    ForkBlobSchedule,
    ForkHash,
    Hash,
    HexNumber,
)
from execution_testing.exceptions import (
    BlockException,
    ExceptionMapperValidator,
    ExceptionWithMessage,
    TransactionException,
    UndefinedException,
)
from execution_testing.fixtures.blockchain import (
    FixtureExecutionPayload,
)
from execution_testing.forks import Fork
from execution_testing.test_types import EOA, Transaction, Withdrawal


class JSONRPCError(Exception):
    """Model to parse a JSON RPC error response."""

    code: int
    message: str
    data: str | dict | None

    def __init__(
        self, code: int | str, message: str, data: str | dict | None = None
    ) -> None:
        """Initialize the JSONRPCError."""
        self.code = int(code)
        self.message = message
        self.data = data

    def __str__(self) -> str:
        """Return string representation of the JSONRPCError."""
        if self.data is not None:
            return (
                f"JSONRPCError(code={self.code}, message={self.message}, "
                f"data={self.data})"
            )

        return f"JSONRPCError(code={self.code}, message={self.message})"


class RPCCall(BaseModel):
    """Represent a JSON-RPC method call before namespace prefixing."""

    method: str
    params: List[Any] = []
    request_id: int | str | None = None


class JSONRPCRequest(BaseModel):
    """Represent a JSON-RPC 2.0 request object."""

    jsonrpc: str = "2.0"
    method: str
    params: List[Any] = []
    id: int | str


class JSONRPCErrorObject(BaseModel):
    """Represent the error object in a JSON-RPC 2.0 response."""

    code: int
    message: str
    data: str | dict | None = None


class JSONRPCResponse(BaseModel):
    """Represent a JSON-RPC 2.0 response object."""

    jsonrpc: str = "2.0"
    id: int | str
    result: Any = None
    error: JSONRPCErrorObject | None = None

    @model_validator(mode="before")
    @classmethod
    def check_result_or_error(cls, data: Any) -> Any:
        """Validate that the response contains 'result' or 'error'."""
        if isinstance(data, dict):
            if "result" not in data and "error" not in data:
                raise ValueError(
                    "RPC response must contain 'result' or 'error'"
                )
        return data

    def result_or_raise(self) -> Any:
        """Return the result or raise JSONRPCError."""
        if self.error is not None:
            raise JSONRPCError(
                code=self.error.code,
                message=self.error.message,
                data=self.error.data,
            )
        return self.result


class TransactionByHashResponse(Transaction):
    """Represents the response of a transaction by hash request."""

    model_config = Transaction.model_config | {"extra": "ignore"}

    block_hash: Hash | None = None
    block_number: HexNumber | None = None

    gas_limit: HexNumber = Field(HexNumber(21_000), alias="gas")
    transaction_hash: Hash = Field(..., alias="hash")
    transaction_index: HexNumber | None = None
    sender: EOA | None = Field(None, alias="from")

    # The to field can have different names in different clients, so we use
    # AliasChoices.
    to: Address | None = Field(
        ..., validation_alias=AliasChoices("to_address", "to", "toAddress")
    )

    v: HexNumber = Field(0, validation_alias=AliasChoices("v", "yParity"))  # type: ignore

    @model_validator(mode="before")
    @classmethod
    def adapt_clients_response(cls, data: Any) -> Any:
        """
        Perform modifications necessary to adapt the response returned by
        clients so it can be parsed by our model.
        """
        if isinstance(data, dict):
            if "gasPrice" in data and "maxFeePerGas" in data:
                # Keep only one of the gas price fields.
                del data["gasPrice"]
        return data

    def model_post_init(self, __context: Any) -> None:
        """
        Check that the transaction hash returned by the client matches the one
        calculated by us.
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
    INCLUSION_LIST_UNSATISFIED = "INCLUSION_LIST_UNSATISFIED"


class BlockTransactionExceptionWithMessage(
    ExceptionWithMessage[BlockException | TransactionException]  # type: ignore
):
    """Exception returned from the execution client with a message."""

    pass


ClientValidationError = (
    BlockTransactionExceptionWithMessage | UndefinedException
)
"""
A client's validation error for a rejected block: the mapped exceptions
with the verbatim message, or `UndefinedException` if the message could
not be mapped.
"""


class PayloadStatus(CamelModel):
    """Represents the status of a payload after execution."""

    status: PayloadStatusEnum
    latest_valid_hash: Hash | None
    validation_error: (
        Annotated[
            ClientValidationError,
            ExceptionMapperValidator,
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
    target_blobs_per_block: HexNumber | None = None
    max_blobs_per_block: HexNumber | None = None
    slot_number: HexNumber | None = None
    target_gas_limit: HexNumber | None = None

    @classmethod
    def for_fork(
        cls,
        fork: Fork,
        *,
        timestamp: int,
        target_gas_limit: int,
        slot_number: int | None,
        prev_randao: Hash | None = None,
        suggested_fee_recipient: Address | None = None,
        withdrawals: List[Withdrawal] | None = None,
        parent_beacon_block_root: Hash | None = None,
    ) -> "PayloadAttributes":
        """
        Build PayloadAttributes with fork-aware optional fields filled in.

        ``withdrawals`` and ``parent_beacon_block_root`` default to
        fork-appropriate empty values; blob and slot fields are populated
        when the fork's engine API requires them.
        """
        if withdrawals is None and fork.header_withdrawals_required():
            withdrawals = []
        if (
            parent_beacon_block_root is None
            and fork.header_beacon_root_required()
        ):
            parent_beacon_block_root = Hash(0)
        attributes_slot_number: HexNumber | None = None
        if fork.engine_payload_attribute_slot_number():
            attributes_slot_number = HexNumber(
                1 if slot_number is None else slot_number
            )
        return cls(
            timestamp=HexNumber(timestamp),
            prev_randao=prev_randao if prev_randao is not None else Hash(0),
            suggested_fee_recipient=(
                suggested_fee_recipient
                if suggested_fee_recipient is not None
                else Address(0)
            ),
            withdrawals=withdrawals,
            parent_beacon_block_root=parent_beacon_block_root,
            target_blobs_per_block=(
                HexNumber(fork.target_blobs_per_block())
                if fork.engine_payload_attribute_target_blobs_per_block()
                else None
            ),
            max_blobs_per_block=(
                HexNumber(fork.max_blobs_per_block())
                if fork.engine_payload_attribute_max_blobs_per_block()
                else None
            ),
            slot_number=attributes_slot_number,
            target_gas_limit=(
                HexNumber(target_gas_limit)
                if fork.engine_payload_attribute_target_gas_limit()
                else None
            ),
        )


class BlobsBundle(CamelModel):
    """Represents the bundle of blobs."""

    commitments: List[Bytes]
    proofs: List[Bytes]
    blobs: List[Bytes]

    def blob_versioned_hashes(
        self, versioned_hash_version: int = 1
    ) -> List[Hash]:
        """Return versioned hashes of the blobs."""
        versioned_hashes: List[Hash] = []
        for commitment in self.commitments:
            commitment_hash = sha256(commitment).digest()
            versioned_hash = Hash(
                bytes([versioned_hash_version]) + commitment_hash[1:]
            )
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


class BlobCellsAndProofsV1(CamelModel):
    """Represents a partial cell and cell-proof structure (>= Amsterdam)."""

    blob_cells: List[Bytes | None]
    proofs: List[Bytes | None]


class GetPayloadResponse(CamelModel):
    """Represents the response of a get payload request."""

    model_config = CamelModel.model_config | {"extra": "ignore"}

    execution_payload: FixtureExecutionPayload
    blobs_bundle: BlobsBundle | None = None
    execution_requests: List[Bytes] | None = None


class GetBlobsResponse(
    EthereumTestRootModel[List[BlobAndProofV1 | BlobAndProofV2 | None]]
):
    """Represents the response of a get blobs request."""

    root: List[BlobAndProofV1 | BlobAndProofV2 | None]

    def __len__(self) -> int:
        """Return the number of blobs in the response."""
        return len(self.root)

    def __getitem__(
        self, index: int
    ) -> BlobAndProofV1 | BlobAndProofV2 | None:
        """Return the blob at the given index."""
        return self.root[index]


class GetBlobsV4Response(
    EthereumTestRootModel[List[BlobCellsAndProofsV1 | None]]
):
    """Represents the response of an `engine_getBlobsV4` request."""

    root: List[BlobCellsAndProofsV1 | None]

    def __len__(self) -> int:
        """Return the number of blob entries in the response."""
        return len(self.root)

    def __getitem__(self, index: int) -> BlobCellsAndProofsV1 | None:
        """Return the blob cell matrix at the given index."""
        return self.root[index]


class ForkConfigBlobSchedule(CamelModel):
    """Representation of the blob schedule of a given fork."""

    target_blobs_per_block: int = Field(..., alias="target")
    max_blobs_per_block: int = Field(..., alias="max")
    base_fee_update_fraction: int

    @classmethod
    def from_fork_blob_schedule(
        cls, fork_blob_schedule: ForkBlobSchedule
    ) -> Self:
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
    fork_id: ForkHash
    precompiles: Dict[str, Address]
    system_contracts: Dict[str, Address]

    def get_hash(self) -> ForkHash:
        """Return the hash of the fork config."""
        obj = self.model_dump(mode="json", by_alias=True, exclude_none=True)
        return ForkHash(
            crc32(
                json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
            )
        )


class EthConfigResponse(CamelModel):
    """Response of the `eth_config` RPC endpoint."""

    current: ForkConfig
    next: ForkConfig | None = None
    last: ForkConfig | None = None


class TransactionProtocol(Protocol):
    """Protocol for a transaction that can be sent to the client."""

    def rlp(self) -> Bytes:
        """Return the RLP of the transaction."""
        ...

    @property
    def hash(self) -> Hash:
        """Return the hash of the transaction."""
        ...

    def metadata_string(self) -> str | None:
        """Return the metadata field as a formatted json string or None."""
        ...

    def model_dump_json(self) -> str:
        """Return the transaction as a json string."""
        ...
