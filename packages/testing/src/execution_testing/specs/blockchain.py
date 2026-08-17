"""Ethereum blockchain test spec definition and filler."""

from hashlib import sha256
from pprint import pprint
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generator,
    List,
    Sequence,
    Tuple,
    Type,
)

import pytest
from pydantic import (
    ConfigDict,
    Field,
    field_validator,
    model_serializer,
)

from execution_testing.base_types import (
    Address,
    Bloom,
    Bytes,
    CamelModel,
    Hash,
    HeaderNonce,
    HexNumber,
    Number,
    ZeroPaddedHexNumber,
)
from execution_testing.client_clis import (
    BlockExceptionWithMessage,
    ClientBackend,
    FillerBackend,
    LazyAlloc,
    Result,
    TransitionTool,
)
from execution_testing.client_clis.cli_types import (
    EnginePayloadMetadata,
    OpcodeCount,
)
from execution_testing.exceptions import (
    BlockException,
    EngineAPIError,
    ExceptionWithMessage,
    TransactionException,
    UndefinedException,
)
from execution_testing.execution import (
    BaseExecute,
    ExecuteFormat,
    LabeledExecuteFormat,
    TransactionPost,
)
from execution_testing.fixtures import (
    BaseFixture,
    BlockchainEngineFixture,
    BlockchainEngineStatefulFixture,
    BlockchainEngineSyncFixture,
    BlockchainEngineXFixture,
    BlockchainFixture,
    FixtureFormat,
    LabeledFixtureFormat,
)
from execution_testing.fixtures.blockchain import (
    FixtureBlock,
    FixtureBlockBase,
    FixtureConfig,
    FixtureEngineNewPayload,
    FixtureExecutionPayloadModifier,
    FixtureHeader,
    FixtureTransaction,
    FixtureWithdrawal,
    InvalidFixtureBlock,
)
from execution_testing.fixtures.common import (
    FixtureBlobSchedule,
    FixtureTransactionReceipt,
)
from execution_testing.fixtures.post_verifications import PostVerifications
from execution_testing.forks import Fork
from execution_testing.test_types import (
    Alloc,
    Environment,
    Removable,
    Requests,
    TestPhase,
    Transaction,
    Withdrawal,
)
from execution_testing.test_types.block_access_list import (
    BlockAccessList,
    BlockAccessListExpectation,
)
from execution_testing.test_types.chain_config_types import ChainConfigDefaults

from .base import BaseTest, FillResult, OpMode, verify_result
from .debugging import print_traces
from .helpers import verify_block, verify_transactions


def environment_from_parent_header(parent: "FixtureHeader") -> "Environment":
    """Instantiate new environment with the provided header as parent."""
    return Environment(
        parent_difficulty=parent.difficulty,
        parent_timestamp=parent.timestamp,
        parent_base_fee_per_gas=parent.base_fee_per_gas,
        parent_blob_gas_used=parent.blob_gas_used,
        parent_excess_blob_gas=parent.excess_blob_gas,
        parent_gas_used=parent.gas_used,
        parent_gas_limit=parent.gas_limit,
        parent_ommers_hash=parent.ommers_hash,
        block_hashes={parent.number: parent.block_hash},
    )


def apply_new_parent(
    env: Environment, new_parent: FixtureHeader
) -> "Environment":
    """Apply header as parent to a copy of this environment."""
    updated: Dict[str, Any] = {}
    updated["parent_difficulty"] = new_parent.difficulty
    updated["parent_timestamp"] = new_parent.timestamp
    updated["parent_base_fee_per_gas"] = new_parent.base_fee_per_gas
    updated["parent_blob_gas_used"] = new_parent.blob_gas_used
    updated["parent_excess_blob_gas"] = new_parent.excess_blob_gas
    updated["parent_gas_used"] = new_parent.gas_used
    updated["parent_gas_limit"] = new_parent.gas_limit
    updated["parent_ommers_hash"] = new_parent.ommers_hash
    updated["parent_slot_number"] = new_parent.slot_number
    block_hashes = env.block_hashes.copy()
    block_hashes[new_parent.number] = new_parent.block_hash
    updated["block_hashes"] = block_hashes
    return env.copy(**updated)


def count_blobs(txs: List[Transaction]) -> int:
    """Return number of blobs in a list of transactions."""
    return sum(
        [
            len(tx.blob_versioned_hashes)
            for tx in txs
            if tx.blob_versioned_hashes is not None
        ]
    )


def payload_metadata_to_fixture(
    meta: EnginePayloadMetadata,
    *,
    phase: TestPhase | None = None,
) -> FixtureEngineNewPayload:
    """
    Materialise an ``EnginePayloadMetadata`` into a fixture payload.

    The client's ``execution_payload`` is forwarded verbatim — rebuilding
    from fill's ``FixtureHeader`` would disagree on client-chosen fields
    (``gas_limit``, etc.) and produce a mismatched ``block_hash``.
    """
    version = meta.new_payload_version
    response = meta.payload_response
    params: List[Any] = [response.execution_payload]
    if version >= 3:
        blob_hashes = (
            response.blobs_bundle.blob_versioned_hashes()
            if response.blobs_bundle is not None
            else []
        )
        params.append(blob_hashes)
        params.append(meta.parent_beacon_block_root)
    if version >= 4 and response.execution_requests is not None:
        params.append(response.execution_requests)
    return FixtureEngineNewPayload(
        params=tuple(params),
        new_payload_version=version,
        forkchoice_updated_version=meta.forkchoice_updated_version,
        phase=phase,
    )


class Header(CamelModel):
    """Header type used to describe block header properties in test specs."""

    parent_hash: Hash | None = None
    ommers_hash: Hash | None = None
    fee_recipient: Address | None = None
    state_root: Hash | None = None
    transactions_trie: Hash | None = None
    receipts_root: Hash | None = None
    logs_bloom: Bloom | None = None
    difficulty: HexNumber | None = None
    number: HexNumber | None = None
    gas_limit: HexNumber | None = None
    gas_used: HexNumber | None = None
    timestamp: HexNumber | None = None
    extra_data: Bytes | None = None
    prev_randao: Hash | None = None
    nonce: HeaderNonce | None = None
    base_fee_per_gas: Removable | HexNumber | None = None
    withdrawals_root: Removable | Hash | None = None
    blob_gas_used: Removable | HexNumber | None = None
    excess_blob_gas: Removable | HexNumber | None = None
    parent_beacon_block_root: Removable | Hash | None = None
    requests_hash: Removable | Hash | None = None
    block_access_list_hash: Removable | Hash | None = None
    slot_number: Removable | HexNumber | None = None

    REMOVE_FIELD: ClassVar[Removable] = Removable()
    """
    Sentinel object used to specify that a header field should be removed.
    """
    EMPTY_FIELD: ClassVar[Removable] = Removable()
    """
    Sentinel object used to specify that a header field must be empty during
    verification.

    This can be used in a test to explicitly skip a field in a block's RLP
    encoding that would otherwise be included in the (json) output when the
    model is serialized. For example:

    ```
    header_modifier = Header(
        excess_blob_gas=Header.REMOVE_FIELD,
    )
    block = Block(
        timestamp=TIMESTAMP,
        rlp_modifier=header_modifier,
        exception=BlockException.INCORRECT_BLOCK_FORMAT,
        engine_api_error_code=EngineAPIError.InvalidParams,
    )
    ```
    """

    model_config = ConfigDict(
        **CamelModel.model_config,
        arbitrary_types_allowed=True,
    )

    @model_serializer(mode="wrap", when_used="json")
    def _serialize_model(self, serializer: Any, info: Any) -> Dict[str, Any]:
        """Exclude Removable fields from serialization."""
        del info
        data = serializer(self)
        return {k: v for k, v in data.items() if not isinstance(v, Removable)}

    @field_validator("withdrawals_root", mode="before")
    @classmethod
    def validate_withdrawals_root(cls, value: Any) -> Any:
        """Convert a list of withdrawals into the withdrawals root hash."""
        if isinstance(value, list):
            return Withdrawal.list_root(value)
        return value

    def apply(self, target: FixtureHeader) -> FixtureHeader:
        """
        Produce a fixture header copy with the set values from the modifier.
        """
        overrides = {
            k: (v if v is not Header.REMOVE_FIELD else None)
            for k, v in self.model_dump(exclude_none=True).items()
        }
        unknown = overrides.keys() - target.__class__.model_fields.keys()
        if unknown:
            raise ValueError(
                f"Header fields {unknown} do not exist on "
                f"{target.__class__.__name__}. Check for field name "
                f"mismatches between Header and {target.__class__.__name__}."
            )
        return target.copy(**overrides)

    def verify(self, target: FixtureHeader) -> None:
        """Verify that the header fields from self are as expected."""
        for field_name in self.__class__.model_fields:
            baseline_value = getattr(self, field_name)
            if baseline_value is not None:
                assert baseline_value is not Header.REMOVE_FIELD, (
                    "invalid header"
                )
                value = getattr(target, field_name)
                if baseline_value is Header.EMPTY_FIELD:
                    assert value is None, (
                        f"invalid header field {field_name}, "
                        f"got {value}, want None"
                    )
                    continue
                assert value == baseline_value, (
                    f"invalid header field ({field_name}) value, "
                    + f"got {value}, want {baseline_value}"
                )


