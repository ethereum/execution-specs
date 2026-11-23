"""Transaction-related types for Ethereum tests."""

import numbers
from dataclasses import dataclass
from enum import Enum, IntEnum, IntFlag, auto, unique
from functools import cached_property
from typing import (
    Annotated,
    Any,
    ClassVar,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Self,
    Sequence,
)

import ethereum_rlp as eth_rlp
from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    InstanceOf,
    PrivateAttr,
    computed_field,
    field_validator,
    model_serializer,
    model_validator,
)
from spec256k1 import PrivateKey, PublicKey

from execution_testing.base_types import (
    AccessList,
    Address,
    Bytes,
    CamelModel,
    FrameSignatureScheme,
    Hash,
    HexNumber,
    NumberBoundTypeVar,
    RLPSerializable,
    SignableRLPSerializable,
    Signer,
    TestAddress,
    TestPrivateKey,
    encoded_prefixed_size,
    encoded_size,
)
from execution_testing.exceptions import TransactionException
from execution_testing.forks import Fork
from execution_testing.forks.forks.eips.bogota.eip_8141 import (
    EXPIRY_VERIFIER_ADDRESS,
)
from execution_testing.logging import (
    get_logger,
)
from execution_testing.vm import Bytecode

from .account_types import EOA
from .blob_types import Blob
from .chain_config_types import ChainConfigDefaults
from .phase_manager import TestPhase, TestPhaseManager
from .receipt_types import FrameReceipt, TransactionLog, TransactionReceipt
from .utils import int_to_bytes, keccak256

logger = get_logger(__name__)


class TransactionType(IntEnum):
    """Transaction types."""

    LEGACY = 0
    ACCESS_LIST = 1
    BASE_FEE = 2
    BLOB_TRANSACTION = 3
    SET_CODE = 4
    FRAME = 6


class FrameMode(IntEnum):
    """
    Mode of a frame in an [EIP-8141](https://eips.ethereum.org/EIPS/eip-8141)
    frame transaction: who the frame executes as and when it runs.
    """

    DEFAULT = 0
    VERIFY = 1
    SENDER = 2


class FrameFlag(IntFlag):
    """
    Flags of a frame in an [EIP-8141](https://eips.ethereum.org/EIPS/eip-8141)
    frame transaction: the approvals it may grant and whether it opens an
    atomic batch.
    """

    APPROVE_PAYMENT = 1
    APPROVE_EXECUTION = 2
    ATOMIC_BATCH = 4


class FrameStatus(IntEnum):
    """
    Status of a frame in an [EIP-8141](https://eips.ethereum.org/EIPS/eip-8141)
    frame transaction's receipt.
    """

    FAILURE = 0
    SUCCESS = 1
    SKIPPED = 2


@unique
class FrameOutcome(Enum):
    """
    How a frame of an [EIP-8141](https://eips.ethereum.org/EIPS/eip-8141)
    frame transaction ends, and therefore what its receipt reports.
    """

    SUCCESS = auto()
    REVERT = auto()
    HALT = auto()
    SKIPPED = auto()
    UNROLLED = auto()
    """Succeeded, then undone by its atomic batch."""

    @property
    def status(self) -> FrameStatus:
        """Return the status this outcome reports."""
        if self in (FrameOutcome.SUCCESS, FrameOutcome.UNROLLED):
            return FrameStatus.SUCCESS
        if self is FrameOutcome.SKIPPED:
            return FrameStatus.SKIPPED
        return FrameStatus.FAILURE

    @property
    def keeps_state_gas(self) -> bool:
        """Check whether the frame's state changes survive."""
        return self is FrameOutcome.SUCCESS


@dataclass
class TransactionDefaults:
    """Default values for transactions."""

    gas_price: int = 10
    max_fee_per_gas: int = 7
    max_priority_fee_per_gas: int = 0
    # EIP-8141 frame transactions cap their total fee instead of a fee
    # per gas; the default budget never binds at test base fees.
    max_fee: int = 10**18


class AuthorizationTupleGeneric(
    CamelModel, Generic[NumberBoundTypeVar], SignableRLPSerializable
):
    """Authorization tuple for transactions."""

    chain_id: NumberBoundTypeVar = Field(0)  # type: ignore
    address: Address
    nonce: NumberBoundTypeVar = Field(0)  # type: ignore

    v: NumberBoundTypeVar = Field(
        default=0, validation_alias=AliasChoices("v", "yParity")
    )  # type: ignore
    r: NumberBoundTypeVar = Field(0)  # type: ignore
    s: NumberBoundTypeVar = Field(0)  # type: ignore

    magic: ClassVar[int] = 0x05

    rlp_fields: ClassVar[List[str]] = [
        "chain_id",
        "address",
        "nonce",
        "v",
        "r",
        "s",
    ]
    rlp_signing_fields: ClassVar[List[str]] = ["chain_id", "address", "nonce"]

    def get_rlp_signing_prefix(self) -> bytes:
        """
        Return a prefix that has to be appended to the serialized signing
        object.

        By default, an empty string is returned.
        """
        return self.magic.to_bytes(1, byteorder="big")

    @model_serializer(mode="wrap", when_used="json-unless-none")
    def duplicate_v_as_y_parity(self, serializer: Any) -> Any:
        """
        Add a duplicate 'yParity' field (same as `v`) in JSON fixtures.

        Background: https://github.com/erigontech/erigon/issues/14073
        """
        data = serializer(self)
        if "v" in data and data["v"] is not None:
            data["yParity"] = data["v"]
        return data


class AuthorizationTuple(AuthorizationTupleGeneric[HexNumber]):
    """Authorization tuple for transactions."""

    signer: EOA | None = None
    secret_key: Hash | None = None
    creates_account: bool = Field(False, exclude=True)
    writes_delegation: bool = Field(True, exclude=True)
    # Whether applying this authorization is the transaction's first
    # write to the authority's account leaf. False for a self-sponsored
    # authority (the sender is written at inclusion), for repeated
    # authorizations on one authority, and for invalid authorizations.
    first_write: bool = Field(True, exclude=True)

    def model_post_init(self, __context: Any) -> None:
        """
        Automatically signs the authorization tuple if a secret key or sender
        are provided.
        """
        super().model_post_init(__context)
        self.sign()

    def sign(self: "AuthorizationTuple") -> None:
        """Signs the authorization tuple with a private key."""
        signature_bytes: bytes | None = None
        rlp_signing_bytes = self.rlp_signing_bytes()
        if (
            "v" not in self.model_fields_set
            and "r" not in self.model_fields_set
            and "s" not in self.model_fields_set
        ):
            signing_key: Hash | None = None
            if self.secret_key is not None:
                signing_key = self.secret_key
            elif self.signer is not None:
                eoa = self.signer
                assert eoa is not None, "signer must be set"
                signing_key = eoa.key
            assert signing_key is not None, "secret_key or signer must be set"

            signature_bytes = PrivateKey(signing_key).sign_recoverable(
                rlp_signing_bytes.keccak256()
            )
            self.v, self.r, self.s = (
                HexNumber(signature_bytes[64]),
                HexNumber(
                    int.from_bytes(signature_bytes[0:32], byteorder="big")
                ),
                HexNumber(
                    int.from_bytes(signature_bytes[32:64], byteorder="big")
                ),
            )
            self.model_fields_set.add("v")
            self.model_fields_set.add("r")
            self.model_fields_set.add("s")

        if self.signer is None:
            try:
                if not signature_bytes:
                    signature_bytes = (
                        int(self.r).to_bytes(32, byteorder="big")
                        + int(self.s).to_bytes(32, byteorder="big")
                        + bytes([self.v])
                    )
                public_key = PublicKey.from_signature_and_message(
                    signature_bytes, rlp_signing_bytes.keccak256()
                )
                self.signer = EOA(
                    address=Address(
                        keccak256(public_key.format(compressed=False)[1:])[
                            32 - 20 :
                        ]
                    )
                )
            except Exception:
                # Signer remains `None` in this case
                pass


DEFAULT_FRAME_GAS_LIMIT = 100_000
"""
Default execution gas budget of a frame, with ample headroom for the
sender's default code, a value transfer, or a small call. Tests that
are gas-sensitive should set `gas_limit` explicitly.
"""

DEFAULT_FRAME_STATE_GAS_LIMIT = 400_000
"""
Default state gas budget of a frame, with ample headroom for an
account creation (183,600) plus a couple of storage slot creations
(97,920 each); unused budget is refunded at settlement. Tests that
are gas-sensitive — including any expiry verifier frame, which must
declare a zero state budget — should set `state_gas_limit` explicitly.
"""


