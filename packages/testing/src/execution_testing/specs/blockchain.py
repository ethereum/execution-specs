"""Ethereum blockchain test spec definition and filler."""

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
from pydantic import ConfigDict, Field, field_validator, model_serializer

from execution_testing.base_types import (
    Address,
    Bloom,
    Bytes,
    CamelModel,
    Hash,
    HeaderNonce,
    HexNumber,
    Number,
)
from execution_testing.client_clis import (
    BlockExceptionWithMessage,
    LazyAlloc,
    Result,
    TransitionTool,
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
    FixtureHeader,
    FixtureTransaction,
    FixtureWithdrawal,
    InvalidFixtureBlock,
)
from execution_testing.fixtures.common import (
    FixtureBlobSchedule,
    FixtureTransactionReceipt,
)
from execution_testing.forks import Fork
from execution_testing.test_types import (
    Alloc,
    Environment,
    Removable,
    Requests,
    Transaction,
    Withdrawal,
)
from execution_testing.test_types.block_access_list import (
    BlockAccessList,
    BlockAccessListExpectation,
)

from .base import BaseTest, OpMode, verify_result
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
    bal_hash: Removable | Hash | None = None

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
        return target.copy(
            **{
                k: (v if v is not Header.REMOVE_FIELD else None)
                for k, v in self.model_dump(exclude_none=True).items()
            }
        )

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
            new_env_values["bal_hash"] = self.block_access_list.keccak256()
            new_env_values["block_access_list"] = self.block_access_list
        if (
            not isinstance(self.block_access_list, Removable)
            and self.block_access_list is not None
        ):
            new_env_values["block_access_list"] = self.block_access_list
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
    alloc: LazyAlloc
    state_root: Hash
    txs: List[Transaction]
    ommers: List[FixtureHeader]
    withdrawals: List[Withdrawal] | None
    requests: List[Bytes] | None
    result: Result
    expected_exception: BLOCK_EXCEPTION_TYPE = None
    engine_api_error_code: EngineAPIError | None = None
    fork: Fork
    block_access_list: BlockAccessList | None

    def get_fixture_block(self) -> FixtureBlock | InvalidFixtureBlock:
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
                if self.result.receipts
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
        fork_block_rlp_size_limit = self.fork.block_rlp_size_limit(
            block_number=self.env.number,
            timestamp=self.env.timestamp,
        )
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