BLOCK_EXCEPTION_TYPE = (
    List[TransactionException | BlockException]
    | TransactionException
    | BlockException
    | None
)


class Block(Header):
    """Block type used to describe block properties in test specs."""

    header_verify: Header | None = None
    # If set, the block header will be verified against the specified values.
    rlp_modifier: Header | None = None
    """
    An RLP modifying header which values would be used to override the ones
    returned by the `ethereum_clis.TransitionTool`.
    """
    expected_block_access_list: BlockAccessListExpectation | None = None
    """
    If set, the block access list will be verified and potentially corrupted
    for invalid tests.
    """
    exception: BLOCK_EXCEPTION_TYPE = None
    # If set, the block is expected to be rejected by the client.
    skip_exception_verification: bool = False
    """
    Skip verifying that the exception is returned by the transition tool. This
    could be because the exception is inserted in the block after the
    transition tool evaluates it.
    """
    engine_api_error_code: EngineAPIError | None = None
    """
    If set, the block is expected to produce an error response from the Engine
    API.
    """
    include_receipts_in_output: bool | None = None
    """
    If set to `True`, the block’s output fixture representation will include
    full transaction receipts. If unset, the test-level value is used.
    """
    txs: List[Transaction] = Field(default_factory=list)
    """List of transactions included in the block."""
    ommers: List[Header] | None = None
    """List of ommer headers included in the block."""
    withdrawals: List[Withdrawal] | None = None
    """List of withdrawals to perform for this block."""
    requests: List[Bytes] | None = None
    """Custom list of requests to embed in this block."""
    expected_post_state: Alloc | None = None
    """Post state for verification after block execution in BlockchainTest"""
    block_access_list: Bytes | None = Field(None)
    """EIP-7928: Block-level access lists (serialized)."""
    engine_new_payload_block_access_list: Bytes | None = None
    """EIP-7928: override only the engine newPayload blockAccessList field."""
    engine_new_payload_slot_number: HexNumber | None = None
    """EIP-7843: override only the engine payload slotNumber field."""
    expected_gas_used: int | None = None
    """Expected gas used for the block."""

    @property
    def phase(self) -> TestPhase | None:
        """
        Return the single phase shared by all txs, or ``None`` when the
        block has no phase-tagged txs.

        Mixed-phase blocks must be split via ``_split_blocks_by_phase``
        before this property is read — they would otherwise need an
        arbitrary tiebreaker, which is a bug, not a default.
        """
        phases = {_tx_phase(tx) for tx in self.txs}
        phases.discard(None)
        if not phases:
            return None
        if len(phases) == 1:
            return next(iter(phases))
        raise AssertionError(
            f"Block.phase called on mixed-phase block (phases={phases}); "
            "split via _split_blocks_by_phase first."
        )

    def set_environment(self, env: Environment) -> Environment:
        """
        Create copy of the environment with the characteristics of this
        specific block.
        """
        new_env_values: Dict[str, Any] = {}

        """
        Values that need to be set in the environment and are `None` for this
        block need to be set to their defaults.
        """
        new_env_values["difficulty"] = self.difficulty
        new_env_values["prev_randao"] = self.prev_randao
        new_env_values["fee_recipient"] = (
            self.fee_recipient
            if self.fee_recipient is not None
            else Environment().fee_recipient
        )
        new_env_values["gas_limit"] = (
            self.gas_limit or env.parent_gas_limit or Environment().gas_limit
        )
        if not isinstance(self.base_fee_per_gas, Removable):
            new_env_values["base_fee_per_gas"] = self.base_fee_per_gas
        new_env_values["withdrawals"] = self.withdrawals
        if not isinstance(self.excess_blob_gas, Removable):
            new_env_values["excess_blob_gas"] = self.excess_blob_gas
        if not isinstance(self.blob_gas_used, Removable):
            new_env_values["blob_gas_used"] = self.blob_gas_used
        if not isinstance(self.parent_beacon_block_root, Removable):
            new_env_values["parent_beacon_block_root"] = (
                self.parent_beacon_block_root
            )
        if (
            not isinstance(self.requests_hash, Removable)
            and self.block_access_list is not None
        ):
            new_env_values["block_access_list_hash"] = (
                self.block_access_list.keccak256()
            )
            new_env_values["block_access_list"] = self.block_access_list
        if (
            not isinstance(self.block_access_list, Removable)
            and self.block_access_list is not None
        ):
            new_env_values["block_access_list"] = self.block_access_list
        if not isinstance(self.slot_number, Removable):
            new_env_values["slot_number"] = self.slot_number
        """
        These values are required, but they depend on the previous environment,
        so they can be calculated here.
        """
        if self.number is not None:
            new_env_values["number"] = self.number
        else:
            # calculate the next block number for the environment
            if len(env.block_hashes) == 0:
                new_env_values["number"] = 0
            else:
                new_env_values["number"] = (
                    max([Number(n) for n in env.block_hashes.keys()]) + 1
                )

        if self.timestamp is not None:
            new_env_values["timestamp"] = self.timestamp
        else:
            assert env.parent_timestamp is not None
            new_env_values["timestamp"] = int(
                Number(env.parent_timestamp) + 12
            )

        return env.copy(**new_env_values)


