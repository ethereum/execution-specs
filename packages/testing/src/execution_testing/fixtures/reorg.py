"""
Reorg fixture format: a DAG of engine payloads plus an ordered, branching list
of Engine API / JSON-RPC steps with expected outcomes.

Unlike ``BlockchainEngineFixture`` (a linear payload list where the consumer
always sends ``forkchoiceUpdated(head=payload)`` after each payload), this
format lets a test describe side chains, explicit forkchoice states (head,
safe, finalized), multiple legal outcomes per step (``expect`` is a list of
outcomes; the first one that matches wins), outcome-specific follow-up steps
(``branches``), client-built payloads (``getPayload`` binds the built payload
to a new label), and transaction-pool observations.

Block labels are the identifiers used throughout: ``blocks`` maps a label to a
payload and its parent label; every hash-valued step field is a label
(``"genesis"`` is reserved for the genesis block, ``"zero"`` for the zero hash;
labels introduced by ``getPayload.bind`` are resolved at run time). The
consumer resolves labels to hashes, so fixtures are byte-identical across
clients.
"""

from typing import (
    Annotated,
    Any,
    ClassVar,
    Dict,
    List,
    Literal,
    Self,
    Tuple,
    Union,
)

from pydantic import AfterValidator, Field, model_validator

from execution_testing.base_types import (
    Account,
    Address,
    Alloc,
    Bytes,
    CamelModel,
    Hash,
    HexNumber,
    Number,
)

from .blockchain import (
    EngineAPIErrorCode,
    EngineFixtureCommon,
    FixtureHeader,
    FixtureNewPayloadRequest,
    PayloadAttributes,
    PayloadStatusEnum,
)

GENESIS_LABEL = "genesis"
ZERO_LABEL = "zero"
"""Reserved labels."""

LATEST_VALID_HASH_ANY = "any"
LATEST_VALID_HASH_NULL = "null"
"""Special values for ``Outcome.latest_valid_hash``."""

RESERVED_LABELS = frozenset(
    {GENESIS_LABEL, ZERO_LABEL, "latest", "null", "any"}
)


def _reject_reserved_label(label: str) -> str:
    """Reject a label colliding with a reserved name or RPC tag."""
    if label in RESERVED_LABELS:
        raise ValueError(f"reserved block label: {label!r}")
    return label


BlockLabel = Annotated[str, AfterValidator(_reject_reserved_label)]
"""An authored block label: any string except a reserved name."""

BlockRef = Union[BlockLabel, Literal["genesis"]]
"""A block: an authored label or ``"genesis"``."""

HashRef = Union[BlockRef, Literal["zero"]]
"""A block-hash reference: a block or ``"zero"``."""


class Outcome(CamelModel):
    """
    One legal outcome of an Engine API step.

    Every set field is a constraint; unset fields are not checked. A step's
    ``expect`` is a list of outcomes and the first matching one is selected.
    """

    id: str
    """Identifier; selects the ``branches`` entry to run when matched."""
    disputed: str | None = None
    """
    If set, the spec is ambiguous about this outcome; the value is a
    reference or rationale. A disputed outcome still passes.
    """
    status: PayloadStatusEnum | None = None
    """Expected ``payloadStatus.status``."""
    latest_valid_hash: HashRef | Literal["any", "null"] | None = None
    """
    Expected ``latestValidHash`` as a block label, ``"null"``, or ``"any"``.
    Unset means not checked.
    """
    error_code: EngineAPIErrorCode | None = None
    """Expected JSON-RPC error code."""
    any_error: bool | None = None
    """If true, any JSON-RPC error matches (for uncoded errors)."""
    head_moved: bool | None = None
    """
    ``forkchoiceUpdated`` only: whether ``latest`` equals the requested head
    right after the call. Tells an applied update from a no-op when both
    answer VALID with the same ``latestValidHash``.
    """
    validation_error: Literal["required", "none"] | None = None
    """Whether ``validationError`` must be present or absent."""
    payload_id: Literal["nonNull", "null"] | None = None
    """For ``forkchoiceUpdated`` with payload attributes."""

    @model_validator(mode="after")
    def _check_error_combination(self) -> Self:
        """
        Reject payload-status constraints alongside an error expectation.

        The matcher returns as soon as it matches ``error_code``/
        ``any_error``; a JSON-RPC error carries no payload status, so any
        other constraint on this outcome could never be enforced. Use a
        follow-up ``AssertHeadStep`` for post-error chain-state checks.
        """
        if self.error_code is not None or self.any_error:
            unenforceable = [
                field
                for field in (
                    "status",
                    "latest_valid_hash",
                    "validation_error",
                    "payload_id",
                    "head_moved",
                )
                if getattr(self, field) is not None
            ]
            if unenforceable:
                raise ValueError(
                    f"outcome {self.id!r}: error_code/any_error cannot be "
                    f"combined with {unenforceable}"
                )
        return self


