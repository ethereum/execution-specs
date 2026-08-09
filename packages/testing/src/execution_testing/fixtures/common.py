"""Common types used to define multiple fixture types."""

from typing import Any, ClassVar, Dict, List

from pydantic import (
    AliasChoices,
    Field,
    computed_field,
    model_validator,
)

from execution_testing.base_types import (
    BlobSchedule,
    Bloom,
    Bytes,
    CamelModel,
    EthereumTestRootModel,
    Hash,
    RLPSerializable,
    SignableRLPSerializable,
    ZeroPaddedHexNumber,
)
from execution_testing.test_types.account_types import Address
from execution_testing.test_types.receipt_types import (
    ReceiptDelegation,
    TransactionReceipt,
)
from execution_testing.test_types.transaction_types import (
    AuthorizationTupleGeneric,
    Transaction,
)


def _hexlify(value: Any) -> Any:
    """Return `value` with every byte-like leaf rendered as a hex string."""
    if isinstance(value, bytes):
        # `bytes(...)` forces the builtin, which emits no prefix. The
        # project's own byte types override `hex()` to include `0x`, so
        # calling it directly would double the prefix and a client would
        # reject the parameter as malformed.
        return "0x" + bytes(value).hex()
    if isinstance(value, dict):
        return {key: _hexlify(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_hexlify(item) for item in value]
    return value


class FixtureRPCCall(CamelModel):
    """
    A JSON-RPC request paired with the response the spec requires.

    The result is derived from the transition tool's own output rather than
    recorded from a client, so it is an assertion about the specification
    rather than about any implementation. Storing it in the fixture keeps
    the expectation pinned to the released artifact instead of to whichever
    version of the consumer happens to replay it.
    """

    method: str
    params: List[Any] = Field(default_factory=list)
    result: Any = None

    @model_validator(mode="before")
    @classmethod
    def stringify_binary_params(cls, data: Any) -> Any:
        """
        Render byte-like parameters as hex before they are stored.

        `params` is untyped, because a JSON-RPC parameter can be a string,
        a number, a boolean or a filter object. That leaves pydantic with
        no serializer for `Address` and `Hash`, which are `bytes`
        subclasses, so a test passing one directly fails at fill time with
        a utf-8 decode error rather than anything informative. Converting
        here keeps the call sites natural: a test names an address with
        the object it already holds.
        """
        if isinstance(data, dict) and "params" in data:
            data = dict(data)
            data["params"] = _hexlify(data["params"])
        return data

    result_keccak: Hash | None = None
    """
    Digest of the expected result, used instead of the result itself.

    Only for responses whose value is large and already present elsewhere
    in the fixture — contract bytecode is in `pre` and `postState`, so
    repeating it here would duplicate the largest field in the file for no
    added assertion. A client can still check its own answer by hashing it,
    and a byte-level diff of a bytecode blob would be unreadable anyway.
    """
    error_code: int | None = None
    """
    Set when the call is expected to fail.

    Error *messages* are client-specific wording and are never compared;
    only the code and the shape of the error are.
    """
    round_trip: bool = False
    """
    Marks an expectation whose value the harness declared, not the spec.

    Every other call here asserts something the Python spec computed, so a
    disagreement means the client is wrong about Ethereum. A round-trip
    call instead asserts "return what I told you", and the only such thing
    at present is the `safe`/`finalized` block tags: the consensus layer
    hands those to the execution client through `engine_forkchoiceUpdated`
    and the client's whole job is to remember them. The spec has nothing to
    say about either.

    The distinction is recorded in the artifact rather than left to the
    code that emits it, because the fixture is what a client team reads and
    they are entitled to know which assertions descend from a
    specification and which describe the test harness. A consumer that
    cannot supply the declaration must skip these; see
    `FixtureForkchoiceState`.
    """


class FixtureForkchoiceState(CamelModel):
    """
    The forkchoice triple a consumer must declare to a client.

    `safe` and `finalized` are not properties of the chain or of the state
    transition: they are values the consensus layer tells the execution
    client, and the client only has to remember them. There is therefore
    nothing to derive, and the three hashes are recorded here so that the
    consumer sending `engine_forkchoiceUpdated` and the round-trip
    expectations replayed afterwards cannot disagree about what was
    declared.

    Only the Engine API can deliver this, so only the engine fixture
    formats carry the field. `consume rlp` never opens the engine port, so
    a client it drives has no safe or finalized block at all and the
    matching expectations are neither emitted into that format nor
    replayed from it.
    """

    head_block_hash: Hash
    safe_block_hash: Hash
    finalized_block_hash: Hash


class FixtureForkBlobSchedule(CamelModel):
    """Representation of the blob schedule of a given fork."""

    target_blobs_per_block: ZeroPaddedHexNumber = Field(..., alias="target")
    max_blobs_per_block: ZeroPaddedHexNumber = Field(..., alias="max")
    base_fee_update_fraction: ZeroPaddedHexNumber = Field(...)


class FixtureBlobSchedule(
    EthereumTestRootModel[Dict[str, FixtureForkBlobSchedule]]
):
    """Blob schedule configuration dictionary."""

    root: Dict[str, FixtureForkBlobSchedule] = Field(
        default_factory=dict, validate_default=True
    )

    @classmethod
    def from_blob_schedule(
        cls, blob_schedule: BlobSchedule | None
    ) -> "FixtureBlobSchedule | None":
        """Return a FixtureBlobSchedule from a BlobSchedule."""
        if blob_schedule is None:
            return None
        return cls(
            root=blob_schedule.model_dump(),
        )


class FixtureAuthorizationTuple(
    AuthorizationTupleGeneric[ZeroPaddedHexNumber], SignableRLPSerializable
):
    """Authorization tuple for fixture transactions."""

    # Allow extra fields: FixtureAuthorizationTuple is constructed from
    # AuthorizationTuple via model_dump(), which has extra fields.
    model_config = CamelModel.model_config | {"extra": "ignore"}

    v: ZeroPaddedHexNumber = Field(
        validation_alias=AliasChoices("v", "yParity")
    )
    r: ZeroPaddedHexNumber
    s: ZeroPaddedHexNumber

    signer: Address | None = None

    @model_validator(mode="before")
    @classmethod
    def strip_y_parity_duplicate(cls, data: Any) -> Any:
        """
        Strip yParity if v is present since yParity is added as a duplicate
        during serialization for compatibility.
        """
        if isinstance(data, dict) and "v" in data and "yParity" in data:
            data.pop("yParity")
        return data

    @classmethod
    def from_authorization_tuple(
        cls, auth_tuple: AuthorizationTupleGeneric
    ) -> "FixtureAuthorizationTuple":
        """Return FixtureAuthorizationTuple from an AuthorizationTuple."""
        # Exclude fields that don't exist in FixtureAuthorizationTuple
        auth_dump = auth_tuple.model_dump()
        auth_dump.pop("secret_key", None)
        return cls(**auth_dump)

    def sign(self) -> None:
        """Sign the current object for further serialization."""
        # No-op, as the object is always already signed
        return


class FixtureTransactionLog(CamelModel, RLPSerializable):
    """Fixture variant of the TransactionLog type."""

    model_config = CamelModel.model_config | {"extra": "ignore"}

    address: Address | None = None
    topics: List[Hash] | None = None
    data: Bytes | None = None

    rlp_fields: ClassVar[List[str]] = [
        "address",
        "topics",
        "data",
    ]


class FixtureReceiptDelegation(ReceiptDelegation):
    """Fixture variant of the ReceiptDelegation type."""

    nonce: ZeroPaddedHexNumber


class FixtureTransactionReceipt(CamelModel, RLPSerializable):
    """Fixture variant of the TransactionReceipt type."""

    transaction_hash: Hash
    ty: ZeroPaddedHexNumber = Field(..., alias="type")
    cumulative_gas_used: ZeroPaddedHexNumber
    bloom: Bloom
    logs: List[FixtureTransactionLog]
    post_state: Hash | None = None
    status: bool | None = None

    rlp_fields: ClassVar[List[str]] = [
        "post_state",
        "status",
        "cumulative_gas_used",
        "bloom",
        "logs",
    ]
    rlp_exclude_none: ClassVar[bool] = True

    @model_validator(mode="before")
    @classmethod
    def _drop_computed_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data = dict(data)
            data.pop("rlp", None)
            data.pop("rlp_field", None)
        return data

    @computed_field(alias="rlp")
    def rlp_field(self) -> Bytes:
        """Return the RLP."""
        return self.rlp()

    def get_rlp_prefix(self) -> bytes:
        """
        Return a prefix that has to be appended to the serialized object.

        By default, an empty string is returned.
        """
        if self.ty > 0:
            return bytes([self.ty])
        return b""

    @classmethod
    def from_transaction_receipt(
        cls,
        receipt: TransactionReceipt,
        tx: Transaction,
    ) -> "FixtureTransactionReceipt":
        """Return FixtureTransactionReceipt from a TransactionReceipt."""
        model_as_dict = receipt.model_dump(
            exclude_none=True, include=set(cls.model_fields.keys())
        ) | {"ty": tx.ty, "transaction_hash": tx.hash}
        return cls(**model_as_dict)