class BuiltBlock(CamelModel):
    """Model that contains all properties to build a full block or payload."""

    header: FixtureHeader
    env: Environment
    alloc: LazyAlloc | Alloc
    state_root: Hash
    txs: List[Transaction]
    ommers: List[FixtureHeader]
    withdrawals: List[Withdrawal] | None
    requests: List[Bytes] | None
    result: Result
    expected_exception: BLOCK_EXCEPTION_TYPE = None
    engine_api_error_code: EngineAPIError | None = None
    rlp_modifier: Header | None = None
    fork: Fork
    block_access_list: BlockAccessList | None
    engine_new_payload_block_access_list: Bytes | None = None
    engine_new_payload_slot_number: HexNumber | None = None

    def cumulative_gas_used(self) -> int:
        """Return the last receipt's cumulative gas used."""
        if not self.result.receipts:
            return int(self.result.gas_used)
        cumulative_gas_used = self.result.receipts[-1].cumulative_gas_used
        if cumulative_gas_used is None:
            return int(self.result.gas_used)
        return int(cumulative_gas_used)

    def block_gas_used(self) -> int:
        """
        Return the block-header gas used.

        Under EIP-8037 this is the maximum across the independent gas
        dimensions (execution vs state), i.e. the value that counts against the
        block gas limit, as opposed to ``cumulative_gas_used`` which is their
        combined sum.
        """
        return int(self.result.gas_used)

    def get_fixture_block(
        self, *, include_receipts: bool = True
    ) -> FixtureBlock | InvalidFixtureBlock:
        """Get a FixtureBlockBase from the built block."""
        fixture_block = FixtureBlockBase(
            header=self.header,
            txs=[FixtureTransaction.from_transaction(tx) for tx in self.txs],
            withdrawals=(
                [
                    FixtureWithdrawal.from_withdrawal(w)
                    for w in self.withdrawals
                ]
                if self.withdrawals is not None
                else None
            ),
            receipts=(
                [
                    FixtureTransactionReceipt.from_transaction_receipt(
                        r, self.txs[i]
                    )
                    for i, r in enumerate(self.result.receipts)
                ]
                if self.result.receipts and include_receipts
                else None
            ),
            block_access_list=self.block_access_list
            if self.block_access_list
            else None,
            fork=self.fork,
        ).with_rlp(txs=self.txs)

        if self.expected_exception is not None:
            return InvalidFixtureBlock(
                rlp=fixture_block.rlp,
                expect_exception=self.expected_exception,
                rlp_decoded=(
                    None
                    if BlockException.RLP_STRUCTURES_ENCODING
                    in self.expected_exception
                    else fixture_block.without_rlp()
                ),
            )

        return fixture_block

    def get_block_rlp(self) -> Bytes:
        """Get the RLP of the block."""
        return self.get_fixture_block().rlp

    def engine_payload_modifier(
        self,
    ) -> "FixtureExecutionPayloadModifier | None":
        """
        Propagate ``rlp_modifier``'s header changes to the engine payload.

        The engine ``ExecutionPayload`` schema does not carry
        ``block_access_list_hash`` directly; the equivalent payload field is
        the ``block_access_list`` body. So a header modifier that touches the
        BAL hash needs to drive a matching change on the payload body.
        """
        if self.engine_new_payload_slot_number is not None:
            return FixtureExecutionPayloadModifier(
                slot_number=self.engine_new_payload_slot_number,
            )
        if self.engine_new_payload_block_access_list is not None:
            return FixtureExecutionPayloadModifier(
                block_access_list=self.engine_new_payload_block_access_list,
            )
        if self.rlp_modifier is None:
            return None
        bal_hash_override = self.rlp_modifier.block_access_list_hash
        if bal_hash_override is None:
            return None
        if bal_hash_override is Header.REMOVE_FIELD:
            return FixtureExecutionPayloadModifier(
                block_access_list=(
                    FixtureExecutionPayloadModifier.REMOVE_FIELD
                ),
            )
        # The user injected a header BAL hash; mirror that on the engine
        # payload by forcing a body to be present. Its exact value is
        # irrelevant for negative tests — a non-``None`` value is enough to
        # make a payload-version mismatch detectable.
        if self.block_access_list is None:
            return FixtureExecutionPayloadModifier(
                block_access_list=Bytes(b""),
            )
        return None

    def get_fixture_engine_new_payload(self) -> FixtureEngineNewPayload:
        """Get a FixtureEngineNewPayload from the built block."""
        return FixtureEngineNewPayload.from_fixture_header(
            fork=self.fork,
            header=self.header,
            transactions=self.txs,
            withdrawals=self.withdrawals,
            requests=self.requests,
            block_access_list=self.block_access_list.rlp
            if self.block_access_list
            else None,
            execution_payload_modifier=self.engine_payload_modifier(),
            validation_error=self.expected_exception,
            error_code=self.engine_api_error_code,
        )

    def verify_transactions(
        self, transition_tool_exceptions_reliable: bool
    ) -> List[int]:
        """Verify the transactions."""
        return verify_transactions(
            txs=self.txs,
            result=self.result,
            transition_tool_exceptions_reliable=transition_tool_exceptions_reliable,
        )

    def verify_block_exception(
        self, transition_tool_exceptions_reliable: bool
    ) -> None:
        """Verify the block exception."""
        got_exception: ExceptionWithMessage | UndefinedException | None = (
            self.result.block_exception
        )
        # Verify exceptions that are not caught by the transition tool.
        fork_block_rlp_size_limit = self.fork.block_rlp_size_limit()
        if fork_block_rlp_size_limit is not None:
            rlp_size = len(self.get_block_rlp())
            if rlp_size > fork_block_rlp_size_limit:
                got_exception = BlockExceptionWithMessage(
                    exceptions=[BlockException.RLP_BLOCK_LIMIT_EXCEEDED],
                    message=f"Block RLP size limit exceeded: {rlp_size} > "
                    f"{fork_block_rlp_size_limit}",
                )
        verify_block(
            block_number=self.env.number,
            want_exception=self.expected_exception,
            got_exception=got_exception,
            transition_tool_exceptions_reliable=transition_tool_exceptions_reliable,
        )


class TestingBuildBlock(BuiltBlock):
    """
    ``BuiltBlock`` from a live-client backend; carries the engine payload
    so ``make_stateful_fixture`` can record what the client built.
    """

    __test__ = False  # "Test" prefix; keep pytest from collecting it

    model_config = CamelModel.model_config | {"arbitrary_types_allowed": True}

    engine_payload: EnginePayloadMetadata


GENESIS_ENVIRONMENT_DEFAULTS: Dict[str, Any] = {
    "fee_recipient": 0,
    "number": 0,
    "timestamp": 0,
    "extra_data": b"\x00",
    "prev_randao": 0,
}
"""
Default values for the genesis environment that are used to create all genesis
headers.
"""


def _tx_phase(tx: Transaction) -> TestPhase | None:
    """Read a tx's phase: ``test_phase`` first, then ``metadata.phase``."""
    phase = getattr(tx, "test_phase", None)
    if phase is not None:
        return phase
    meta = getattr(tx, "metadata", None)
    if meta is None:
        return None
    return getattr(meta, "phase", None)