class TxRef(CamelModel):
    """Reference to a transaction of a fixture block."""

    block: BlockLabel
    index: Number = Number(0)


class StepBase(CamelModel):
    """Common fields of every step."""

    description: str | None = None


class NewPayloadStep(StepBase):
    """Send ``engine_newPayloadVX`` for a labeled (or bound) block."""

    type: Literal["newPayload"] = "newPayload"
    block: BlockLabel
    expect: List[Outcome] = Field(default_factory=list)
    """Legal outcomes; filled by the reference model when left empty."""
    branches: Dict[str, List["Step"]] = Field(default_factory=dict)


class ForkchoiceUpdatedStep(StepBase):
    """Send ``engine_forkchoiceUpdatedVX`` with labeled hashes."""

    type: Literal["forkchoiceUpdated"] = "forkchoiceUpdated"
    head: HashRef
    safe: HashRef = ZERO_LABEL
    finalized: HashRef = ZERO_LABEL
    version: Number | None = None
    """
    Engine API version; when unset, that of the attributes' fork for a build
    request, else of the head block's fork.
    """
    payload_attributes: PayloadAttributes | None = None
    """
    If set, a payload build is requested; ``payloadId`` is kept for the
    next ``getPayload`` step.
    """
    expect: List[Outcome] = Field(default_factory=list)
    """Legal outcomes; filled by the reference model when left empty."""
    branches: Dict[str, List["Step"]] = Field(default_factory=dict)


class GetPayloadStep(StepBase):
    """
    Send ``engine_getPayloadVX`` with the id returned by the previous
    ``forkchoiceUpdated`` and bind the built payload to a new label.
    """

    type: Literal["getPayload"] = "getPayload"
    bind: BlockLabel
    """New label for the built payload (usable in later steps)."""
    version: Number | None = None
    parent: BlockRef
    """Expected parent of the built payload."""
    transactions_include: List[TxRef] = Field(default_factory=list)
    """Transactions that must be in the built payload."""
    transactions_exclude: List[TxRef] = Field(default_factory=list)
    """Transactions that must not be in the built payload."""


class AssertHeadStep(StepBase):
    """Assert ``eth_getBlockByNumber`` for latest / safe / finalized."""

    type: Literal["assertHead"] = "assertHead"
    latest: BlockRef | None = None
    safe: BlockRef | None = None
    finalized: BlockRef | None = None


class AssertCanonicalStep(StepBase):
    """
    Assert which block occupies each height (``eth_getBlockByNumber(n)``).

    A ``None`` value asserts that no block is canonical at that height.
    """

    type: Literal["assertCanonical"] = "assertCanonical"
    blocks: Dict[HexNumber, BlockRef | None]


class AccountExpectation(CamelModel):
    """Subset of account fields to verify."""

    balance: HexNumber | None = None
    nonce: HexNumber | None = None
    storage: Dict[Hash, Hash] | None = None


class AssertStateStep(StepBase):
    """Assert account state via ``eth_getBalance`` etc. at a block."""

    type: Literal["assertState"] = "assertState"
    at: BlockRef | Literal["latest"] = "latest"
    """Block whose own state is read; it must be canonical at that point."""
    accounts: Dict[Address, AccountExpectation]

    def verify(self, label: str, state: Alloc) -> None:
        """
        Fail unless ``state``, the post-state of ``label``, holds the
        expected fields, reading an absent account or slot as zero like
        the RPC calls do.
        """
        for address, want in self.accounts.items():
            got = state.root.get(address) or Account()
            checks: List[Tuple[str, Any, Any]] = [
                ("balance", want.balance, got.balance),
                ("nonce", want.nonce, got.nonce),
            ]
            for key, value in (want.storage or {}).items():
                stored = got.storage[key] if key in got.storage else 0
                checks.append((f"storage {key}", value, Hash(stored)))
            for field, expected, actual in checks:
                if expected is not None and expected != actual:
                    raise ValueError(
                        f"assertState at {label!r}: {field} of {address} "
                        f"is {actual}, expected {expected}"
                    )


class AssertReceiptStep(StepBase):
    """
    Assert ``eth_getTransactionReceipt`` for a fixture transaction.

    ``block`` is the label the receipt must point to; ``None`` asserts there
    is no receipt (transaction not in the canonical chain).
    """

    type: Literal["assertReceipt"] = "assertReceipt"
    tx: TxRef
    block: BlockLabel | None = None
    status: HexNumber | None = None


class AssertLogsStep(StepBase):
    """
    Assert ``eth_getLogs`` over a block range.

    ``blocks`` lists the labels whose logs must appear (one entry per expected
    log); logs from other blocks are a failure.
    """

    type: Literal["assertLogs"] = "assertLogs"
    address: Address | None = None
    from_block: HexNumber | Literal["earliest"] = "earliest"
    to_block: HexNumber | Literal["latest"] = "latest"
    blocks: List[BlockLabel]