class FrameGeneric(CamelModel, Generic[NumberBoundTypeVar], RLPSerializable):
    """
    Frame within an [EIP-8141](https://eips.ethereum.org/EIPS/eip-8141)
    frame transaction.
    """

    mode: NumberBoundTypeVar = Field(0)  # type: ignore
    flags: NumberBoundTypeVar = Field(0)  # type: ignore
    target: Address | None = None
    gas_limit: NumberBoundTypeVar = Field(DEFAULT_FRAME_GAS_LIMIT)  # type: ignore
    state_gas_limit: NumberBoundTypeVar = Field(  # type: ignore
        DEFAULT_FRAME_STATE_GAS_LIMIT
    )
    value: NumberBoundTypeVar = Field(0)  # type: ignore
    data: Bytes = Field(Bytes(b""))

    rlp_fields: ClassVar[List[str]] = [
        "mode",
        "flags",
        "target",
        "gas_limits",
        "value",
        "data",
    ]

    @property
    def gas_limits(self) -> List[NumberBoundTypeVar]:
        """
        Return the frame's nested `limits = [execution, state]` RLP list.
        """
        return [self.gas_limit, self.state_gas_limit]


class _RequiresSettlement:
    """
    Marker of a `Frame` field that only takes effect through
    `Transaction.expect_frame_receipts`.
    """


REQUIRES_SETTLEMENT = _RequiresSettlement()
"""
Annotate a `Frame` expectation field with this marker, so that setting it
requires the frame to be settled before its transaction is encoded or its
receipt is requested.
"""


class Frame(FrameGeneric[HexNumber]):
    """
    Frame within an EIP-8141 frame transaction (test authoring).

    Besides its own fields, a frame can carry the facts its budget and its
    expected receipt follow from: how it ends, the code its target runs,
    and whether its target is warm or delegated. These are excluded from
    serialization, and only take effect when the frame's budgets are
    settled or its receipt is requested.
    """

    # What the frame runs
    outcome: Annotated[FrameOutcome, REQUIRES_SETTLEMENT] = Field(
        FrameOutcome.SUCCESS, exclude=True
    )
    """How the frame ends."""

    code: Annotated[Optional[Bytecode], REQUIRES_SETTLEMENT] = Field(
        None, exclude=True
    )
    """Code the frame's target runs, which prices it."""

    execution_gas: Annotated[Optional[int], REQUIRES_SETTLEMENT] = Field(
        None, exclude=True
    )
    """Execution gas after entry, where `code` cannot price it."""

    # What it is budgeted
    gas_limit_delta: Annotated[Optional[int], REQUIRES_SETTLEMENT] = Field(
        None, exclude=True
    )
    """Execution budget, relative to the gas the frame spends."""

    state_gas_limit_delta: Annotated[Optional[int], REQUIRES_SETTLEMENT] = (
        Field(None, exclude=True)
    )
    """State budget, relative to the state gas the frame writes."""

    # What its target's entry access costs
    warm: Annotated[bool, REQUIRES_SETTLEMENT] = Field(False, exclude=True)
    """
    Whether the resolved target is warm. Unless set explicitly,
    `Transaction.expect_frame_receipts` sets it for a resolved target in
    the warm set the transaction starts with: the sender or a precompile.
    """

    delegated: Annotated[bool, REQUIRES_SETTLEMENT] = Field(
        False, exclude=True
    )
    """Whether the target carries an EIP-7702 designation."""

    delegation_warm: Annotated[bool, REQUIRES_SETTLEMENT] = Field(
        False, exclude=True
    )
    """Whether the designated address is warm."""

    # What its receipt reports
    pin_gas: Annotated[bool, REQUIRES_SETTLEMENT] = Field(True, exclude=True)
    """Whether the receipt's execution gas is pinned."""

    gas_used: Annotated[Optional[int], REQUIRES_SETTLEMENT] = Field(
        None, exclude=True
    )
    """Execution gas the receipt reports."""

    state_gas_used: Annotated[Optional[int], REQUIRES_SETTLEMENT] = Field(
        None, exclude=True
    )
    """State gas the receipt reports."""

    logs: Annotated[Optional[List[TransactionLog]], REQUIRES_SETTLEMENT] = (
        Field(None, exclude=True)
    )
    """Logs the receipt reports."""

    _settled: bool = PrivateAttr(False)

    @property
    def requires_settlement(self) -> bool:
        """
        Check whether any field set on the frame only takes effect through
        `Transaction.expect_frame_receipts`.
        """
        return any(
            REQUIRES_SETTLEMENT in field.metadata
            for name, field in type(self).model_fields.items()
            if name in self.model_fields_set
        )

    @property
    def settled(self) -> bool:
        """
        Check whether `Transaction.expect_frame_receipts` has settled the
        frame.
        """
        return self._settled

    @classmethod
    def default(cls, **overrides: Any) -> Self:
        """Return a `DEFAULT` frame executing the frame entry point."""
        mode = overrides.setdefault("mode", FrameMode.DEFAULT)
        assert mode == FrameMode.DEFAULT, f"not a DEFAULT frame: mode {mode}"
        return cls(**overrides)

    @classmethod
    def sender(cls, **overrides: Any) -> Self:
        """Return a `SENDER` frame executing as the transaction sender."""
        mode = overrides.setdefault("mode", FrameMode.SENDER)
        assert mode == FrameMode.SENDER, f"not a SENDER frame: mode {mode}"
        return cls(**overrides)

    @classmethod
    def verify(cls, **overrides: Any) -> Self:
        """Return a `VERIFY` frame approving execution and payment."""
        mode = overrides.setdefault("mode", FrameMode.VERIFY)
        assert mode == FrameMode.VERIFY, f"not a VERIFY frame: mode {mode}"
        overrides.setdefault(
            "flags", FrameFlag.APPROVE_EXECUTION | FrameFlag.APPROVE_PAYMENT
        )
        return cls(**overrides)

    @classmethod
    def expiry(cls, **overrides: Any) -> Self:
        """Return a `VERIFY` frame targeting the expiry verifier predeploy."""
        mode = overrides.setdefault("mode", FrameMode.VERIFY)
        assert mode == FrameMode.VERIFY, f"not a VERIFY frame: mode {mode}"
        overrides.setdefault("flags", FrameFlag(0))
        overrides.setdefault("target", Address(EXPIRY_VERIFIER_ADDRESS))
        # Such a frame is only valid with a zero state gas budget, and never
        # expires at the maximum 64-bit timestamp.
        overrides.setdefault("state_gas_limit", 0)
        overrides.setdefault("data", (2**64 - 1).to_bytes(8, "big"))
        return cls(**overrides)

    def entry_gas(self, fork: Fork) -> int:
        """Return the access the frame is charged at entry."""
        return fork.frame_entry_gas_calculator()(
            target_warm=self.warm,
            delegated=self.delegated,
            delegation_warm=self.delegation_warm,
        )

    def code_gas(self, fork: Fork) -> int:
        """Return the execution gas the frame draws after entry."""
        if self.execution_gas is not None:
            return self.execution_gas
        if self.code is None:
            return 0
        return self.code.execution_cost(fork)

    def code_state_gas(self, fork: Fork) -> int:
        """Return the state gas the frame's code writes."""
        if self.code is None:
            return 0
        return self.code.state_cost(fork)

    def settle_budgets(self, fork: Fork) -> None:
        """Settle the budgets the frame declares as deltas on its cost."""
        if self.gas_limit_delta is not None:
            assert "gas_limit" not in self.model_fields_set, (
                "a frame declares its execution budget once"
            )
            self.gas_limit = HexNumber(
                self.entry_gas(fork)
                + self.code_gas(fork)
                + self.gas_limit_delta
            )
        if self.state_gas_limit_delta is not None:
            assert "state_gas_limit" not in self.model_fields_set, (
                "a frame declares its state budget once"
            )
            self.state_gas_limit = HexNumber(
                self.code_state_gas(fork) + self.state_gas_limit_delta
            )
        self._settled = True

    def receipt(self, fork: Fork) -> FrameReceipt:
        """Return the receipt the frame should report."""
        assert self.settled or not self.requires_settlement, (
            "the frame's expectations only take effect once settled: call "
            "`expect_frame_receipts` on its transaction and read the frame "
            "from the transaction's `frames`"
        )
        gas_used: Optional[int]
        match self.pin_gas, self.gas_used, self.outcome:
            case False, None, _:
                gas_used = None
            case True, int() as pinned, _:
                gas_used = pinned
            case True, None, FrameOutcome.SKIPPED:
                gas_used = 0
            case True, None, FrameOutcome.HALT:
                # A halting frame forfeits its entire execution budget.
                gas_used = int(self.gas_limit)
            case True, None, (
                FrameOutcome.SUCCESS
                | FrameOutcome.REVERT
                | FrameOutcome.UNROLLED
            ):
                gas_used = self.entry_gas(fork) + self.code_gas(fork)
            case _:
                raise ValueError(
                    f"no receipt gas for pin_gas={self.pin_gas}, "
                    f"gas_used={self.gas_used}, outcome={self.outcome}"
                )

        state_gas_used = 0
        if self.state_gas_used is not None:
            state_gas_used = self.state_gas_used
        elif self.outcome.keeps_state_gas:
            state_gas_used = self.code_state_gas(fork)

        logs = self.logs
        if logs is None and self.outcome is not FrameOutcome.SUCCESS:
            logs = []

        return FrameReceipt(
            status=self.outcome.status,
            gas_used=gas_used,
            state_gas_used=state_gas_used,
            logs=logs,
        )


