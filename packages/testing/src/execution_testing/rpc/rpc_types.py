"""Types used in the RPC module for `eth` and `engine` namespaces' requests."""

import json
from binascii import crc32
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Annotated, Any, Dict, List, Protocol, Self

import ethereum_rlp as eth_rlp
from pydantic import AliasChoices, BaseModel, Field, model_validator
from remerkleable.basic import uint8
from remerkleable.byte_arrays import ByteList, ByteVector
from remerkleable.complex import Container
from remerkleable.complex import List as SSZList
from remerkleable.union import Union as SSZUnion

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


# SSZ schema for the REST POST /new-payload-with-witness response.

VALIDATION_ERROR_MAX = 8192
MAX_WITNESS_BYTES = 2**30  # 1 GiB
MAX_WITNESS_ITEMS = 2**20
MAX_WITNESS_ITEM_BYTES = 2**20


class _SSZExecutionWitness(Container):
    state: SSZList[ByteList[MAX_WITNESS_ITEM_BYTES], MAX_WITNESS_ITEMS]
    codes: SSZList[ByteList[MAX_WITNESS_ITEM_BYTES], MAX_WITNESS_ITEMS]
    headers: SSZList[ByteList[MAX_WITNESS_ITEM_BYTES], MAX_WITNESS_ITEMS]


class _SSZNewPayloadWithWitnessResponse(Container):
    status: uint8
    latest_valid_hash: SSZUnion[None, ByteVector[32]]
    validation_error: SSZUnion[None, ByteList[VALIDATION_ERROR_MAX]]
    witness: ByteList[MAX_WITNESS_BYTES]


class _NewPayloadWithWitnessJSONRPCResult(CamelModel):
    """JSON-RPC result for `engine_newPayloadWithWitnessVX`."""

    model_config = CamelModel.model_config | {"extra": "ignore"}

    status: PayloadStatusEnum
    latest_valid_hash: Hash | None = None
    validation_error: str | None = None
    witness: str | None = None


_SSZ_STATUS_TO_ENUM: Dict[int, PayloadStatusEnum] = {
    0: PayloadStatusEnum.VALID,
    1: PayloadStatusEnum.INVALID,
    2: PayloadStatusEnum.SYNCING,
    3: PayloadStatusEnum.ACCEPTED,
    4: PayloadStatusEnum.INVALID_BLOCK_HASH,
}


def _decode_0x_hex(value: str, field_name: str) -> bytes:
    """Decode a strict JSON-RPC hex string."""
    if not value.startswith("0x"):
        raise ValueError(f"{field_name} must be a 0x-prefixed hex string")
    hex_value = value[2:]
    if len(hex_value) % 2 != 0:
        raise ValueError(
            f"{field_name} must have an even number of hex digits"
        )
    try:
        return bytes.fromhex(hex_value)
    except ValueError as e:
        raise ValueError(f"{field_name} must be valid hex") from e


def _is_rlp_value(value: Any) -> bool:
    """Return True when value can be re-encoded as an RLP value."""
    if isinstance(value, bytes):
        return True
    if isinstance(value, list):
        return all(_is_rlp_value(item) for item in value)
    return False


def _ensure_rlp_list(value: Any, field_name: str) -> List[Any]:
    """Return an RLP list or raise a contextual error."""
    if not isinstance(value, list):
        raise ValueError(
            f"execution witness {field_name} must be an RLP list, "
            f"got {type(value).__name__}"
        )
    return value


def _bytes_list_from_rlp(value: Any, field_name: str) -> List[Bytes]:
    """Convert an RLP list of byte strings to `Bytes` values."""
    values = _ensure_rlp_list(value, field_name)
    result: List[Bytes] = []
    for index, item in enumerate(values):
        if not isinstance(item, bytes):
            raise ValueError(
                f"execution witness {field_name}[{index}] must be bytes, "
                f"got {type(item).__name__}"
            )
        result.append(Bytes(item))
    return result


def _headers_from_rlp(value: Any) -> List[Bytes]:
    """Convert RLP header objects to encoded header bytes."""
    headers = _ensure_rlp_list(value, "headers")
    result: List[Bytes] = []
    for index, header in enumerate(headers):
        if not _is_rlp_value(header):
            raise ValueError(
                f"execution witness headers[{index}] must be an RLP value, "
                f"got {type(header).__name__}"
            )
        result.append(Bytes(eth_rlp.encode(header)))
    return result


def _execution_witness_from_json_rpc_rlp(
    witness_bytes: bytes,
) -> ExecutionWitness:
    """Decode a JSON-RPC RLP execution witness."""
    parsed = eth_rlp.decode(witness_bytes)
    if not isinstance(parsed, list):
        raise ValueError(
            "Unexpected execution witness RLP structure: "
            f"{type(parsed).__name__}"
        )
    # Some clients append a legacy, non-spec `keys` field. Accept it
    # temporarily, but ignore it below and only build from the spec fields.
    if len(parsed) not in (3, 4):
        raise ValueError(
            "Unexpected execution witness RLP structure: "
            f"list of length {len(parsed)}"
        )

    headers_raw, codes_raw, state_raw = parsed[0:3]
    return ExecutionWitness(
        state=_bytes_list_from_rlp(state_raw, "state"),
        codes=_bytes_list_from_rlp(codes_raw, "codes"),
        headers=_headers_from_rlp(headers_raw),
    )


@dataclass(frozen=True, slots=True)
class NewPayloadWithWitnessResponse:
    """
    Decoded response of POST /new-payload-with-witness.

    The witness field is ``None`` whenever status is not ``VALID`` (the spec
    mandates an empty SSZ witness in that case).
    """

    status: PayloadStatusEnum
    latest_valid_hash: Hash | None
    validation_error: str | None
    witness: ExecutionWitness | None = None

    @classmethod
    def from_ssz_bytes(cls, data: bytes) -> Self:
        """Decode an SSZ-encoded NewPayloadWithWitnessResponseV1 body."""
        resp = _SSZNewPayloadWithWitnessResponse.decode_bytes(data)

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
            if status != PayloadStatusEnum.VALID:
                raise ValueError(
                    f"{status.value} SSZ response must not contain a witness"
                )
            inner = _SSZExecutionWitness.decode_bytes(witness_bytes)
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
    def from_json_rpc_result(cls, data: Dict[str, Any]) -> Self:
        """
        Decode a JSON-RPC `engine_newPayloadWithWitnessVX` response.

        The `witness` field is a hex-encoded RLP list
        `[Headers, Codes, State]` where Headers are RLP-encoded header
        structures. Some clients append a legacy `Keys` element; it is ignored
        because it is not part of the current spec. Re-encode each header to
        RLP bytes so the resulting ExecutionWitness has the same
        `headers: List[Bytes]` shape as the fixture.
        """
        result = _NewPayloadWithWitnessJSONRPCResult.model_validate(data)

        witness: ExecutionWitness | None = None
        if result.witness is not None:
            witness_bytes = _decode_0x_hex(result.witness, "witness")
            if witness_bytes:
                witness = _execution_witness_from_json_rpc_rlp(witness_bytes)

        return cls(
            status=result.status,
            latest_valid_hash=result.latest_valid_hash,
            validation_error=result.validation_error,
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