def _split_blocks_by_phase(blocks: List[Block]) -> List[Block]:
    """
    Split each block into contiguous phase runs.

    A mixed-phase block (e.g. EIP-7702 authorization tagged SETUP
    followed by benchmark TEST txs) becomes multiple back-to-back
    blocks, one per run; ``Block.phase`` asserts on mixed input.

    Block-level fields describing final state (``expected_post_state``,
    ``header_verify``, ...) stay on the LAST sub-block; earlier
    sub-blocks get them cleared.
    """
    out: List[Block] = []
    for block in blocks:
        phases = [_tx_phase(tx) for tx in block.txs]
        if len(set(phases)) <= 1:
            out.append(block)
            continue

        runs: List[List[Transaction]] = []
        current_run: List[Transaction] = []
        current_phase: Any = object()  # sentinel
        for tx, phase in zip(block.txs, phases, strict=False):
            if not current_run or phase == current_phase:
                current_run.append(tx)
                current_phase = phase
            else:
                runs.append(current_run)
                current_run = [tx]
                current_phase = phase
        if current_run:
            runs.append(current_run)

        last_idx = len(runs) - 1
        for idx, run_txs in enumerate(runs):
            if idx == last_idx:
                out.append(block.model_copy(update={"txs": run_txs}))
            else:
                out.append(
                    block.model_copy(
                        update={
                            "txs": run_txs,
                            "header_verify": None,
                            "rlp_modifier": None,
                            "expected_block_access_list": None,
                            "expected_post_state": None,
                            "expected_gas_used": None,
                            "exception": None,
                            "skip_exception_verification": False,
                            "engine_api_error_code": None,
                        }
                    )
                )
    return out