class FrameSignatureGeneric(
    CamelModel, Generic[NumberBoundTypeVar], RLPSerializable
):
    """
    Signature entry within an
    [EIP-8141](https://eips.ethereum.org/EIPS/eip-8141) frame transaction.
    """

    scheme: NumberBoundTypeVar = Field(0)  # type: ignore
    signer: Bytes = Field(Bytes(b""))
    msg: Bytes = Field(Bytes(b""))
    signature: Bytes = Field(Bytes(b""))

    rlp_fields: ClassVar[List[str]] = [
        "scheme",
        "signer",
        "msg",
        "signature",
    ]

    @property
    def signature_length(self) -> int:
        """Return the length of the raw signature bytes."""
        return len(self.signature)


class FrameSignature(FrameSignatureGeneric[HexNumber]):
    """
    Signature entry within an EIP-8141 frame transaction (test authoring).

    When the entry has a `signed_by` signer and no `signature` bytes, the
    raw `signature` bytes are filled in automatically: entries with an
    explicit 32-byte `msg` sign that digest as soon as they are built,
    while entries with an empty `msg` sign the canonical transaction
    signature hash when the transaction is signed. Until then, the
    `signature_length` of an unsigned entry is its signer's.

    `signer` also accepts a `Signer`, which becomes `signed_by`, while the
    `signer` field keeps the bytes written in the entry: `bytes(signer)`,
    or empty for `ARBITRARY` entries. Without an explicit `scheme`, the
    signer's preferred scheme is used. Pass `signed_by` and `signer`
    separately for entries whose bytes differ from the signer's.
    """

    signed_by: InstanceOf[Signer] | None = Field(None, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def split_signer(cls, data: Any) -> Any:
        """Split a `Signer` passed as `signer` into `signed_by`."""
        if not isinstance(data, dict):
            return data
        signer = data.get("signer")
        if not isinstance(signer, Signer):
            return data
        data = dict(data)
        data.setdefault("signed_by", signer)
        if data.get("scheme") is None:
            data["scheme"] = signer.signature_schemes[0]
        if data["scheme"] == FrameSignatureScheme.ARBITRARY:
            data["signer"] = Bytes(b"")
        else:
            data["signer"] = Bytes(bytes(signer))
        return data

    @model_validator(mode="after")
    def sign_explicit_digest(self) -> Self:
        """
        Sign an explicit 32-byte `msg` right away, since its signature does
        not depend on the transaction and is priced by its content.
        """
        if (
            self.signed_by is not None
            and len(self.msg) == 32
            and len(self.signature) == 0
        ):
            self.signed_over(Hash(self.msg), self.signed_by)
        return self

    @property
    def signature_length(self) -> int:
        """
        Return the length of the raw signature bytes, or of the bytes its
        signer will produce while the entry is unsigned.
        """
        if len(self.signature) == 0 and self.signed_by is not None:
            return self.signed_by.signature_length
        return len(self.signature)

    def signed_over(self, digest: Hash, signer: Signer) -> None:
        """Fill the raw signature bytes by signing `digest` with `signer`."""
        self.signature = signer.sign_message(digest)


class TransactionGeneric(BaseModel, Generic[NumberBoundTypeVar]):
    """
    Generic transaction type used as a parent for Transaction and
    FixtureTransaction (blockchain).
    """

    ty: NumberBoundTypeVar = Field(0, alias="type")  # type: ignore
    chain_id: NumberBoundTypeVar = Field(
        default_factory=lambda: ChainConfigDefaults.chain_id,
        validate_default=True,
    )
    nonce: NumberBoundTypeVar = Field(0)  # type: ignore
    gas_price: NumberBoundTypeVar | None = None
    max_priority_fee_per_gas: NumberBoundTypeVar | None = None
    max_fee_per_gas: NumberBoundTypeVar | None = None
    max_fee: NumberBoundTypeVar | None = None
    gas_limit: NumberBoundTypeVar = Field(21_000)  # type: ignore
    to: Address | None = None
    value: NumberBoundTypeVar = Field(0)  # type: ignore
    data: Bytes = Field(Bytes(b""))
    access_list: List[AccessList] | None = None
    max_fee_per_blob_gas: NumberBoundTypeVar | None = None
    blob_versioned_hashes: Sequence[Hash] | None = None

    v: NumberBoundTypeVar = Field(0)  # type: ignore
    r: NumberBoundTypeVar = Field(0)  # type: ignore
    s: NumberBoundTypeVar = Field(0)  # type: ignore
    sender: EOA | None = None

    def metadata_string(self) -> str | None:
        """Return the metadata field as a formatted json string or None."""
        return None


class TransactionValidateToAsEmptyString(CamelModel):
    """Handler to validate the `to` field from an empty string."""

    @model_validator(mode="before")
    @classmethod
    def validate_to_as_empty_string(cls, data: Any) -> Any:
        """
        If the `to` field is an empty string, set the model value to None.
        """
        if (
            isinstance(data, dict)
            and "to" in data
            and isinstance(data["to"], str)
            and data["to"] == ""
        ):
            data["to"] = None
        return data


class TransactionFixtureConverter(TransactionValidateToAsEmptyString):
    """
    Handler for serializing and validating the `to` field as an empty string.
    """

    @model_serializer(mode="wrap", when_used="json-unless-none")
    def serialize_to_as_empty_string(self, serializer: Any) -> Any:
        """
        Serialize the `to` field as the empty string if the model value is
        None.
        """
        default = serializer(self)
        if default is not None and "to" not in default:
            default["to"] = ""
        return default


class TransactionTransitionToolConverter(TransactionValidateToAsEmptyString):
    """
    Handler for serializing and validating the `to` field as an empty string.
    """

    @model_serializer(mode="wrap", when_used="json-unless-none")
    def serialize_to_as_none(self, serializer: Any) -> Any:
        """
        Serialize the `to` field as `None` if the model value is None.

        This is required as we use `exclude_none=True` when serializing, but
        the t8n tool explicitly requires a value of `None` (respectively null),
        for if the `to` field should be unset (contract creation).
        """
        default = serializer(self)
        if default is not None and "to" not in default:
            default["to"] = None
        return default


class TransactionTestMetadata(CamelModel):
    """Represents the metadata for a transaction."""

    test_id: str | None = None
    phase: TestPhase | None = None
    action: str | None = None  # e.g. deploy / fund / execute
    target: str | None = None  # account/contract label
    tx_index: int | None = None  # index within this phase

    def to_json(self) -> str:
        """
        Convert the transaction metadata into json string for it to be embedded
        in the request id.
        """
        return self.model_dump_json(exclude_none=True, by_alias=True)


@dataclass(frozen=True)
class FrameSettlement:
    """
    How the gas of an [EIP-8141](https://eips.ethereum.org/EIPS/eip-8141)
    frame transaction settles, from its intrinsic cost and the expected
    receipts of its frames.
    """

    execution_gas: int
    """Pre-refund execution gas: the intrinsic cost plus every receipt."""

    state_gas: int
    """Attributed state gas, which no refund and no floor touches."""

    calldata_floor: int
    """The floor the execution dimension is held to."""

    effective_refund: int
    """The refund that survives the cap."""

    @property
    def gas_before_refund(self) -> int:
        """Return the spent gas in both dimensions, before refunds."""
        return self.execution_gas + self.state_gas

    def floor_binds(self, *, after_refund: bool = True) -> bool:
        """Check whether the calldata floor sets the settled execution gas."""
        charged = self.execution_gas
        if after_refund:
            charged -= self.effective_refund
        return self.calldata_floor > charged

    def payer_gas_used(self) -> int:
        """Return the gas the payer is charged."""
        execution = max(
            self.execution_gas - self.effective_refund, self.calldata_floor
        )
        return execution + self.state_gas

    def block_gas_used(self) -> int:
        """
        Return the gas the block accounts for across both dimensions,
        before refunds.

        This is the sum of the two dimensions, not the header's `gas_used`,
        which `block_header_gas_used` returns.
        """
        return max(self.execution_gas, self.calldata_floor) + self.state_gas

    def block_header_gas_used(self) -> int:
        """
        Return the header's `gas_used` of a block holding only this
        transaction: the larger of its execution and state dimensions.

        Care should be taken with a block of several transactions: the
        header takes the larger of the block's execution and state totals,
        each summed across every transaction, which is not the sum of this
        value over the transactions.
        """
        return max(
            max(self.execution_gas, self.calldata_floor), self.state_gas
        )


class Transaction(
    TransactionGeneric[HexNumber],
    TransactionTransitionToolConverter,
    SignableRLPSerializable,
):
    """Generic object that can represent all Ethereum transaction types."""

    @model_validator(mode="before")
    @classmethod
    def strip_hash_from_t8n_output(cls, data: Any) -> Any:
        """Strip the hash field which may be included in t8n tool output."""
        if isinstance(data, dict):
            # If the class has a transaction_hash, keep it. This is likely
            # an internal RPC class that extends from Transaction.
            if "transaction_hash" not in cls.model_fields:
                data.pop("hash", None)
        return data

    @field_validator("signatures", mode="before")
    @classmethod
    def signers_to_frame_signatures(cls, signatures: Any) -> Any:
        """
        Turn each `Signer` in the signature list into an entry signed by it
        over the canonical signature hash.

        Entries are copied, since signing fills in their raw bytes and must
        not modify entries shared with the caller.
        """
        if signatures is None:
            return None
        entries = []
        for sig in signatures:
            if isinstance(sig, Signer):
                entries.append(FrameSignature(signer=sig))
            elif isinstance(sig, FrameSignature):
                entries.append(sig.model_copy())
            else:
                entries.append(sig)
        return entries

    @field_validator("frames", mode="before")
    @classmethod
    def copy_frames(cls, frames: Any) -> Any:
        """
        Copy each frame on instantiation in order to protect the original frame
        instance from modifications.
        """
        if frames is None:
            return None
        return [
            frame.model_copy() if isinstance(frame, Frame) else frame
            for frame in frames
        ]

    def copy(self, **kwargs: Any) -> Self:
        """
        Create a copy of the transaction with the updated fields that are
        validated.

        Frame transactions are not supported: the copy is rebuilt from the
        serialized fields, which leave out each signature entry's signer
        and each frame's expectations, so the copy would never be signed.
        """
        if self.frames is not None:
            raise NotImplementedError(
                "copying a frame transaction drops its signers and frame "
                "expectations; build a new `Transaction` instead"
            )
        return super().copy(**kwargs)

    @model_validator(mode="before")
    @classmethod
    def treat_none_gas_limit_as_unset(cls, data: Any) -> Any:
        """Treat a `None` gas limit (any alias) as unset."""
        if isinstance(data, dict):
            for alias in ("gas_limit", "gasLimit", "gas"):
                if alias in data and data[alias] is None:
                    del data[alias]
        return data

    gas_limit: HexNumber = Field(
        HexNumber(21_000),
        serialization_alias="gas",
        validation_alias=AliasChoices("gas_limit", "gasLimit", "gas"),
    )
    to: Address | None = Field(Address(0xAA))
    data: Bytes = Field(Bytes(b""), alias="input")

    authorization_list: List[AuthorizationTuple] | None = None

    frames: List[Frame] | None = None
    signatures: List[FrameSignature] | None = None

    secret_key: Hash | None = None
    error: List[TransactionException] | TransactionException | None = Field(
        None, exclude=True
    )

    protected: bool = Field(True, exclude=True)

    expected_receipt: TransactionReceipt | None = Field(None, exclude=True)

    state_gas_reservoir: int = Field(
        0,
        exclude=True,
        description=(
            "Extra gas on top of the transaction gas limit cap, reserved "
            "for state gas (EIP-8037). Only takes effect when `gas_limit` "
            "is unset and the fork enables the state gas reservoir: "
            "leaving it unset keeps the full implicit gas limit, an "
            "explicit 0 pins the gas limit to exactly the cap (no "
            "reservoir), and a positive value pins it to the cap plus the "
            "requested reservoir. Requesting a positive reservoir on a "
            "fork without the state gas reservoir raises an error."
        ),
    )

    zero: ClassVar[Literal[0]] = 0

    metadata: TransactionTestMetadata | None = Field(None, exclude=True)
    test_phase: TestPhase | None = Field(
        default_factory=TestPhaseManager.get_current_phase, exclude=True
    )

    model_config = ConfigDict(validate_assignment=True)

    class InvalidFeePaymentError(Exception):
        """Transaction described more than one fee payment type."""

        FEE_FIELD_LABELS = {
            "gas_price": "legacy/type-1",
            "max_fee_per_gas": "type-2+",
            "max_priority_fee_per_gas": "type-2+",
            "max_fee_per_blob_gas": "type-3+",
            "max_fee": "frame",
        }

        def __init__(self, *conflicting_fields: str) -> None:
            """Store the conflicting fee fields used in the transaction."""
            self.conflicting_fields = conflicting_fields

        def __str__(self) -> str:
            """Print exception string."""
            if not self.conflicting_fields:
                return "cannot mix fee fields in a single tx"
            labels = ", ".join(
                f"'{f}' ({self.FEE_FIELD_LABELS[f]})"
                for f in self.conflicting_fields
            )
            return f"cannot mix fee fields in a single tx: {labels}"

    class InvalidSignaturePrivateKeyError(Exception):
        """
        Transaction describes both the signature and private key of source
        account.
        """

        def __str__(self) -> str:
            """Print exception string."""
            return "can't define both 'signature' and 'private_key'"

    def model_post_init(self, __context: Any) -> None:
        """Ensure transaction has no conflicting properties."""
        super().model_post_init(__context)

        conflicting_fee_fields = [
            field_name
            for field_name in (
                "gas_price",
                "max_fee_per_gas",
                "max_priority_fee_per_gas",
                "max_fee_per_blob_gas",
                "max_fee",
            )
            if getattr(self, field_name) is not None
        ]
        if self.gas_price is not None and len(conflicting_fee_fields) > 1:
            raise Transaction.InvalidFeePaymentError(*conflicting_fee_fields)

        if "ty" not in self.model_fields_set:
            # Try to deduce transaction type from included fields
            if self.frames is not None:
                self.ty = HexNumber(TransactionType.FRAME)
            elif self.authorization_list is not None:
                self.ty = HexNumber(4)
            elif (
                self.max_fee_per_blob_gas is not None
                or self.blob_versioned_hashes is not None
            ):
                self.ty = HexNumber(3)
            elif (
                self.max_fee_per_gas is not None
                or self.max_priority_fee_per_gas is not None
            ):
                self.ty = HexNumber(2)
            elif self.access_list is not None:
                self.ty = HexNumber(1)
            else:
                self.ty = HexNumber(0)

        if self.ty == TransactionType.FRAME and self.frames is None:
            # Type 6 is the EIP-8141 frame transaction, whose call lives
            # in its frames. A legacy-shaped type-6 transaction has no
            # valid encoding, so refuse it rather than build one with no
            # frames.
            raise ValueError(
                "a type 6 transaction is an EIP-8141 frame transaction: "
                "pass `frames` instead of `to`, `value`, `data` and "
                "`gas_limit`"
            )

        if "v" in self.model_fields_set and self.secret_key is not None:
            raise Transaction.InvalidSignaturePrivateKeyError()

        if self.frames is not None:
            # EIP-8141: Frame transactions carry an explicit sender and
            # a signature list instead of a single v/r/s signature.
            assert self.sender is not None, (
                "frame transactions require an explicit sender"
            )
            if self.signatures is None:
                # A sender holding a key signs the canonical signature
                # hash, as consumed by the default code; the entry stays
                # unsigned until the transaction is signed. Contract
                # senders authorize via their code; no protocol-validated
                # signature is required.
                self.signatures = (
                    [FrameSignature(signer=self.sender)]
                    if self.sender.key is not None
                    else []
                )
        elif "v" not in self.model_fields_set and self.secret_key is None:
            if self.sender is not None:
                self.secret_key = self.sender.key
            else:
                self.secret_key = Hash(TestPrivateKey)
                self.sender = EOA(
                    address=TestAddress, key=self.secret_key, nonce=0
                )

        # Set default values for fields that are required for certain tx types
        if self.ty <= 1 and self.gas_price is None:
            self.gas_price = HexNumber(TransactionDefaults.gas_price)
            self.model_fields_set.remove("gas_price")
        if self.ty >= 2:
            assert self.gas_price is None, (
                f"gas_price not supported for tx type {int(self.ty)}"
            )
        if self.ty >= 1 and self.access_list is None:
            self.access_list = []
        if self.ty < 1:
            assert self.access_list is None, "access_list must be None"

        if (
            self.ty >= 2
            and self.frames is None
            and self.max_fee_per_gas is None
        ):
            self.max_fee_per_gas = HexNumber(
                TransactionDefaults.max_fee_per_gas
            )
            self.model_fields_set.remove("max_fee_per_gas")
        if self.ty >= 2 and self.max_priority_fee_per_gas is None:
            self.max_priority_fee_per_gas = HexNumber(
                TransactionDefaults.max_priority_fee_per_gas
            )
            self.model_fields_set.remove("max_priority_fee_per_gas")
        if self.ty < 2:
            assert self.max_fee_per_gas is None, "max_fee_per_gas must be None"
            assert self.max_priority_fee_per_gas is None, (
                "max_priority_fee_per_gas must be None"
            )

        if self.ty == 3 and self.max_fee_per_blob_gas is None:
            self.max_fee_per_blob_gas = HexNumber(1)
            self.model_fields_set.remove("max_fee_per_blob_gas")
        if self.frames is not None:
            # EIP-8141: Frame transactions cap their total fee with
            # `max_fee` instead of a fee per gas or per blob gas, and
            # always carry blob versioned hashes.
            assert self.max_fee_per_gas is None, (
                "frame transactions set max_fee, not max_fee_per_gas"
            )
            assert self.max_fee_per_blob_gas is None, (
                "frame transactions set max_fee, not max_fee_per_blob_gas"
            )
            if self.max_fee is None:
                self.max_fee = HexNumber(TransactionDefaults.max_fee)
                self.model_fields_set.remove("max_fee")
            if self.blob_versioned_hashes is None:
                self.blob_versioned_hashes = []
        else:
            assert self.max_fee is None, "max_fee must be None"
        if self.frames is None and self.ty != 3:
            assert self.blob_versioned_hashes is None, (
                "blob_versioned_hashes must be None"
            )
            assert self.max_fee_per_blob_gas is None, (
                "max_fee_per_blob_gas must be None"
            )

        if self.ty == 4 and self.authorization_list is None:
            self.authorization_list = []
        if self.ty != 4:
            assert self.authorization_list is None, (
                "authorization_list must be None"
            )

        if self.ty != TransactionType.FRAME:
            assert self.frames is None, "frames must be None"
            assert self.signatures is None, "signatures must be None"

        if "nonce" not in self.model_fields_set and self.sender is not None:
            self.nonce = HexNumber(self.sender.get_nonce())

    def with_error(
        self, error: List[TransactionException] | TransactionException
    ) -> "Transaction":
        """Create a copy of the transaction with an added error."""
        return self.copy(error=error)

    def with_nonce(self, nonce: int) -> "Transaction":
        """Create a copy of the transaction with a modified nonce."""
        return self.copy(nonce=nonce)

    @cached_property
    def signature_bytes(self) -> Bytes:
        """Returns the serialized bytes of the transaction signature."""
        assert "v" in self.model_fields_set, "transaction must be signed"
        v = int(self.v)
        if self.ty == 0:
            if self.protected:
                assert self.chain_id is not None
                v -= 35 + (self.chain_id * 2)
            else:
                v -= 27
        return Bytes(
            self.r.to_bytes(32, byteorder="big")
            + self.s.to_bytes(32, byteorder="big")
            + bytes([v])
        )

    @property
    def fees(self) -> List[HexNumber]:
        """
        Return the frame transaction's nested `fees` RLP list:
        `[max_fee, max_priority_fee_per_gas]`.
        """
        assert self.max_fee is not None
        assert self.max_priority_fee_per_gas is not None
        return [self.max_fee, self.max_priority_fee_per_gas]

    @property
    def signing_signatures(self) -> List[FrameSignature]:
        """
        Return the signature entries as included in the canonical frame
        transaction signature hash: entries with an empty `msg` have
        their raw `signature` bytes replaced by their length, encoded as
        an unsigned integer.
        """
        assert self.signatures is not None
        return [
            sig.model_copy(
                update={"signature": Bytes(int_to_bytes(len(sig.signature)))}
            )
            if len(sig.msg) == 0
            else sig
            for sig in self.signatures
        ]

    def frame_settlement(
        self, fork: Fork, *, refund: int = 0
    ) -> FrameSettlement:
        """
        Return how the frame transaction's gas settles under `fork`, from
        its frames' expected receipts and the `refund` its execution
        earns before the cap.

        The frames' budgets must already be settled, which
        `expect_frame_receipts` does.
        """
        assert self.frames is not None, "not a frame transaction"
        assert self.signatures is not None
        receipts = [frame.receipt(fork) for frame in self.frames]
        anchors: Dict[str, Any] = dict(
            frames=self.frames,
            signatures=self.signatures,
            sender=self.sender,
        )
        intrinsic = fork.frame_transaction_intrinsic_cost_calculator()(
            return_cost_deducted_prior_execution=True, **anchors
        )
        execution_gas = intrinsic + sum(
            int(receipt.gas_used or 0) for receipt in receipts
        )
        state_gas = sum(
            int(receipt.state_gas_used or 0) for receipt in receipts
        )
        return FrameSettlement(
            execution_gas=execution_gas,
            state_gas=state_gas,
            calldata_floor=(
                fork.frame_transaction_data_floor_cost_calculator()(**anchors)
            ),
            effective_refund=min(
                refund,
                (execution_gas + state_gas) // fork.max_refund_quotient(),
            ),
        )

    def expect_frame_receipts(
        self,
        fork: Fork,
        *,
        payer: Address | None = None,
        refund: int = 0,
        settle: bool = True,
    ) -> Self:
        """
        Settle the budgets the frames declare as deltas on their cost, and
        expect the receipt the frames' outcomes follow from. A frame whose
        `warm` is unset is warm when its resolved target is the sender or a
        precompile.

        The receipt names `payer`, the sender by default, and pins the
        gas the payer is charged, after `refund`. `settle=False` leaves
        that total unpinned for a test that prices neither the refund nor
        the floor; so does any frame whose execution gas is unpinned,
        since the total follows from every receipt. A transaction expected
        to be rejected carries no receipt expectation at all.
        """
        assert self.frames is not None, "not a frame transaction"
        assert self.expected_receipt is None, (
            "the receipt follows from the frames, so it is never given"
        )
        # The transaction starts with the sender and the precompiles warm,
        # and they stay warm: a frame's revert only restores the warmth the
        # frame started with. Other warm targets, such as the coinbase or
        # an address an earlier frame touched, are set explicitly.
        initially_warm = {Address(a) for a in fork.precompiles()}
        if self.sender is not None:
            initially_warm.add(Address(self.sender))
        for frame in self.frames:
            if "warm" in frame.model_fields_set:
                continue
            resolved_target = (
                frame.target if frame.target is not None else self.sender
            )
            if (
                resolved_target is not None
                and Address(resolved_target) in initially_warm
            ):
                frame.warm = True
        for frame in self.frames:
            frame.settle_budgets(fork)
        self._drop_cached_properties()
        if self.error is not None:
            return self

        receipts = [frame.receipt(fork) for frame in self.frames]
        settled = settle and all(
            receipt.gas_used is not None for receipt in receipts
        )
        self.expected_receipt = TransactionReceipt(
            payer=payer if payer is not None else self.sender,
            cumulative_gas_used=(
                self.frame_settlement(fork, refund=refund).payer_gas_used()
                if settled
                else None
            ),
            frame_receipts=receipts,
        )
        return self

    def _drop_cached_properties(self) -> None:
        """
        Drop every cached property value, so that each is computed again
        from the current fields on its next access.
        """
        for klass in type(self).__mro__:
            for name, attribute in vars(klass).items():
                if isinstance(attribute, cached_property):
                    self.__dict__.pop(name, None)

    def _sign_frame_signatures(self) -> None:
        """
        Fill in the raw signature bytes of the frame transaction's
        signature entries.

        Entries with an explicit 32-byte `msg` were signed when built, so
        their raw bytes are in place before the canonical hash commits to
        them.
        """
        assert self.frames is not None
        assert self.signatures is not None
        assert all(
            frame.settled or not frame.requires_settlement
            for frame in self.frames
        ), (
            "the frames' expectations only take effect once settled: call "
            "`expect_frame_receipts` before encoding the transaction"
        )

        # Explicit-digest entries are already signed, as they are built.
        # The canonical signature hash commits to the length of each
        # empty-msg entry's raw bytes, so reserve the signature's length
        # before hashing.
        empty_msg_entries = []
        for sig in self.signatures:
            if len(sig.msg) != 0 or len(sig.signature) != 0:
                continue
            signer = sig.signed_by
            if signer is not None:
                sig.signature = Bytes(bytes(signer.signature_length))
                empty_msg_entries.append((sig, signer))

        sig_hash = self.rlp_signing_bytes().keccak256()
        for sig, signer in empty_msg_entries:
            sig.signed_over(sig_hash, signer)

    def sign(self: "Transaction") -> None:
        """
        Sign the transaction.

        Set `v`, `r` and `s` from `secret_key` or the sender's key. For a
        frame transaction, fill in the raw bytes of its unsigned signature
        entries instead.
        """
        if self.frames is not None:
            self._sign_frame_signatures()
            return
        needs_signature = (
            "v" not in self.model_fields_set
            and "r" not in self.model_fields_set
            and "s" not in self.model_fields_set
        )
        if not needs_signature and self.sender is not None:
            return
        signature_bytes: bytes | None = None
        rlp_signing_bytes = self.rlp_signing_bytes()
        if needs_signature:
            signing_key: Hash | None = None
            if self.secret_key is not None:
                signing_key = self.secret_key
                self.secret_key = None
            elif self.sender is not None:
                eoa = self.sender
                assert eoa is not None, "signer must be set"
                signing_key = eoa.key
            assert signing_key is not None, "secret_key or signer must be set"

            signature_bytes = PrivateKey(signing_key).sign_recoverable(
                rlp_signing_bytes.keccak256()
            )
            v, r, s = (
                signature_bytes[64],
                int.from_bytes(signature_bytes[0:32], byteorder="big"),
                int.from_bytes(signature_bytes[32:64], byteorder="big"),
            )
            if self.ty == 0:
                if self.protected:
                    v += 35 + (self.chain_id * 2)
                else:  # not protected
                    v += 27
            self.v, self.r, self.s = (HexNumber(v), HexNumber(r), HexNumber(s))
            self.model_fields_set.add("v")
            self.model_fields_set.add("r")
            self.model_fields_set.add("s")

        if self.sender is None:
            try:
                if not signature_bytes:
                    v = self.v
                    if self.ty == 0:
                        if v > 28:
                            v -= 35 + (self.chain_id * 2)
                        else:  # not protected
                            v -= 27
                    signature_bytes = (
                        int(self.r).to_bytes(32, byteorder="big")
                        + int(self.s).to_bytes(32, byteorder="big")
                        + bytes([v])
                    )
                public_key = PublicKey.from_signature_and_message(
                    signature_bytes, rlp_signing_bytes.keccak256()
                )
                self.sender = EOA(
                    address=Address(
                        keccak256(public_key.format(compressed=False)[1:])[
                            32 - 20 :
                        ]
                    )
                )
            except Exception:
                # Signer remains `None` in this case
                pass

    def _calculate_implicit_gas_limit(
        self,
        *,
        max_gas_limit: int,
        transaction_gas_limit_cap: int | None,
        state_gas_reservoir_enabled: bool = False,
        transaction_total_gas_limit_cap: int | None = None,
    ) -> HexNumber:
        """
        Calculate the gas limit given the current external factors.

        The implicit gas limit defaults to `max_gas_limit`, clamped to
        the fork's transaction gas limit cap if there is one. On forks
        with the state gas reservoir enabled (EIP-8037),
        `state_gas_reservoir` refines this: unset keeps the full
        `max_gas_limit` (any excess above the cap acts as an implicit
        reservoir), an explicit 0 pins the gas limit to exactly the
        cap, and a positive value pins it to the cap plus the requested
        reservoir. The result never exceeds the fork's transaction total
        gas limit cap (EIP-8037's bound on `tx.gas` as a whole) if there
        is one; a reservoir request that would is a test correctness
        error.
        """
        tx_gas_limit = max_gas_limit
        if (
            transaction_total_gas_limit_cap is not None
            and tx_gas_limit > transaction_total_gas_limit_cap
        ):
            tx_gas_limit = transaction_total_gas_limit_cap
        if state_gas_reservoir_enabled:
            if "state_gas_reservoir" in self.model_fields_set:
                assert transaction_gas_limit_cap is not None, (
                    "state_gas_reservoir_enabled is True but "
                    "transaction_gas_limit_cap is None; the state "
                    "gas reservoir is defined as gas above the cap "
                    "(EIP-8037 builds on EIP-7825), so a fork that "
                    "enables it must also define a cap"
                )
                if self.state_gas_reservoir > 0:
                    minimum_gas_with_reservoir = (
                        transaction_gas_limit_cap + self.state_gas_reservoir
                    )
                    if (
                        transaction_total_gas_limit_cap is not None
                        and minimum_gas_with_reservoir
                        > transaction_total_gas_limit_cap
                    ):
                        raise Exception(
                            "test correctness: the requested state "
                            "gas reservoir of "
                            f"{self.state_gas_reservoir} puts the gas "
                            f"limit at {minimum_gas_with_reservoir} "
                            "(transaction gas limit cap of "
                            f"{transaction_gas_limit_cap} plus "
                            "reservoir), above the transaction total "
                            "gas limit cap of "
                            f"{transaction_total_gas_limit_cap}."
                        )
                    if tx_gas_limit < minimum_gas_with_reservoir:
                        raise Exception(
                            "test correctness: the requested state "
                            "gas reservoir of "
                            f"{self.state_gas_reservoir} requires a "
                            f"gas limit of {minimum_gas_with_reservoir} "
                            "(transaction gas limit cap of "
                            f"{transaction_gas_limit_cap} plus "
                            "reservoir), but only "
                            f"{tx_gas_limit} gas is available for "
                            "this transaction."
                        )
                    tx_gas_limit = minimum_gas_with_reservoir
                else:
                    if tx_gas_limit > transaction_gas_limit_cap:
                        tx_gas_limit = transaction_gas_limit_cap
        else:
            if (
                transaction_gas_limit_cap is not None
                and tx_gas_limit > transaction_gas_limit_cap
            ):
                tx_gas_limit = transaction_gas_limit_cap
        return HexNumber(tx_gas_limit)

    def _check_state_gas_reservoir_supported(
        self, *, state_gas_reservoir_enabled: bool
    ) -> None:
        """Raise if a positive reservoir is requested but unsupported."""
        if not state_gas_reservoir_enabled and self.state_gas_reservoir > 0:
            raise Exception(
                "test correctness: transaction requests a state gas "
                f"reservoir of {self.state_gas_reservoir} but the fork "
                "does not enable the state gas reservoir; the request "
                "would be silently ignored."
            )

    def with_gas_limit(
        self,
        *,
        max_gas_limit: int,
        transaction_gas_limit_cap: int | None,
        state_gas_reservoir_enabled: bool = False,
        transaction_total_gas_limit_cap: int | None = None,
    ) -> Self:
        """Return copy of the transaction with the set gas limit."""
        updated_values: Dict[str, Any] = {}

        self._check_state_gas_reservoir_supported(
            state_gas_reservoir_enabled=state_gas_reservoir_enabled
        )
        if "gas_limit" not in self.model_fields_set:
            updated_values["gas_limit"] = self._calculate_implicit_gas_limit(
                max_gas_limit=max_gas_limit,
                transaction_gas_limit_cap=transaction_gas_limit_cap,
                state_gas_reservoir_enabled=state_gas_reservoir_enabled,
                transaction_total_gas_limit_cap=(
                    transaction_total_gas_limit_cap
                ),
            )

        return self.model_copy(update=updated_values)

    def with_signature_and_sender(
        self, *, keep_secret_key: bool = False
    ) -> Self:
        """Return signed version of the transaction using the private key."""
        updated_values: Dict[str, Any] = {}

        if self.frames is not None:
            # EIP-8141: The sender is explicit; fill in the signature
            # entries instead of v/r/s. Sign a copy, as the other types
            # return one: the entries are signed in place, so signing
            # `self` would also sign a transaction the caller keeps. The
            # copy is shallow, like the other types', so the entries are
            # copied too. It also carries over any hash or encoding the
            # caller cached before signing, which signing makes stale.
            signed = self.model_copy(
                update={
                    "signatures": (
                        None
                        if self.signatures is None
                        else [sig.model_copy() for sig in self.signatures]
                    )
                }
            )
            signed._drop_cached_properties()
            signed._sign_frame_signatures()
            return signed

        if (
            "v" in self.model_fields_set
            or "r" in self.model_fields_set
            or "s" in self.model_fields_set
        ):
            # Transaction already signed
            if self.sender is not None:
                return self

            public_key = PublicKey.from_signature_and_message(
                self.signature_bytes,
                self.rlp_signing_bytes().keccak256(),
            )
            updated_values["sender"] = Address(
                keccak256(public_key.format(compressed=False)[1:])[32 - 20 :]
            )
            return self.copy(**updated_values)

        if self.secret_key is None:
            raise ValueError("secret_key must be set to sign a transaction")

        if "gas_limit" not in self.model_fields_set:
            raise ValueError("gas_limit must be set to sign a transaction")

        # Get the signing bytes
        signing_hash = self.rlp_signing_bytes().keccak256()

        # Sign the bytes
        signing_key = PrivateKey(self.secret_key)
        signature_bytes = signing_key.sign_recoverable(signing_hash)

        # The key comparison is what makes reusing `sender` safe: it is
        # reassignable and `EOA.key` may be `None`, so a sender that does not
        # hold the signing key would contradict its own signature.
        if self.sender is not None and self.sender.key == self.secret_key:
            updated_values["sender"] = self.sender
        else:
            # The address the public key recovery would return, since the
            # signature was produced by this key, but derived with one point
            # multiplication instead.
            public_key = signing_key.public_key
            updated_values["sender"] = Address(
                keccak256(public_key.format(compressed=False)[1:])[32 - 20 :]
            )

        v, r, s = (
            signature_bytes[64],
            int.from_bytes(signature_bytes[0:32], byteorder="big"),
            int.from_bytes(signature_bytes[32:64], byteorder="big"),
        )
        if self.ty == 0:
            if self.protected:
                v += 35 + (self.chain_id * 2)
            else:  # not protected
                v += 27

        updated_values["v"] = HexNumber(v)
        updated_values["r"] = HexNumber(r)
        updated_values["s"] = HexNumber(s)

        updated_values["secret_key"] = None

        updated_tx = self.model_copy(update=updated_values)

        # Remove the secret key if requested
        if keep_secret_key:
            updated_tx.secret_key = self.secret_key
        return updated_tx

    def get_rlp_signing_fields(self) -> List[str]:
        """
        Return the list of values included in the envelope used for signing
        depending on the transaction type.
        """
        field_list: List[str]
        if self.ty == TransactionType.FRAME:
            # EIP-8141: https://eips.ethereum.org/EIPS/eip-8141
            field_list = [
                "chain_id",
                "nonce",
                "sender",
                "frames",
                "signing_signatures",
                "fees",
                "blob_versioned_hashes",
            ]
        elif self.ty == 4:
            # EIP-7702: https://eips.ethereum.org/EIPS/eip-7702
            field_list = [
                "chain_id",
                "nonce",
                "max_priority_fee_per_gas",
                "max_fee_per_gas",
                "gas_limit",
                "to",
                "value",
                "data",
                "access_list",
                "authorization_list",
            ]
        elif self.ty == 3:
            # EIP-4844: https://eips.ethereum.org/EIPS/eip-4844
            field_list = [
                "chain_id",
                "nonce",
                "max_priority_fee_per_gas",
                "max_fee_per_gas",
                "gas_limit",
                "to",
                "value",
                "data",
                "access_list",
                "max_fee_per_blob_gas",
                "blob_versioned_hashes",
            ]
        elif self.ty == 2:
            # EIP-1559: https://eips.ethereum.org/EIPS/eip-1559
            field_list = [
                "chain_id",
                "nonce",
                "max_priority_fee_per_gas",
                "max_fee_per_gas",
                "gas_limit",
                "to",
                "value",
                "data",
                "access_list",
            ]
        elif self.ty == 1:
            # EIP-2930: https://eips.ethereum.org/EIPS/eip-2930
            field_list = [
                "chain_id",
                "nonce",
                "gas_price",
                "gas_limit",
                "to",
                "value",
                "data",
                "access_list",
            ]
        elif self.ty == 0:
            field_list = [
                "nonce",
                "gas_price",
                "gas_limit",
                "to",
                "value",
                "data",
            ]
            if self.protected:
                # EIP-155: https://eips.ethereum.org/EIPS/eip-155
                field_list.extend(["chain_id", "zero", "zero"])
        else:
            raise NotImplementedError(
                f"signing for transaction type {self.ty} not implemented"
            )

        for field in field_list:
            if field != "to":
                assert getattr(self, field) is not None, (
                    f"{field} must be set for type {self.ty} tx"
                )
        return field_list

    def get_rlp_fields(self) -> List[str]:
        """
        Return the list of values included in the list used for rlp encoding
        depending on the transaction type.
        """
        fields = self.get_rlp_signing_fields()
        if self.ty == TransactionType.FRAME and self.frames is not None:
            # EIP-8141: The transaction is not wrapped in a signature;
            # the full encoding carries the raw signature entries.
            return [
                "signatures" if field == "signing_signatures" else field
                for field in fields
            ]
        if self.ty == 0 and self.protected:
            fields = fields[:-3]
        return fields + ["v", "r", "s"]

    def get_rlp_prefix(self) -> bytes:
        """
        Return the transaction type as bytes to be appended at the beginning of
        the serialized transaction if type is not 0.
        """
        if self.ty > 0:
            return bytes([self.ty])
        return b""

    def get_rlp_signing_prefix(self) -> bytes:
        """
        Return the transaction type as bytes to be appended at the beginning of
        the serialized transaction signing envelope if type is not 0.
        """
        if self.ty > 0:
            return bytes([self.ty])
        return b""

    def metadata_string(self) -> str | None:
        """Return the metadata field as a formatted json string or None."""
        if self.metadata is None:
            return None
        return self.metadata.to_json()

    @cached_property
    def hash(self) -> Hash:
        """Returns hash of the transaction."""
        return self.rlp().keccak256()

    @cached_property
    def serializable_list(self) -> Any:
        """
        Return list of values included in the transaction as a serializable
        object.
        """
        return self.rlp() if self.ty > 0 else self.to_list(signing=False)

    @cached_property
    def serializable_size(self) -> int:
        """
        Return the encoded size of `serializable_list`, without building the
        encoding.
        """
        if self.ty == 0:
            return encoded_size(self.serializable_list)
        # A typed transaction is embedded as an opaque byte string, never
        # short enough to encode as a single byte.
        return encoded_prefixed_size(self.rlp_size())

    @staticmethod
    def list_blob_versioned_hashes(
        input_txs: List["Transaction"],
    ) -> List[Hash]:
        """
        Get list of ordered blob versioned hashes from a list of transactions.
        """
        return [
            blob_versioned_hash
            for tx in input_txs
            if tx.blob_versioned_hashes is not None
            for blob_versioned_hash in tx.blob_versioned_hashes
        ]

    @staticmethod
    def calculate_max_gas_limit(
        *,
        txs: List["Transaction"],
        env_gas_limit: int,
        transaction_gas_limit_cap: int | None,
        state_gas_reservoir_enabled: bool,
        transaction_total_gas_limit_cap: int | None = None,
    ) -> int:
        """
        Calculate the maximum gas limit that can be set in a transaction
        given a list of transactions with and without gas-limits set
        and a maximum available environment gas.

        The share is clamped to the transaction gas limit cap on forks
        without the state gas reservoir, and always to the transaction
        total gas limit cap if there is one.
        """
        available_gas = env_gas_limit
        unset_gas_limit_tx_count = 0
        for tx in txs:
            if "gas_limit" not in tx.model_fields_set:
                unset_gas_limit_tx_count += 1
            else:
                available_gas -= int(tx.gas_limit)

        if unset_gas_limit_tx_count == 0:
            return 0

        if available_gas <= 0:
            raise Exception(
                "test correctness: unable to automatically calculate gas "
                "limit for transactions (no remaining gas: explicit "
                "transaction gas limits already consume the full "
                f"environment gas limit of {env_gas_limit})."
            )

        max_tx_gas_limit = available_gas // unset_gas_limit_tx_count
        if state_gas_reservoir_enabled:
            transaction_gas_limit_cap = None
        if transaction_gas_limit_cap:
            max_tx_gas_limit = min(max_tx_gas_limit, transaction_gas_limit_cap)
        if transaction_total_gas_limit_cap:
            max_tx_gas_limit = min(
                max_tx_gas_limit, transaction_total_gas_limit_cap
            )
        return max_tx_gas_limit

    @cached_property
    def created_contract(self) -> Address:
        """Return address of the contract created by the transaction."""
        if self.to is not None:
            raise ValueError("transaction is not a contract creation")
        if self.sender is None:
            raise ValueError("sender address is None")
        hash_bytes = Bytes(
            eth_rlp.encode([self.sender, int_to_bytes(self.nonce)])
        ).keccak256()
        return Address(hash_bytes[-20:])

    def set_gas_price(
        self,
        *,
        gas_price: int,
        max_fee_per_gas: int,
        max_priority_fee_per_gas: int,
        max_fee_per_blob_gas: int,
    ) -> None:
        """
        Set the gas price to the appropriate values of the current
        execution environment.

        Values are only set if they were not
         set during instance creation.
        """
        if self.ty <= 1:
            if "gas_price" not in self.model_fields_set:
                self.gas_price = HexNumber(gas_price)
        elif self.frames is not None:
            # A frame transaction's `max_fee` budget has no per-gas
            # environment value to take.
            if "max_priority_fee_per_gas" not in self.model_fields_set:
                self.max_priority_fee_per_gas = HexNumber(
                    max_priority_fee_per_gas
                )
        else:
            if "max_fee_per_gas" not in self.model_fields_set:
                self.max_fee_per_gas = HexNumber(max_fee_per_gas)
            if "max_priority_fee_per_gas" not in self.model_fields_set:
                self.max_priority_fee_per_gas = HexNumber(
                    max_priority_fee_per_gas
                )
            if self.ty == 3:
                if "max_fee_per_blob_gas" not in self.model_fields_set:
                    self.max_fee_per_blob_gas = HexNumber(max_fee_per_blob_gas)

    def set_gas_limit(
        self,
        *,
        max_gas_limit: int,
        transaction_gas_limit_cap: int | None,
        state_gas_reservoir_enabled: bool = False,
        transaction_total_gas_limit_cap: int | None = None,
    ) -> None:
        """Set the transaction gas limit if unset."""
        self._check_state_gas_reservoir_supported(
            state_gas_reservoir_enabled=state_gas_reservoir_enabled
        )
        if "gas_limit" not in self.model_fields_set:
            self.gas_limit = self._calculate_implicit_gas_limit(
                max_gas_limit=max_gas_limit,
                transaction_gas_limit_cap=transaction_gas_limit_cap,
                state_gas_reservoir_enabled=state_gas_reservoir_enabled,
                transaction_total_gas_limit_cap=(
                    transaction_total_gas_limit_cap
                ),
            )

    def signer_minimum_balance(self, *, fork: Fork) -> int:
        """Return minimum balance of the signer."""
        if self.frames is not None:
            # A frame transaction's payer is charged at most `max_fee`.
            assert self.max_fee is not None
            return self.max_fee
        gas_price = self.gas_price or self.max_fee_per_gas
        assert gas_price is not None, (
            "Impossible to calculate minimum balance without gas price"
        )
        assert "gas_limit" in self.model_fields_set, (
            "Impossible to calculate minimum balance without a set gas limit"
        )
        if self.blob_versioned_hashes and self.ty == 3:
            max_fee_per_blob_gas = self.max_fee_per_blob_gas
            assert max_fee_per_blob_gas is not None, (
                "Impossible to calculate minimum balance without "
                "max_fee_per_blob_gas"
            )
            return (
                gas_price * self.gas_limit
                + self.value
                + max_fee_per_blob_gas
                * (fork.blob_gas_per_blob() * len(self.blob_versioned_hashes))
            )
        else:
            return gas_price * self.gas_limit + self.value

    def _format_field_value(self, value: Any) -> str:
        """
        Format a field value for string representation.

        Uses decimal for numeric values (int, HexNumber, etc.) and
        hex encoding for Address, Bytes, Hash, etc.
        """
        if value is None:
            return "None"

        # fields like 'value' should be shown as decimal number
        if isinstance(value, numbers.Number):
            # Force decimal representation for int subclasses like HexNumber
            if isinstance(value, int):
                return str(int(value))

            return str(value)

        # fields like 'to' should be shown as hex string
        if hasattr(value, "hex") and callable(value.hex):
            return f'"{value.hex()}"'

        return repr(value)

    def __repr__(self) -> str:
        """
        Return string representation with hex-encoded values for
        applicable fields.
        """
        field_strs = []
        for field_name in self.__class__.model_fields:
            value = getattr(self, field_name)
            formatted_value = self._format_field_value(value)
            field_strs.append(f"{field_name}={formatted_value}")

        return f"{self.__class__.__name__}({', '.join(field_strs)})"

    def __str__(self) -> str:
        """Return the repr string representation."""
        return self.__repr__()


class NetworkWrappedTransaction(CamelModel, RLPSerializable):
    """
    Network wrapped transaction as defined in
    [EIP-4844](https://eips.ethereum.org/EIPS/eip-4844#networking).

    < Osaka: rlp([tx_payload_body, blobs, commitments, proofs])

    >= Osaka: rlp([tx_payload_body, wrapper_version,  blobs, commitments,
                   cell_proofs])
    """

    tx: Transaction
    blob_objects: Sequence[Blob]
    wrapper_version: int | None = None  # only exists in >= osaka

    @computed_field  # type: ignore[prop-decorator]
    @property
    def blobs(self) -> Sequence[Bytes]:
        """Return a list of blob data as bytes."""
        return [blob.data for blob in self.blob_objects]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def commitments(self) -> Sequence[Bytes]:
        """Return a list of kzg commitments."""
        return [blob.commitment for blob in self.blob_objects]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def proofs(self) -> Sequence[Bytes] | None:
        """Return a list of kzg proofs (returns None >= Osaka)."""
        if self.wrapper_version is not None:
            return None

        proofs: list[Bytes] = []
        for blob in self.blob_objects:
            assert isinstance(blob.proof, Bytes)
            proofs.append(blob.proof)

        return proofs

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cell_proofs(self) -> Sequence[Bytes] | None:
        """Return a list of cells (returns None < Osaka)."""
        if self.wrapper_version is None:
            return None

        cells: list[Bytes] = []
        for blob in self.blob_objects:
            assert isinstance(blob.proof, list)
            cells.extend(blob.proof)

        return cells

    def get_rlp_fields(self) -> List[str]:
        """
        Return an ordered list of field names to be included in RLP
        serialization.

        Function can be overridden to customize the logic to return the fields.

        By default, rlp_fields class variable is used.

        The list can be nested list up to one extra level to represent nested
        fields.
        """
        # only put a wrapper_version field for >=osaka (value 1), otherwise
        # omit field
        wrapper = []
        if self.wrapper_version is not None:
            wrapper = ["wrapper_version"]

        rlp_proofs: list[str] = []
        if self.proofs is not None:
            rlp_proofs = ["proofs"]

        rlp_cell_proofs: list[str] = []
        if self.cell_proofs is not None:
            rlp_cell_proofs = ["cell_proofs"]

        rlp_fields: List[str] = [  # structure explained in
            # https://eips.ethereum.org/EIPS/eip-7594#Networking
            "tx",  # tx_payload_body
            *wrapper,  # wrapper_version, which is always 1 for osaka (was non-
            # existing before)
            "blobs",  # Blob.data
            "commitments",
            *rlp_proofs,
            *rlp_cell_proofs,
        ]

        assert ("proofs" in rlp_fields) or ("cell_proofs" in rlp_fields), (
            "Neither proofs nor cell_proofs are in rlp_fields. Critical error!"
        )

        # logger.debug(f"Ended up with this rlp field list: {rlp_fields}")

        return rlp_fields

    @property
    def hash(self) -> Hash:
        """Return the hash of the transaction."""
        return self.tx.hash

    @property
    def sender(self) -> EOA | None:
        """Return the sender of the transaction."""
        return self.tx.sender

    @property
    def to(self) -> Address | None:
        """Return the to address of the transaction."""
        return self.tx.to

    def set_gas_price(
        self,
        *,
        gas_price: int,
        max_fee_per_gas: int,
        max_priority_fee_per_gas: int,
        max_fee_per_blob_gas: int,
    ) -> None:
        """Set gas price to values of the current execution environment."""
        self.tx.set_gas_price(
            gas_price=gas_price,
            max_fee_per_gas=max_fee_per_gas,
            max_priority_fee_per_gas=max_priority_fee_per_gas,
            max_fee_per_blob_gas=max_fee_per_blob_gas,
        )

    def set_gas_limit(
        self,
        *,
        max_gas_limit: int,
        transaction_gas_limit_cap: int | None,
        state_gas_reservoir_enabled: bool = False,
        transaction_total_gas_limit_cap: int | None = None,
    ) -> None:
        """Set the transaction gas limit if unset."""
        self.tx.set_gas_limit(
            max_gas_limit=max_gas_limit,
            transaction_gas_limit_cap=transaction_gas_limit_cap,
            state_gas_reservoir_enabled=state_gas_reservoir_enabled,
            transaction_total_gas_limit_cap=transaction_total_gas_limit_cap,
        )

    def signer_minimum_balance(self, *, fork: Fork) -> int:
        """Return minimum balance of the signer."""
        return self.tx.signer_minimum_balance(fork=fork)

    def get_rlp_prefix(self) -> bytes:
        """
        Return the transaction type as bytes to be appended at the beginning of
        the serialized transaction if type is not 0.
        """
        if self.tx.ty > 0:
            return bytes([self.tx.ty])
        return b""

    def with_signature_and_sender(
        self, *, keep_secret_key: bool = False
    ) -> Self:
        """Return a new transaction with the signature and sender added."""
        return self.model_copy(
            update={
                "tx": self.tx.with_signature_and_sender(
                    keep_secret_key=keep_secret_key
                ),
            }
        )