class BlockchainTest(BaseTest):
    """Filler type that tests multiple blocks (valid or invalid) in a chain."""

    pre: Alloc
    post: Alloc
    blocks: List[Block]
    genesis_environment: Environment = Field(default_factory=Environment)
    chain_id: int = 1
    exclude_full_post_state_in_output: bool = False
    """
    Exclude the post state from the fixture output. In this case, the state
    verification is only performed based on the state root.
    """

    supported_fixture_formats: ClassVar[
        Sequence[FixtureFormat | LabeledFixtureFormat]
    ] = [
        BlockchainFixture,
        BlockchainEngineFixture,
        BlockchainEngineXFixture,
        BlockchainEngineSyncFixture,
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
        fixture_format: FixtureFormat,
        fork: Fork,
        markers: List[pytest.Mark],
    ) -> bool:
        """
        Discard a fixture format from filling if the appropriate marker is
        used.
        """
        del fork

        marker_names = [m.name for m in markers]
        if (
            fixture_format != BlockchainFixture
            and "blockchain_test_only" in marker_names
        ):
            return True
        if (
            fixture_format
            not in [BlockchainEngineFixture, BlockchainEngineXFixture]
            and "blockchain_test_engine_only" in marker_names
        ):
            return True
        return False

    def get_genesis_environment(self) -> Environment:
        """Get the genesis environment for pre-allocation groups."""
        modified_values = self.genesis_environment.set_fork_requirements(
            self.fork
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
                Alloc.model_validate(self.fork.pre_allocation_blockchain()),
                pre_alloc,
            )
        if empty_accounts := pre_alloc.empty_accounts():
            raise Exception(f"Empty accounts in pre state: {empty_accounts}")
        state_root = pre_alloc.state_root()
        genesis = FixtureHeader.genesis(self.fork, env, state_root)

        return (
            pre_alloc,
            FixtureBlockBase(
                header=genesis,
                withdrawals=None if env.withdrawals is None else [],
            ).with_rlp(txs=[]),
        )

    def generate_block_data(
        self,
        t8n: TransitionTool,
        block: Block,
        previous_env: Environment,
        previous_alloc: Alloc | LazyAlloc,
        last_block: bool,
    ) -> BuiltBlock:
        """
        Generate common block data for both make_fixture and make_hive_fixture.
        """
        env = block.set_environment(previous_env)
        env = env.set_fork_requirements(self.fork)
        txs = [tx.with_signature_and_sender() for tx in block.txs]

        if failing_tx_count := len([tx for tx in txs if tx.error]) > 0:
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
                fork=self.fork,
                chain_id=self.chain_id,
                reward=self.fork.get_reward(
                    block_number=env.number, timestamp=env.timestamp
                ),
                blob_schedule=self.fork.blob_schedule(),
            ),
            debug_output_path=self.get_next_transition_tool_output_path(),
            slow_request=self.is_tx_gas_heavy_test(),
        )

        if transition_tool_output.result.opcode_count is not None:
            if self._opcode_count is None:
                self._opcode_count = transition_tool_output.result.opcode_count
            else:
                self._opcode_count += (
                    transition_tool_output.result.opcode_count
                )

        # One special case of the invalid transactions is the blob gas used,
        # since this value is not included in the transition tool result, but
        # it is included in the block header, and some clients check it before
        # executing the block by simply counting the type-3 txs, we need to set
        # the correct value by default.
        blob_gas_used: int | None = None
        if (
            blob_gas_per_blob := self.fork.blob_gas_per_blob(
                block_number=env.number, timestamp=env.timestamp
            )
        ) > 0:
            blob_gas_used = blob_gas_per_blob * count_blobs(txs)

        header = FixtureHeader(
            **(
                transition_tool_output.result.model_dump(
                    exclude_none=True,
                    exclude={"blob_gas_used", "transactions_trie"},
                )
                | env.model_dump(exclude_none=True, exclude={"blob_gas_used"})
            ),
            blob_gas_used=blob_gas_used,
            transactions_trie=Transaction.list_root(txs),
            extra_data=block.extra_data
            if block.extra_data is not None
            else b"",
            fork=self.fork,
        )

        if block.header_verify is not None:
            # Verify the header after transition tool processing.
            try:
                block.header_verify.verify(header)
            except Exception as e:
                raise Exception(
                    f"Verification of block {int(env.number)} failed"
                ) from e

        if last_block and self._operation_mode == OpMode.BENCHMARKING:
            expected_benchmark_gas_used = self.expected_benchmark_gas_used
            assert expected_benchmark_gas_used is not None, (
                "expected_benchmark_gas_used is not set"
            )
            gas_used = int(transition_tool_output.result.gas_used)

            if not self.skip_gas_used_validation:
                diff = gas_used - expected_benchmark_gas_used
                assert gas_used == expected_benchmark_gas_used, (
                    f"gas_used ({gas_used}) does not match "
                    f"expected_benchmark_gas_used "
                    f"({expected_benchmark_gas_used}), difference: {diff}"
                )

        requests_list: List[Bytes] | None = None
        if self.fork.header_requests_required(
            block_number=header.number, timestamp=header.timestamp
        ):
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

        if self.fork.header_bal_hash_required(
            block_number=header.number, timestamp=header.timestamp
        ):
            assert (
                transition_tool_output.result.block_access_list is not None
            ), (
                "Block access list is required for this block but was not "
                "provided by the transition tool"
            )

            rlp = transition_tool_output.result.block_access_list.rlp
            computed_bal_hash = Hash(rlp.keccak256())
            assert computed_bal_hash == header.block_access_list_hash, (
                "Block access list hash in header does not match the "
                f"computed hash from BAL: {header.block_access_list_hash} "
                f"!= {computed_bal_hash}"
            )

        if block.rlp_modifier is not None:
            # Modify any parameter specified in the `rlp_modifier` after
            # transition tool processing.
            header = block.rlp_modifier.apply(header)
            header.fork = (
                self.fork
            )  # Deleted during `apply` because `exclude=True`

        # Process block access list - apply transformer if present for invalid
        # tests
        t8n_bal = transition_tool_output.result.block_access_list
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
                # If the BAL was modified, update the header hash
                header.block_access_list_hash = Hash(bal.rlp.keccak256())

        built_block = BuiltBlock(
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
            fork=self.fork,
            block_access_list=bal,
        )

        try:
            rejected_txs = built_block.verify_transactions(
                transition_tool_exceptions_reliable=t8n.exception_mapper.reliable,
            )
            if (
                not rejected_txs
                and block.rlp_modifier is None
                and block.requests is None
                and not block.skip_exception_verification
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
                # what normally produces the block exception. - No BAL modifier
                # was specified, because modified BAL also produces block
                # exceptions.
                built_block.verify_block_exception(
                    transition_tool_exceptions_reliable=t8n.exception_mapper.reliable,
                )
            verify_result(transition_tool_output.result, env)
        except Exception as e:
            print_traces(t8n.get_traces())
            pprint(transition_tool_output.result)
            pprint(previous_alloc)
            pprint(transition_tool_output.alloc.get())
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
        t8n: TransitionTool,
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
        t8n: TransitionTool,
    ) -> BlockchainFixture:
        """Create a fixture from the blockchain test definition."""
        fixture_blocks: List[FixtureBlock | InvalidFixtureBlock] = []

        pre, genesis = self.make_genesis(apply_pre_allocation_blockchain=True)

        alloc: Alloc | LazyAlloc = pre
        state_root = genesis.header.state_root
        env = environment_from_parent_header(genesis.header)
        head = genesis.header.block_hash
        invalid_blocks = 0
        for i, block in enumerate(self.blocks):
            # This is the most common case, the RLP needs to be constructed
            # based on the transactions to be included in the block.
            # Set the environment according to the block to execute.
            built_block = self.generate_block_data(
                t8n=t8n,
                block=block,
                previous_env=env,
                previous_alloc=alloc,
                last_block=i == len(self.blocks) - 1,
            )
            fixture_blocks.append(built_block.get_fixture_block())

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
                    t8n_state=alloc.get()
                    if isinstance(alloc, LazyAlloc)
                    else alloc,
                    expected_state=block.expected_post_state,
                )
        self.check_exception_test(exception=invalid_blocks > 0)
        alloc = alloc.get() if isinstance(alloc, LazyAlloc) else alloc
        self.verify_post_state(t8n, t8n_state=alloc)
        info = {}
        if self._opcode_count is not None:
            info["opcode_count"] = self._opcode_count.model_dump()
        return BlockchainFixture(
            fork=self.fork,
            genesis=genesis.header,
            genesis_rlp=genesis.rlp,
            blocks=fixture_blocks,
            last_block_hash=head,
            pre=pre,
            post_state=alloc
            if not self.exclude_full_post_state_in_output
            else None,
            post_state_hash=state_root
            if self.exclude_full_post_state_in_output
            else None,
            config=FixtureConfig(
                fork=self.fork,
                blob_schedule=FixtureBlobSchedule.from_blob_schedule(
                    self.fork.blob_schedule()
                ),
                chain_id=self.chain_id,
            ),
            info=info,
        )

    def make_hive_fixture(
        self,
        t8n: TransitionTool,
        fixture_format: FixtureFormat = BlockchainEngineFixture,
    ) -> (
        BlockchainEngineFixture
        | BlockchainEngineXFixture
        | BlockchainEngineSyncFixture
    ):
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
        for i, block in enumerate(self.blocks):
            built_block = self.generate_block_data(
                t8n=t8n,
                block=block,
                previous_env=env,
                previous_alloc=alloc,
                last_block=i == len(self.blocks) - 1,
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
                    t8n_state=alloc.get()
                    if isinstance(alloc, LazyAlloc)
                    else alloc,
                    expected_state=block.expected_post_state,
                )
        self.check_exception_test(exception=invalid_blocks > 0)
        fcu_version = self.fork.engine_forkchoice_updated_version(
            block_number=built_block.header.number,
            timestamp=built_block.header.timestamp,
        )
        assert fcu_version is not None, (
            "A hive fixture was requested but no forkchoice update is defined."
            " The framework should never try to execute this test case."
        )

        alloc = alloc.get() if isinstance(alloc, LazyAlloc) else alloc
        self.verify_post_state(t8n, t8n_state=alloc)

        # Create base fixture data, common to all fixture formats
        info = {}
        if self._opcode_count is not None:
            info["opcode_count"] = self._opcode_count.model_dump()
        fixture_data = {
            "fork": self.fork,
            "genesis": genesis.header,
            "payloads": fixture_payloads,
            "last_block_hash": head_hash,
            "post_state_hash": state_root
            if self.exclude_full_post_state_in_output
            else None,
            "config": FixtureConfig(
                fork=self.fork,
                chain_id=self.chain_id,
                blob_schedule=FixtureBlobSchedule.from_blob_schedule(
                    self.fork.blob_schedule()
                ),
            ),
            "info": info,
        }

        # Add format-specific fields
        if fixture_format == BlockchainEngineXFixture:
            # For Engine X format, exclude pre (will be provided via shared
            # state) and prepare for state diff optimization
            fixture_data.update(
                {
                    "post_state": alloc
                    if not self.exclude_full_post_state_in_output
                    else None,
                    "pre_hash": "",  # Will be set by BaseTestWrapper
                }
            )
            return BlockchainEngineXFixture(**fixture_data)
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
                last_block=False,
            )
            fixture_data.update(
                {
                    "sync_payload": (
                        sync_built_block.get_fixture_engine_new_payload()
                    ),
                    "pre": pre,
                    "post_state": alloc
                    if not self.exclude_full_post_state_in_output
                    else None,
                }
            )
            return BlockchainEngineSyncFixture(**fixture_data)
        else:
            # Standard engine fixture
            fixture_data.update(
                {
                    "pre": pre,
                    "post_state": alloc
                    if not self.exclude_full_post_state_in_output
                    else None,
                }
            )
            return BlockchainEngineFixture(**fixture_data)

    def generate(
        self,
        t8n: TransitionTool,
        fixture_format: FixtureFormat,
    ) -> BaseFixture:
        """Generate the BlockchainTest fixture."""
        t8n.reset_traces()
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
        execute_format: ExecuteFormat,
    ) -> BaseExecute:
        """Generate the list of test fixtures."""
        if execute_format == TransactionPost:
            blocks: List[List[Transaction]] = []
            for block in self.blocks:
                blocks += [block.txs]
            # Pass gas validation params for benchmark tests
            # If not benchmark mode, skip gas used validation
            if self._operation_mode != OpMode.BENCHMARKING:
                self.skip_gas_used_validation = True

            return TransactionPost(
                blocks=blocks,
                post=self.post,
                expected_benchmark_gas_used=self.expected_benchmark_gas_used,
                skip_gas_used_validation=self.skip_gas_used_validation,
            )
        raise Exception(f"Unsupported execute format: {execute_format}")


BlockchainTestSpec = Callable[[str], Generator[BlockchainTest, None, None]]
BlockchainTestFiller = Type[BlockchainTest]