class BlockchainTest(BaseTest):
    """Filler type that tests multiple blocks (valid or invalid) in a chain."""

    pre: Alloc
    post: Alloc
    blocks: List[Block]
    genesis_environment: Environment = Field(default_factory=Environment)
    chain_id: int = Field(
        default_factory=lambda: ChainConfigDefaults.chain_id,
        validate_default=True,
    )
    include_full_post_state_in_output: bool = True
    """
    Include the post state in the fixture output. Otherwise, the state
    verification is only performed based on the state root.
    """
    include_tx_receipts_in_output: bool = True
    """
    Include transaction receipts in the fixture output.
    """

    supported_fixture_formats: ClassVar[
        Sequence[FixtureFormat | LabeledFixtureFormat]
    ] = [
        BlockchainFixture,
        BlockchainEngineFixture,
        BlockchainEngineSyncFixture,
        BlockchainEngineXFixture,
        BlockchainEngineStatefulFixture,
    ]
    supported_execute_formats: ClassVar[Sequence[LabeledExecuteFormat]] = [
        LabeledExecuteFormat(
            TransactionPost,
            "blockchain_test",
            "An execute test derived from a blockchain test",
        ),
    ]

    supported_markers: ClassVar[Dict[str, str]] = {
        "blockchain_test_engine_only": (
            "Only generate a blockchain test engine fixture"
        ),
        "blockchain_test_only": "Only generate a blockchain test fixture",
    }

    @classmethod
    def discard_fixture_format_by_marks(
        cls,
        fixture_format: FixtureFormat | LabeledFixtureFormat,
        markers: List[pytest.Mark],
    ) -> bool:
        """
        Discard a fixture format from filling if the appropriate marker is
        used.
        """
        marker_names = [m.name for m in markers]
        if (
            fixture_format != BlockchainFixture
            and "blockchain_test_only" in marker_names
        ):
            return True
        engine_formats: List[FixtureFormat] = [
            BlockchainEngineFixture,
            BlockchainEngineXFixture,
        ]
        if (
            fixture_format not in engine_formats
            and "blockchain_test_engine_only" in marker_names
        ):
            return True
        return False

    def model_post_init(self, __context: Any, /) -> None:
        """
        Model post-init to assert static (pre-fill/execute) checks.
        """
        super().model_post_init(__context)
        if self.is_inclusion_test:
            # Verify that the blockchain contains at most one invalid
            # transaction which must be located at the end of the last block.
            for i, block in enumerate(self.blocks):
                if i != (len(self.blocks) - 1):
                    valid_tx_range = block.txs[:]
                else:
                    valid_tx_range = block.txs[:-1]
                if any(tx.error is not None for tx in valid_tx_range):
                    raise Exception(
                        "test correctness: in an inclusion test the only "
                        "transaction allowed to produce an exception is the "
                        "last transaction of the last block, but block "
                        f"{i} contains an invalid transaction elsewhere"
                    )

    def get_genesis_environment(self) -> Environment:
        """Get the genesis environment for pre-allocation groups."""
        modified_values = self.genesis_environment.set_fork_requirements(
            self.fork.transitions_from()
        ).model_dump(exclude_unset=True)
        return Environment(**(GENESIS_ENVIRONMENT_DEFAULTS | modified_values))

    def make_genesis(
        self, *, apply_pre_allocation_blockchain: bool
    ) -> Tuple[Alloc, FixtureBlock]:
        """Create a genesis block from the blockchain test definition."""
        env = self.get_genesis_environment()
        assert env.withdrawals is None or len(env.withdrawals) == 0, (
            "withdrawals must be empty at genesis"
        )
        assert (
            env.parent_beacon_block_root is None
            or env.parent_beacon_block_root == Hash(0)
        ), "parent_beacon_block_root must be empty at genesis"

        pre_alloc = self.pre
        if apply_pre_allocation_blockchain:
            pre_alloc = Alloc.merge(
                Alloc.model_validate(
                    self.fork.transitions_to().pre_allocation_blockchain()
                ),
                pre_alloc,
            )
        if empty_accounts := pre_alloc.empty_accounts():
            raise Exception(f"Empty accounts in pre state: {empty_accounts}")
        if pre_alloc.state_commitment() is None:
            pre_alloc.migrate_state_commitment(
                self.fork.transitions_from().state_commitment()
            )
        state_root = pre_alloc.state_root()
        genesis = FixtureHeader.genesis(
            self.fork.transitions_from(), env, state_root
        )

        return (
            pre_alloc,
            FixtureBlockBase(
                header=genesis,
                withdrawals=None if env.withdrawals is None else [],
            ).with_rlp(txs=[]),
        )

    def generate_block_data(
        self,
        t8n: FillerBackend,
        block: Block,
        previous_env: Environment,
        previous_alloc: Alloc | LazyAlloc,
    ) -> BuiltBlock:
        """
        Generate common block data for both make_fixture and make_hive_fixture.

        ``t8n`` is any backend satisfying ``FillerBackend``. The
        default compute path passes a concrete ``TransitionTool``; stateful
        filling will pass an ``ClientBackend`` that drives
        ``testing_buildBlockV1`` against a live client.
        """
        env = block.set_environment(previous_env)
        fork = self.fork.fork_at(
            block_number=env.number, timestamp=env.timestamp
        )
        env = env.set_fork_requirements(fork)
        txs = block.txs[:]
        if any("gas_limit" not in tx.model_fields_set for tx in block.txs):
            max_tx_gas_limit = Transaction.calculate_max_gas_limit(
                txs=txs,
                env_gas_limit=int(env.gas_limit),
                transaction_gas_limit_cap=fork.transaction_gas_limit_cap(),
                state_gas_reservoir_enabled=fork.state_gas_reservoir_enabled(),
            )
            if max_tx_gas_limit == 0:
                raise Exception(
                    "test correctness: unable to automatically calculate gas "
                    "limit for transactions (No remaining gas)."
                )
            txs = [
                tx.with_gas_limit(
                    max_gas_limit=max_tx_gas_limit,
                    transaction_gas_limit_cap=fork.transaction_gas_limit_cap(),
                    state_gas_reservoir_enabled=fork.state_gas_reservoir_enabled(),
                )
                for tx in txs
            ]
        txs = [tx.with_signature_and_sender() for tx in txs]

        if (failing_tx_count := len([tx for tx in txs if tx.error])) > 0:
            if failing_tx_count > 1:
                raise Exception(
                    "test correctness: only one transaction can produce "
                    "an exception in a block"
                )
            if not txs[-1].error:
                raise Exception(
                    "test correctness: the transaction that produces an "
                    "exception must be the last transaction in the block"
                )

        transition_tool_output = t8n.evaluate(
            transition_tool_data=TransitionTool.TransitionToolData(
                alloc=previous_alloc,
                txs=txs,
                env=env,
                fork=fork,
                chain_id=self.chain_id,
                reward=fork.get_reward(),
                blob_schedule=fork.blob_schedule(),
            ),
            slow_request=self.is_tx_gas_heavy_test,
        )

        # One special case of the invalid transactions is the blob gas used,
        # since this value is not included in the transition tool result, but
        # it is included in the block header, and some clients check it before
        # executing the block by simply counting the type-3 txs, we need to set
        # the correct value by default.
        blob_gas_used: int | None = None
        if fork.supports_blobs():
            if (blob_gas_per_blob := fork.blob_gas_per_blob()) > 0:
                blob_gas_used = blob_gas_per_blob * count_blobs(txs)

        # Prepare slot_number for header initialization
        slot_number_value: ZeroPaddedHexNumber | None = None
        if fork.header_slot_number_required():
            slot_number_value = ZeroPaddedHexNumber(
                int(env.slot_number) if env.slot_number is not None else 0
            )

        header = FixtureHeader(
            **(
                transition_tool_output.result.model_dump(
                    exclude_none=True,
                    exclude={"blob_gas_used", "transactions_trie"},
                )
                | env.model_dump(
                    exclude_none=True,
                    exclude={"blob_gas_used", "slot_number"},
                )
            ),
            blob_gas_used=blob_gas_used,
            transactions_trie=Transaction.list_root(txs),
            extra_data=(
                block.extra_data if block.extra_data is not None else b""
            ),
            slot_number=slot_number_value,
            fork=fork,
        )

        if block.header_verify is not None:
            # Verify the header after transition tool processing.
            try:
                block.header_verify.verify(header)
            except Exception as e:
                raise Exception(
                    f"Verification of block {int(env.number)} failed"
                ) from e

        if block.expected_gas_used is not None:
            gas_used = int(transition_tool_output.result.gas_used)
            assert gas_used == block.expected_gas_used, (
                f"gas_used ({gas_used}) does not match expected_gas_used "
                f"({block.expected_gas_used})"
                f", difference: {gas_used - block.expected_gas_used}"
            )

        requests_list: List[Bytes] | None = None
        if fork.header_requests_required():
            assert transition_tool_output.result.requests is not None, (
                "Requests are required for this block"
            )
            requests = Requests(
                requests_lists=list(transition_tool_output.result.requests)
            )

            if Hash(requests) != header.requests_hash:
                raise Exception(
                    "Requests root in header does not match the requests "
                    "root in the transition tool output: "
                    f"{header.requests_hash} != {Hash(requests)}"
                )

            requests_list = requests.requests_list

        if block.requests is not None:
            header.requests_hash = Hash(
                Requests(requests_lists=list(block.requests))
            )
            requests_list = block.requests

        # Decode BAL from RLP bytes provided by the transition tool.
        t8n_bal_rlp = transition_tool_output.result.block_access_list
        t8n_bal: BlockAccessList | None = None
        if t8n_bal_rlp is not None:
            t8n_bal = BlockAccessList.from_rlp(t8n_bal_rlp)

        if fork.header_bal_hash_required():
            assert t8n_bal is not None, (
                "Block access list is required for this block but was not "
                "provided by the transition tool"
            )

            computed_block_access_list_hash = Hash(t8n_bal.rlp.keccak256())
            assert (
                computed_block_access_list_hash
                == header.block_access_list_hash
            ), (
                "Block access list hash in header does not match the "
                f"computed hash from BAL: {header.block_access_list_hash} "
                f"!= {computed_block_access_list_hash}"
            )

        if block.rlp_modifier is not None:
            # Modify any parameter specified in the `rlp_modifier` after
            # transition tool processing.
            header = block.rlp_modifier.apply(header)
            header.fork = fork  # Deleted during `apply` because `exclude=True`

        # Process block access list - apply transformer if present for invalid
        # tests
        bal = t8n_bal

        # Always validate BAL structural integrity (ordering, duplicates)
        # if present
        if t8n_bal is not None:
            t8n_bal.validate_structure()

        # If expected BAL is defined, verify against it
        if (
            block.expected_block_access_list is not None
            and t8n_bal is not None
        ):
            block.expected_block_access_list.verify_against(t8n_bal)

            bal = block.expected_block_access_list.modify_if_invalid_test(
                t8n_bal
            )
            if bal != t8n_bal:
                # If the BAL was modified and the fork requires it, update the
                # header hash
                header.block_access_list_hash = Hash(bal.rlp.keccak256())

        built_block_kwargs: Dict[str, Any] = dict(
            header=header,
            alloc=transition_tool_output.alloc,
            state_root=transition_tool_output.result.state_root,
            env=env,
            txs=txs,
            ommers=[],
            withdrawals=env.withdrawals,
            requests=requests_list,
            result=transition_tool_output.result,
            expected_exception=block.exception,
            engine_api_error_code=block.engine_api_error_code,
            rlp_modifier=block.rlp_modifier,
            fork=fork,
            block_access_list=bal,
            engine_new_payload_block_access_list=(
                block.engine_new_payload_block_access_list
            ),
            engine_new_payload_slot_number=(
                block.engine_new_payload_slot_number
            ),
        )
        built_block: BuiltBlock
        if transition_tool_output.engine_payload is not None:
            built_block = TestingBuildBlock(
                **built_block_kwargs,
                engine_payload=transition_tool_output.engine_payload,
            )
        else:
            built_block = BuiltBlock(**built_block_kwargs)

        try:
            rejected_txs = built_block.verify_transactions(
                transition_tool_exceptions_reliable=t8n.exception_mapper.reliable,
            )
            if (
                not rejected_txs
                and block.rlp_modifier is None
                and block.requests is None
                and not block.skip_exception_verification
                and block.engine_new_payload_block_access_list is None
                and block.engine_new_payload_slot_number is None
                and not (
                    block.expected_block_access_list is not None
                    and block.expected_block_access_list._modifier is not None
                )
            ):
                # Only verify block level exception if: - No transaction
                # exception was raised, because these are not reported as block
                # exceptions. - No RLP modifier was specified, because the
                # modifier is what normally produces the block exception. - No
                # requests were specified, because modified requests are also
                # what normally produces the block exception. - No engine
                # payload BAL override was specified, because it corrupts only
                # the engine payload after the transition tool has run. - No
                # BAL modifier was specified, because modified BAL also
                # produces block exceptions.
                built_block.verify_block_exception(
                    transition_tool_exceptions_reliable=t8n.exception_mapper.reliable,
                )
            verify_result(transition_tool_output.result, env)
        except Exception as e:
            print_traces(t8n.get_traces())
            pprint(transition_tool_output.result)
            pprint(previous_alloc)
            pprint(transition_tool_output.alloc.materialize())
            raise e

        if len(rejected_txs) > 0 and block.exception is None:
            print_traces(t8n.get_traces())
            raise Exception(
                "one or more transactions in `BlockchainTest` are "
                + "intrinsically invalid, but the block was not expected "
                + "to be invalid. Please verify whether the transaction "
                + "was indeed expected to fail and add the proper "
                + "`block.exception`"
            )

        return built_block

    def verify_post_state(
        self,
        t8n: FillerBackend,
        t8n_state: Alloc,
        expected_state: Alloc | None = None,
    ) -> None:
        """Verify post alloc after all block/s or payload/s are generated."""
        try:
            if expected_state:
                expected_state.verify_post_alloc(t8n_state)
            else:
                self.post.verify_post_alloc(t8n_state)
        except Exception as e:
            print_traces(t8n.get_traces())
            raise e

    def make_fixture(
        self,
        t8n: FillerBackend,
    ) -> FillResult:
        """Create a fixture from the blockchain test definition."""
        fixture_blocks: List[FixtureBlock | InvalidFixtureBlock] = []

        pre, genesis = self.make_genesis(apply_pre_allocation_blockchain=True)

        alloc: Alloc | LazyAlloc = pre
        state_root = genesis.header.state_root
        env = environment_from_parent_header(genesis.header)
        head = genesis.header.block_hash
        invalid_blocks = 0
        benchmark_gas_used: int | None = None
        benchmark_block_gas_used: int | None = None
        benchmark_opcode_count: OpcodeCount | None = None
        for block in self.blocks:
            # This is the most common case, the RLP needs to be constructed
            # based on the transactions to be included in the block.
            # Set the environment according to the block to execute.
            built_block = self.generate_block_data(
                t8n=t8n,
                block=block,
                previous_env=env,
                previous_alloc=alloc,
            )
            block_number = int(built_block.header.number)
            is_last_block = block is self.blocks[-1]
            if is_last_block and self.operation_mode == OpMode.BENCHMARKING:
                benchmark_gas_used = built_block.cumulative_gas_used()
                benchmark_block_gas_used = built_block.block_gas_used()
                benchmark_opcode_count = built_block.result.opcode_count
            if built_block.result.receipts:
                self.validate_receipt_status(
                    receipts=built_block.result.receipts,
                    block_number=block_number,
                )
            include_receipts = (
                block.include_receipts_in_output
                if block.include_receipts_in_output is not None
                else self.include_tx_receipts_in_output
            )
            fixture_blocks.append(
                built_block.get_fixture_block(
                    include_receipts=include_receipts
                )
            )

            # BAL verification already done in to_fixture_bal() if
            # expected_block_access_list set

            if block.exception is None:
                # Update env, alloc and last block hash for the next block.
                alloc = built_block.alloc
                state_root = built_block.state_root
                env = apply_new_parent(built_block.env, built_block.header)
                head = built_block.header.block_hash
            else:
                invalid_blocks += 1

            if block.expected_post_state:
                self.verify_post_state(
                    t8n,
                    t8n_state=alloc.materialize()
                    if isinstance(alloc, LazyAlloc)
                    else alloc,
                    expected_state=block.expected_post_state,
                )
        self.check_exception_test(exception=invalid_blocks > 0)
        alloc = alloc.materialize() if isinstance(alloc, LazyAlloc) else alloc
        self.verify_post_state(t8n, t8n_state=alloc)
        fixture = BlockchainFixture(
            fork=self.fork,
            genesis=genesis.header,
            genesis_rlp=genesis.rlp,
            blocks=fixture_blocks,
            last_block_hash=head,
            pre=pre,
            post_state=alloc
            if self.include_full_post_state_in_output
            else None,
            post_state_hash=state_root
            if not self.include_full_post_state_in_output
            else None,
            config=FixtureConfig(
                fork=self.fork,
                blob_schedule=FixtureBlobSchedule.from_blob_schedule(
                    self.fork.transitions_to().blob_schedule()
                ),
                chain_id=self.chain_id,
            ),
        )
        return FillResult(
            fixture=fixture,
            gas_optimization=None,
            benchmark_gas_used=benchmark_gas_used,
            benchmark_block_gas_used=benchmark_block_gas_used,
            benchmark_opcode_count=benchmark_opcode_count,
            post_verifications=PostVerifications.from_alloc(self.post),
        )

    def sync_payload_eligible(self) -> bool:
        """
        Return whether this test's chain takes the appended sync block.

        Eligible unless the fill context withheld the block (the
        ``--no-sync-block`` option or the test's own opt-out, folded
        into ``sync_block``), the chain has no blocks to append to, or
        a block asserts an Engine API error code: that assertion is
        about the client's answer to the announcement of the test's
        *own* payload, and a block appended above it would be announced
        instead, so the refusal the test verifies would never happen.

        Expected-invalid blocks are eligible, and are the reason the
        block is appended rather than inserted below the chain: above
        an invalid head the appended block is a sync target only, and
        it puts the invalid block itself on the wire, where a client
        must fetch and judge it through its sync path.
        """
        if not self.sync_block or not self.blocks:
            return False
        return all(
            block.engine_api_error_code is None for block in self.blocks
        )

    def build_sync_payload(
        self,
        t8n: FillerBackend,
        *,
        head: BuiltBlock,
        alloc: Alloc | LazyAlloc,
    ) -> FixtureEngineNewPayload:
        """
        Build the empty block appended above the chain's ``head``.

        ``head`` is the chain's last built block, valid or not, and
        ``alloc`` is the state the chain leaves behind: a valid head's
        post-state or, when the head is expected to be rejected and was
        rolled back, the state of its own parent.

        Above a rejected head the block is a sync target only, not a
        valid continuation: its ``state_root`` follows from a state
        transition no client would compute, since no client accepts its
        parent. What it must get right is the part of its header a
        client checks without the parent's state - it names the
        rejected block as its parent, one block above it, with the fee
        and gas context the fork derives from that block's header -
        which is enough for the client to answer the announcement with
        SYNCING and fetch the ancestry it lacks. It rejects the test's
        block from that ancestry long before it would execute this one.
        """
        env = apply_new_parent(head.env, head.header)
        extra_data = Bytes(sha256(self.sync_block_salt.encode()).digest()[:16])
        sync_block = self.generate_block_data(
            t8n=t8n,
            block=Block(extra_data=extra_data),
            previous_env=env,
            previous_alloc=alloc,
        )
        return sync_block.get_fixture_engine_new_payload()

    def make_hive_fixture(
        self,
        t8n: FillerBackend,
        fixture_format: FixtureFormat
        | LabeledFixtureFormat = BlockchainEngineFixture,
    ) -> FillResult:
        """Create a hive fixture from the blocktest definition."""
        fixture_payloads: List[FixtureEngineNewPayload] = []

        pre, genesis = self.make_genesis(
            apply_pre_allocation_blockchain=fixture_format
            != BlockchainEngineXFixture,
        )
        alloc: Alloc | LazyAlloc = pre
        state_root = genesis.header.state_root
        env = environment_from_parent_header(genesis.header)
        head_hash = genesis.header.block_hash
        invalid_blocks = 0
        benchmark_gas_used: int | None = None
        benchmark_block_gas_used: int | None = None
        benchmark_opcode_count: OpcodeCount | None = None
        for block in self.blocks:
            built_block = self.generate_block_data(
                t8n=t8n,
                block=block,
                previous_env=env,
                previous_alloc=alloc,
            )
            block_number = int(built_block.header.number)
            is_last_block = block is self.blocks[-1]
            if is_last_block and self.operation_mode == OpMode.BENCHMARKING:
                benchmark_gas_used = built_block.cumulative_gas_used()
                benchmark_block_gas_used = built_block.block_gas_used()
                benchmark_opcode_count = built_block.result.opcode_count
            if built_block.result.receipts:
                self.validate_receipt_status(
                    receipts=built_block.result.receipts,
                    block_number=block_number,
                )
            fixture_payloads.append(
                built_block.get_fixture_engine_new_payload()
            )
            if block.exception is None:
                alloc = built_block.alloc
                state_root = built_block.state_root
                env = apply_new_parent(built_block.env, built_block.header)
                head_hash = built_block.header.block_hash
            else:
                invalid_blocks += 1

            if block.expected_post_state:
                self.verify_post_state(
                    t8n,
                    t8n_state=alloc.materialize()
                    if isinstance(alloc, LazyAlloc)
                    else alloc,
                    expected_state=block.expected_post_state,
                )
        self.check_exception_test(exception=invalid_blocks > 0)
        fcu_version = (
            self.fork.transitions_from().engine_forkchoice_updated_version()
        )
        assert fcu_version is not None, (
            "A hive fixture was requested but no forkchoice update is defined."
            " The framework should never try to execute this test case."
        )

        alloc = alloc.materialize() if isinstance(alloc, LazyAlloc) else alloc
        self.verify_post_state(t8n, t8n_state=alloc)

        # Create base fixture data, common to all fixture formats
        fixture_data: Dict[str, Any] = {
            "fork": self.fork,
            "genesis": genesis.header,
            "payloads": fixture_payloads,
            "last_block_hash": head_hash,
            "post_state_hash": state_root
            if not self.include_full_post_state_in_output
            else None,
            "config": FixtureConfig(
                fork=self.fork,
                chain_id=self.chain_id,
                blob_schedule=FixtureBlobSchedule.from_blob_schedule(
                    self.fork.transitions_to().blob_schedule()
                ),
            ),
        }

        # Add format-specific fields
        fixture: BaseFixture
        if fixture_format == BlockchainEngineXFixture:
            # For Engine X format, exclude pre (will be provided via shared
            # state) and prepare for state diff optimization
            fixture_data.update(
                {
                    "post_state": alloc
                    if self.include_full_post_state_in_output
                    else None,
                    "pre_hash": "",  # Will be set by BaseTestWrapper
                }
            )
            if self.sync_payload_eligible():
                # `built_block` is the chain's last built block, valid
                # or not; the sync block sits above it so that every
                # test-authored block is an ancestor of the announced
                # head. Stored out-of-chain: `payloads`, the head and
                # the post state stay exactly the author's chain.
                fixture_data["sync_payload"] = self.build_sync_payload(
                    t8n, head=built_block, alloc=alloc
                )
            fixture = BlockchainEngineXFixture(**fixture_data)
        elif fixture_format == BlockchainEngineSyncFixture:
            # Sync fixture format
            assert genesis.header.block_hash != head_hash, (
                "Invalid payload tests negative test via sync is not "
                "supported yet."
            )
            # Most clients require the header to start the sync process, so we
            # create an empty block on top of the last block of the test to
            # send it as new payload and trigger the sync process.
            sync_built_block = self.generate_block_data(
                t8n=t8n,
                block=Block(),
                previous_env=env,
                previous_alloc=alloc,
            )
            fixture_data.update(
                {
                    "sync_payload": (
                        sync_built_block.get_fixture_engine_new_payload()
                    ),
                    "pre": pre,
                    "post_state": alloc
                    if self.include_full_post_state_in_output
                    else None,
                }
            )
            fixture = BlockchainEngineSyncFixture(**fixture_data)
        else:
            # Standard engine fixture
            fixture_data.update(
                {
                    "pre": pre,
                    "post_state": alloc
                    if self.include_full_post_state_in_output
                    else None,
                }
            )
            fixture = BlockchainEngineFixture(**fixture_data)

        return FillResult(
            fixture=fixture,
            gas_optimization=None,
            benchmark_gas_used=benchmark_gas_used,
            benchmark_block_gas_used=benchmark_block_gas_used,
            benchmark_opcode_count=benchmark_opcode_count,
            post_verifications=PostVerifications.from_alloc(self.post),
        )

    def make_stateful_fixture(
        self,
        t8n: FillerBackend,
    ) -> FillResult:
        """
        Create a ``BlockchainEngineStatefulFixture`` against a live client.

        Differs from ``make_hive_fixture``:

        - No genesis building: the client already has warm state from a
          snapshot. The backend (typically ``ClientBackend``) owns
          ``snapshot_block`` / ``start_block`` captured at session start.
        - ``pre.fund_eoa`` / ``pre.deploy_contract`` calls are materialised
          into a synthetic setup block prepended to ``self.blocks``,
          instead of being baked into genesis alloc.
        - Payloads are partitioned by ``FixtureEngineNewPayload.phase``
          into ``setup_payloads`` (setup-phase txs) and ``payloads``
          (execution-phase txs).
        - ``post`` is verified against the live client (the oracle) via
          ``get_post_state_alloc``; there is no t8n post alloc to diff.
        """
        if not isinstance(t8n, ClientBackend):
            raise RuntimeError(
                "make_stateful_fixture requires a ClientBackend; got "
                f"{type(t8n).__name__}."
            )
        if t8n.snapshot_block is None or t8n.start_block is None:
            raise RuntimeError(
                "ClientBackend.snapshot_block / .start_block must be "
                "captured by the fill-stateful pre-run before fill."
            )
        snapshot_block = t8n.snapshot_block
        start_block = t8n.start_block

        # Mirror execute.py's pre-send flow so pending-tx funding amounts
        # materialise before we drain the queue: required-balances →
        # resolve deferred deploys/stubs/fund_addresses → run
        # minimum_balance_for_pending_transactions. Tests whose Alloc
        # does not expose ``pending_transactions`` skip this entirely.
        pending_getter = getattr(self.pre, "pending_transactions", None)
        resolve_deferred = getattr(self.pre, "resolve_deferred_checks", None)
        min_balance = getattr(
            self.pre, "minimum_balance_for_pending_transactions", None
        )
        if (
            callable(pending_getter)
            and callable(resolve_deferred)
            and callable(min_balance)
        ):
            execute_plan = self.execute(execute_format=TransactionPost)
            session_fork = self.fork.fork_at(block_number=0, timestamp=0)
            # Session fees pinned on the backend by the fill-stateful plugin.
            gas_price = t8n.gas_price
            max_fee_per_gas = t8n.max_fee_per_gas
            max_priority_fee_per_gas = t8n.max_priority_fee_per_gas
            max_fee_per_blob_gas = t8n.max_fee_per_blob_gas
            if not all(
                [
                    gas_price,
                    max_fee_per_gas,
                    max_priority_fee_per_gas,
                    max_fee_per_blob_gas,
                ]
            ):
                raise RuntimeError(
                    "make_stateful_fixture requires the backend to carry "
                    f"non-zero session fees; got gas_price={gas_price}, "
                    f"max_fee_per_gas={max_fee_per_gas}, "
                    f"max_priority_fee_per_gas={max_priority_fee_per_gas}, "
                    f"max_fee_per_blob_gas={max_fee_per_blob_gas}."
                )
            execute_plan.prepare_transactions(
                env=Environment(gas_limit=HexNumber(start_block["gasLimit"])),
                gas_price=gas_price,
                max_fee_per_gas=max_fee_per_gas,
                max_priority_fee_per_gas=max_priority_fee_per_gas,
                max_fee_per_blob_gas=max_fee_per_blob_gas,
                fork=session_fork,
            )
            required_balances = execute_plan.get_required_sender_balances(
                fork=session_fork,
            )
            resolve_deferred()
            min_balance(
                required_balances,
                gas_price=gas_price,
                max_fee_per_gas=max_fee_per_gas,
                max_priority_fee_per_gas=max_priority_fee_per_gas,
                max_fee_per_blob_gas=max_fee_per_blob_gas,
            )

        self.pre.verify_deployed_accounts(
            int(HexNumber(start_block["number"]))
        )

        # Materialise queued pre-alloc txs into a synthetic setup block.
        blocks_to_process: List[Block] = []
        if callable(pending_getter):
            setup_txs = pending_getter()
            if setup_txs:
                blocks_to_process.append(Block(txs=setup_txs))
        # Each block must be single-phase (Block.phase asserts otherwise);
        # mixed blocks (e.g. EIP-7702 authorization + benchmark exec) are
        # split into contiguous phase runs so benchmark gas isn't
        # swallowed into ``setupEngineNewPayloads``.
        blocks_to_process.extend(_split_blocks_by_phase(self.blocks))

        # Chain off the session start_block. We pull parent_* from a
        # FixtureHeader-validated copy of the client's block dict, but
        # seed block_hashes with the client's hash directly — FixtureHeader
        # recomputes block_hash from RLP and that diverges from the
        # client's authoritative hash unless every header byte is
        # reproduced exactly.
        start_block_number = int(HexNumber(start_block["number"]))
        start_block_hash = Hash(start_block["hash"])
        parent_header = FixtureHeader.model_validate(start_block)
        env = Environment(
            parent_difficulty=parent_header.difficulty,
            parent_timestamp=parent_header.timestamp,
            parent_base_fee_per_gas=parent_header.base_fee_per_gas,
            parent_blob_gas_used=parent_header.blob_gas_used,
            parent_excess_blob_gas=parent_header.excess_blob_gas,
            parent_gas_used=parent_header.gas_used,
            parent_gas_limit=parent_header.gas_limit,
            parent_ommers_hash=parent_header.ommers_hash,
            block_hashes={
                HexNumber(start_block_number): start_block_hash,
            },
        )

        setup_payloads: List[FixtureEngineNewPayload] = []
        execution_payloads: List[FixtureEngineNewPayload] = []
        # Aligned 1:1 with execution_payloads; None when no trace.
        execution_opcode_counts: List[Dict[str, int] | None] = []
        head_hash = start_block_hash
        benchmark_gas_used: int | None = None
        benchmark_block_gas_used: int | None = None
        benchmark_opcode_count: OpcodeCount | None = None
        # Alloc is not authoritative in stateful mode; pass self.pre as a
        # placeholder — ClientBackend ignores it.
        alloc: Alloc | LazyAlloc = self.pre
        for block in blocks_to_process:
            built_block = self.generate_block_data(
                t8n=t8n,
                block=block,
                previous_env=env,
                previous_alloc=alloc,
            )
            assert isinstance(built_block, TestingBuildBlock), (
                "ClientBackend must return TestingBuildBlock; got "
                f"{type(built_block).__name__}"
            )
            payload = payload_metadata_to_fixture(
                built_block.engine_payload, phase=block.phase
            )
            # The client's authoritative block hash (the FixtureHeader RLP
            # hash diverges — the client picks fields like gas_limit).
            client_hash = Hash(
                built_block.engine_payload.payload_response.execution_payload.block_hash
            )
            if payload.phase == TestPhase.SETUP:
                setup_payloads.append(payload)
            else:
                execution_payloads.append(payload)
                block_opcode_count = t8n.extract_block_opcode_count(
                    client_hash
                )
                execution_opcode_counts.append(
                    block_opcode_count.model_dump()
                    if block_opcode_count is not None
                    else None
                )
                # Setup blocks (pre-alloc funding/deploys) are exempt:
                # ``expected_receipt_status`` describes the test's own
                # transactions, and setup txs always succeed.
                if built_block.result.receipts:
                    self.validate_receipt_status(
                        receipts=built_block.result.receipts,
                        block_number=int(built_block.header.number),
                    )
                if self.operation_mode == OpMode.BENCHMARKING:
                    benchmark_gas_used = built_block.cumulative_gas_used()
                    benchmark_block_gas_used = built_block.block_gas_used()
                    # Consumed by BenchmarkTest's opcode-count verification.
                    benchmark_opcode_count = block_opcode_count
            # apply_new_parent records the RLP hash; the next block's
            # parent_hash must point at what the client actually built.
            env = apply_new_parent(built_block.env, built_block.header)
            env = env.copy(
                block_hashes={
                    **env.block_hashes,
                    HexNumber(int(env.number)): client_hash,
                },
            )
            head_hash = client_hash

        if self.post.root:
            got_alloc = t8n.get_post_state_alloc(self.post)
            self.post.verify_post_alloc(got_alloc)

        fixture = BlockchainEngineStatefulFixture(
            fork=self.fork,
            last_block_hash=head_hash,
            config=FixtureConfig(fork=self.fork),
            snapshot_block_number=HexNumber(snapshot_block["number"]),
            snapshot_block_hash=Hash(snapshot_block["hash"]),
            start_block_number=HexNumber(start_block_number),
            start_block_hash=start_block_hash,
            setup_payloads=setup_payloads,
            payloads=execution_payloads,
            benchmark_gas_used=(
                HexNumber(benchmark_gas_used)
                if benchmark_gas_used is not None
                else None
            ),
        )
        metadata: Dict[str, Any] = {}
        if t8n.extract_opcode_count:
            metadata["opcode_counts"] = execution_opcode_counts
        return FillResult(
            fixture=fixture,
            gas_optimization=None,
            benchmark_gas_used=benchmark_gas_used,
            benchmark_block_gas_used=benchmark_block_gas_used,
            benchmark_opcode_count=benchmark_opcode_count,
            metadata=metadata,
            post_verifications=PostVerifications.from_alloc(self.post),
        )

    def generate(
        self,
        t8n: FillerBackend,
        fixture_format: FixtureFormat | LabeledFixtureFormat,
    ) -> FillResult:
        """Generate the BlockchainTest fixture."""
        if fixture_format == BlockchainEngineStatefulFixture:
            return self.make_stateful_fixture(t8n)
        if fixture_format in [
            BlockchainEngineFixture,
            BlockchainEngineXFixture,
            BlockchainEngineSyncFixture,
        ]:
            return self.make_hive_fixture(t8n, fixture_format)
        elif fixture_format == BlockchainFixture:
            return self.make_fixture(t8n)

        raise Exception(f"Unknown fixture format: {fixture_format}")

    def execute(
        self,
        *,
        execute_format: ExecuteFormat | LabeledExecuteFormat,
    ) -> BaseExecute:
        """Generate the list of test fixtures."""
        if execute_format == TransactionPost:
            blocks: List[List[Transaction]] = []
            for block in self.blocks:
                blocks += [block.txs]
            # Pass gas validation params for benchmark tests
            # If not benchmark mode, skip gas used validation
            if self.operation_mode != OpMode.BENCHMARKING:
                self.skip_gas_used_validation = True

            benchmark_mode = self.operation_mode == OpMode.BENCHMARKING
            return TransactionPost(
                blocks=blocks,
                post=self.post,
                benchmark_mode=benchmark_mode,
            )
        raise Exception(f"Unsupported execute format: {execute_format}")


BlockchainTestSpec = Callable[[str], Generator[BlockchainTest, None, None]]
BlockchainTestFiller = Type[BlockchainTest]