class SendRawTransactionStep(StepBase):
    """Send a fixture transaction via ``eth_sendRawTransaction``."""

    type: Literal["sendRawTransaction"] = "sendRawTransaction"
    tx: TxRef
    expect: List[Literal["accepted", "rejected"]] = ["accepted"]
    """``rejected`` = any JSON-RPC error (e.g. already known)."""


class AssertTxStatusStep(StepBase):
    """
    Assert the pool/chain status of a fixture transaction via
    ``eth_getTransactionByHash``: ``included`` (block hash set), ``pending``
    (known, no block), ``dropped`` (unknown).
    """

    type: Literal["assertTxStatus"] = "assertTxStatus"
    tx: TxRef
    expect: List[Literal["included", "pending", "dropped"]]
    included_in: BlockLabel | None = None
    """If ``included`` matches, the block label it must be included in."""


Step = Annotated[
    Union[
        NewPayloadStep,
        ForkchoiceUpdatedStep,
        GetPayloadStep,
        AssertHeadStep,
        AssertCanonicalStep,
        AssertStateStep,
        AssertReceiptStep,
        AssertLogsStep,
        SendRawTransactionStep,
        AssertTxStatusStep,
    ],
    Field(discriminator="type"),
]

NewPayloadStep.model_rebuild()
ForkchoiceUpdatedStep.model_rebuild()


class FixtureReorgBlock(CamelModel):
    """A block of the DAG: its parent label and engine payload."""

    parent: BlockRef
    payload: FixtureNewPayloadRequest

    @property
    def block_hash(self) -> Hash:
        """Hash of the block."""
        return self.payload.params[0].block_hash

    @property
    def transactions(self) -> List[Bytes]:
        """Raw transactions of the block."""
        return self.payload.params[0].transactions


class BlockchainEngineReorgFixture(EngineFixtureCommon):
    """Engine API reorg test fixture."""

    format_name: ClassVar[str] = "blockchain_test_engine_reorg"
    description: ClassVar[str] = (
        "Tests that describe a DAG of payloads and an ordered list of "
        "Engine API / JSON-RPC steps with expected outcomes, to verify chain "
        "reorganization behavior."
    )
    transition_tool_cache_key: ClassVar[str] = "blockchain_test"

    genesis: FixtureHeader = Field(..., alias="genesisBlockHeader")
    pre: Alloc
    blocks: Dict[str, FixtureReorgBlock]
    steps: List[Step]
    min_reorg_depth: Number | None = None
    """
    Minimum side-chain reorg depth (in blocks) the client must apply
    without refusing for capacity reasons; the consumer sets the client's
    cap to it. ``None`` keeps client defaults.
    """
    meta: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_filled(self) -> Self:
        """
        Reject steps filling leaves incomplete: every ``forkchoiceUpdated``
        and ``getPayload`` has a version, every ``newPayload`` and
        ``forkchoiceUpdated`` a non-empty ``expect``.
        """

        def check(steps: List[Step]) -> None:
            for step in steps:
                if isinstance(step, (ForkchoiceUpdatedStep, GetPayloadStep)):
                    if step.version is None:
                        raise ValueError(f"{step.type} step without version")
                if isinstance(step, (NewPayloadStep, ForkchoiceUpdatedStep)):
                    if not step.expect:
                        raise ValueError(f"{step.type} step without expect")
                    for branch in step.branches.values():
                        check(branch)

        check(self.steps)
        return self

    def resolve(self, label: str) -> Hash | None:
        """
        Resolve a static label to a block hash.

        Returns ``None`` for the ``"null"`` special value. Bound labels are
        resolved by the consumer.
        """
        if label == GENESIS_LABEL:
            return self.genesis.block_hash
        if label == ZERO_LABEL:
            return Hash(0)
        if label == LATEST_VALID_HASH_NULL:
            return None
        if label not in self.blocks:
            raise KeyError(f"unknown block label: {label}")
        return self.blocks[label].block_hash

    def labels_by_hash(self) -> Dict[Hash, str]:
        """Reverse map from block hash to label (incl. genesis)."""
        result = {self.genesis.block_hash: GENESIS_LABEL}
        for label, block in self.blocks.items():
            result[block.block_hash] = label
        return result

    def tx_rlp(self, ref: TxRef) -> Bytes:
        """Raw transaction bytes referenced by ``ref``."""
        return self.blocks[ref.block].transactions[ref.index]

    def tx_hash(self, ref: TxRef) -> Hash:
        """Hash of the transaction referenced by ``ref``."""
        return Hash(self.tx_rlp(ref).keccak256())
