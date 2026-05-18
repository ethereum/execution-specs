"""Types used in the RPC module for `eth` and `engine` namespaces' requests."""

import json
from binascii import crc32
from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from typing import Annotated, Any, Dict, List, Protocol, Self

import ethereum_rlp as eth_rlp
from pydantic import AliasChoices, BaseModel, Field, model_validator
from remerkleable.basic import uint8
from remerkleable.byte_arrays import ByteList, ByteVector
from remerkleable.complex import Container
from remerkleable.complex import List as SszList
from remerkleable.union import Union as SszUnion

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
from execution_testing.test_types import EOA, Transaction, Withdrawal
from execution_testing.test_types.execution_witness import ExecutionWitness


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
            BlockTransactionExceptionWithMessage | UndefinedException,
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


# SSZ schema for the REST POST /new-payload-with-witness response.

VALIDATION_ERROR_MAX = 8192
MAX_WITNESS_BYTES = 2**30  # 1 GiB
MAX_WITNESS_ITEMS = 2**20
MAX_WITNESS_ITEM_BYTES = 2**20


class _SszExecutionWitness(Container):
    state: SszList[ByteList[MAX_WITNESS_ITEM_BYTES], MAX_WITNESS_ITEMS]
    codes: SszList[ByteList[MAX_WITNESS_ITEM_BYTES], MAX_WITNESS_ITEMS]
    headers: SszList[ByteList[MAX_WITNESS_ITEM_BYTES], MAX_WITNESS_ITEMS]


class _SszNewPayloadWithWitnessResponse(Container):
    status: uint8
    latest_valid_hash: SszUnion[None, ByteVector[32]]
    validation_error: SszUnion[None, ByteList[VALIDATION_ERROR_MAX]]
    witness: ByteList[MAX_WITNESS_BYTES]


_SSZ_STATUS_TO_ENUM: Dict[int, PayloadStatusEnum] = {
    0: PayloadStatusEnum.VALID,
    1: PayloadStatusEnum.INVALID,
    2: PayloadStatusEnum.SYNCING,
    3: PayloadStatusEnum.ACCEPTED,
    4: PayloadStatusEnum.INVALID_BLOCK_HASH,
}


@dataclass
class NewPayloadWithWitnessResponse:
    """
    Decoded response of POST /new-payload-with-witness.

    The witness field is ``None`` whenever status is not ``VALID`` (the spec
    mandates an empty SSZ witness in that case).
    """

    status: PayloadStatusEnum
    latest_valid_hash: Hash | None
    validation_error: str | None
    witness: ExecutionWitness | None = field(default=None)

    @classmethod
    def from_ssz_bytes(cls, data: bytes) -> Self:
        """Decode an SSZ-encoded NewPayloadWithWitnessResponseV1 body."""
        resp = _SszNewPayloadWithWitnessResponse.decode_bytes(data)

        status_int = int(resp.status)
        try:
            status = _SSZ_STATUS_TO_ENUM[status_int]
        except KeyError as e:
            raise ValueError(f"Unknown SSZ status byte: {status_int}") from e

        latest_valid_hash: Hash | None = None
        if resp.latest_valid_hash.selector() == 1:
            latest_valid_hash = Hash(bytes(resp.latest_valid_hash.value()))

        validation_error: str | None = None
        if resp.validation_error.selector() == 1:
            raw = bytes(resp.validation_error.value())
            validation_error = raw.decode("utf-8", errors="replace")

        witness: ExecutionWitness | None = None
        witness_bytes = bytes(resp.witness)
        if witness_bytes:
            inner = _SszExecutionWitness.decode_bytes(witness_bytes)
            witness = ExecutionWitness(
                state=[Bytes(bytes(x)) for x in inner.state],
                codes=[Bytes(bytes(x)) for x in inner.codes],
                headers=[Bytes(bytes(x)) for x in inner.headers],
            )

        return cls(
            status=status,
            latest_valid_hash=latest_valid_hash,
            validation_error=validation_error,
            witness=witness,
        )

    @classmethod
    def from_geth_json(cls, data: Dict[str, Any]) -> Self:
        """
        Decode geth's JSON-RPC `engine_newPayloadWithWitnessVX` response.

        The `witness` field is a hex-encoded RLP list
        `[Headers, Codes, State, Keys]` where Headers are RLP-encoded header
        structures. Re-encode each header to RLP bytes so the resulting
        ExecutionWitness has the same `headers: List[Bytes]` shape as the
        fixture.
        """
        status = PayloadStatusEnum(data["status"])

        raw_hash = data.get("latestValidHash")
        latest_valid_hash: Hash | None = (
            Hash(raw_hash) if raw_hash is not None else None
        )

        raw_err = data.get("validationError")
        validation_error: str | None = raw_err if raw_err is not None else None

        witness: ExecutionWitness | None = None
        raw_witness = data.get("witness")
        if raw_witness is not None:
            witness_bytes = (
                bytes.fromhex(raw_witness[2:])
                if isinstance(raw_witness, str)
                else bytes(raw_witness)
            )
            if witness_bytes:
                parsed = eth_rlp.decode(witness_bytes)
                if not isinstance(parsed, list) or len(parsed) < 3:
                    raise ValueError(
                        "Unexpected geth ExtWitness RLP structure: "
                        f"{type(parsed).__name__} of length "
                        f"{len(parsed) if isinstance(parsed, list) else 0}"
                    )
                headers_raw, codes_raw, state_raw = parsed[0:3]
                witness = ExecutionWitness(
                    state=[Bytes(bytes(x)) for x in state_raw],
                    codes=[Bytes(bytes(x)) for x in codes_raw],
                    headers=[Bytes(eth_rlp.encode(h)) for h in headers_raw],
                )

        return cls(
            status=status,
            latest_valid_hash=latest_valid_hash,
            validation_error=validation_error,
            witness=witness,
        )


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
