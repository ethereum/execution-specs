"""Ethereum blockchain test spec definition and filler."""

from pprint import pprint
from typing import Any, Callable, ClassVar, Dict, Generator, List, Optional, Sequence, Tuple, Type

import pytest
from pydantic import ConfigDict, Field, field_validator

from ethereum_clis import TransitionTool
from ethereum_test_base_types import (
    Address,
    Bloom,
    Bytes,
    CamelModel,
    EmptyOmmersRoot,
    EmptyTrieRoot,
    Hash,
    HeaderNonce,
    HexNumber,
    Number,
)
from ethereum_test_exceptions import BlockException, EngineAPIError, TransactionException
from ethereum_test_execution import (
    BaseExecute,
    ExecuteFormat,
    LabeledExecuteFormat,
    TransactionPost,
)
from ethereum_test_fixtures import (
    BaseFixture,
    BlockchainEngineFixture,
    BlockchainFixture,
    FixtureFormat,
    LabeledFixtureFormat,
)
from ethereum_test_fixtures.blockchain import (
    FixtureBlock,
    FixtureBlockBase,
    FixtureConfig,
    FixtureEngineNewPayload,
    FixtureHeader,
    FixtureTransaction,
    FixtureWithdrawal,
    InvalidFixtureBlock,
)
from ethereum_test_fixtures.common import FixtureBlobSchedule
from ethereum_test_forks import Fork
from ethereum_test_types import Alloc, Environment, Removable, Requests, Transaction, Withdrawal

from .base import BaseTest, verify_result
from .debugging import print_traces
from .helpers import is_slow_test, verify_transactions


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


def apply_new_parent(env: Environment, new_parent: FixtureHeader) -> "Environment":
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
        [len(tx.blob_versioned_hashes) for tx in txs if tx.blob_versioned_hashes is not None]
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

    REMOVE_FIELD: ClassVar[Removable] = Removable()
    """
    Sentinel object used to specify that a header field should be removed.
    """
    EMPTY_FIELD: ClassVar[Removable] = Removable()
    """
    Sentinel object used to specify that a header field must be empty during verification.

    This can be used in a test to explicitly skip a field in a block's RLP encoding.
    included in the (json) output when the model is serialized. For example:
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
        arbitrary_types_allowed=True,
        # explicitly set Removable items to None so they are not included in the serialization
        # (in combination with exclude_None=True in model.dump()).
        json_encoders={
            Removable: lambda x: None,
        },
    )

    @field_validator("withdrawals_root", mode="before")
    @classmethod
    def validate_withdrawals_root(cls, value):
        """Convert a list of withdrawals into the withdrawals root hash."""
        if isinstance(value, list):
            return Withdrawal.list_root(value)
        return value

    def apply(self, target: FixtureHeader) -> FixtureHeader:
        """Produce a fixture header copy with the set values from the modifier."""
        return target.copy(
            **{
                k: (v if v is not Header.REMOVE_FIELD else None)
                for k, v in self.model_dump(exclude_none=True).items()
            }
        )

    def verify(self, target: FixtureHeader):
        """Verify that the header fields from self are as expected."""
        for field_name in self.model_fields:
            baseline_value = getattr(self, field_name)
            if baseline_value is not None:
                assert baseline_value is not Header.REMOVE_FIELD, "invalid header"
                value = getattr(target, field_name)
                if baseline_value is Header.EMPTY_FIELD:
                    assert value is None, (
                        f"invalid header field {field_name}, got {value}, want None"
                    )
                    continue
                assert value == baseline_value, (
                    f"invalid header field ({field_name}) value, "
                    + f"got {value}, want {baseline_value}"
                )


class Block(Header):
    """Block type used to describe block properties in test specs."""

    rlp: Bytes | None = None
    """
    If set, blockchain test will skip generating the block and will pass this value directly to
    the Fixture.

    Only meant to be used to simulate blocks with bad formats, and therefore
    requires the block to produce an exception.
    """
    header_verify: Header | None = None
    """
    If set, the block header will be verified against the specified values.
    """
    rlp_modifier: Header | None = None
    """
    An RLP modifying header which values would be used to override the ones
    returned by the `ethereum_clis.TransitionTool`.
    """
    exception: (
        List[TransactionException | BlockException] | TransactionException | BlockException | None
    ) = None
    """
    If set, the block is expected to be rejected by the client.
    """
    engine_api_error_code: EngineAPIError | None = None
    """
    If set, the block is expected to produce an error response from the Engine API.
    """
    txs: List[Transaction] = Field(default_factory=list)
    """
    List of transactions included in the block.
    """
    ommers: List[Header] | None = None
    """
    List of ommer headers included in the block.
    """
    withdrawals: List[Withdrawal] | None = None
    """
    List of withdrawals to perform for this block.
    """
    requests: List[Bytes] | None = None
    """
    Custom list of requests to embed in this block.
    """
    expected_post_state: Alloc | None = None
    """
    Post state for verification after block execution in BlockchainTest
    """

    def set_environment(self, env: Environment) -> Environment:
        """
        Create copy of the environment with the characteristics of this
        specific block.
        """
        new_env_values: Dict[str, Any] = {}

        """
        Values that need to be set in the environment and are `None` for
        this block need to be set to their defaults.
        """
        new_env_values["difficulty"] = self.difficulty
        new_env_values["fee_recipient"] = (
            self.fee_recipient if self.fee_recipient is not None else Environment().fee_recipient
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
            new_env_values["parent_beacon_block_root"] = self.parent_beacon_block_root
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
                new_env_values["number"] = max([Number(n) for n in env.block_hashes.keys()]) + 1

        if self.timestamp is not None:
            new_env_values["timestamp"] = self.timestamp
        else:
            assert env.parent_timestamp is not None
            new_env_values["timestamp"] = int(Number(env.parent_timestamp) + 12)

        return env.copy(**new_env_values)


class BlockchainTest(BaseTest):
    """Filler type that tests multiple blocks (valid or invalid) in a chain."""

    pre: Alloc
    post: Alloc
    blocks: List[Block]
    genesis_environment: Environment = Field(default_factory=Environment)
    verify_sync: bool = False
    chain_id: int = 1

    supported_fixture_formats: ClassVar[Sequence[FixtureFormat | LabeledFixtureFormat]] = [
        BlockchainFixture,
        BlockchainEngineFixture,
    ]
    supported_execute_formats: ClassVar[Sequence[LabeledExecuteFormat]] = [
        LabeledExecuteFormat(
            TransactionPost,
            "blockchain_test",
            "An execute test derived from a blockchain test",
        ),
    ]

    supported_markers: ClassVar[Dict[str, str]] = {
        "blockchain_test_engine_only": "Only generate a blockchain test engine fixture",
        "blockchain_test_only": "Only generate a blockchain test fixture",
    }

    @classmethod
    def discard_fixture_format_by_marks(
        cls,
        fixture_format: FixtureFormat,
        fork: Fork,
        markers: List[pytest.Mark],
    ) -> bool:
        """Discard a fixture format from filling if the appropriate marker is used."""
        if "blockchain_test_only" in [m.name for m in markers]:
            return fixture_format != BlockchainFixture
        if "blockchain_test_engine_only" in [m.name for m in markers]:
            return fixture_format != BlockchainEngineFixture
        return False

    @staticmethod
    def make_genesis(
        genesis_environment: Environment,
        pre: Alloc,
        fork: Fork,
    ) -> Tuple[Alloc, FixtureBlock]:
        """Create a genesis block from the blockchain test definition."""
        env = genesis_environment.set_fork_requirements(fork)
        assert env.withdrawals is None or len(env.withdrawals) == 0, (
            "withdrawals must be empty at genesis"
        )
        assert env.parent_beacon_block_root is None or env.parent_beacon_block_root == Hash(0), (
            "parent_beacon_block_root must be empty at genesis"
        )

        pre_alloc = Alloc.merge(
            Alloc.model_validate(fork.pre_allocation_blockchain()),
            pre,
        )
        if empty_accounts := pre_alloc.empty_accounts():
            raise Exception(f"Empty accounts in pre state: {empty_accounts}")
        state_root = pre_alloc.state_root()
        genesis = FixtureHeader(
            parent_hash=0,
            ommers_hash=EmptyOmmersRoot,
            fee_recipient=0,
            state_root=state_root,
            transactions_trie=EmptyTrieRoot,
            receipts_root=EmptyTrieRoot,
            logs_bloom=0,
            difficulty=0x20000 if env.difficulty is None else env.difficulty,
            number=0,
            gas_limit=env.gas_limit,
            gas_used=0,
            timestamp=0,
            extra_data=b"\x00",
            prev_randao=0,
            nonce=0,
            base_fee_per_gas=env.base_fee_per_gas,
            blob_gas_used=env.blob_gas_used,
            excess_blob_gas=env.excess_blob_gas,
            withdrawals_root=(
                Withdrawal.list_root(env.withdrawals) if env.withdrawals is not None else None
            ),
            parent_beacon_block_root=env.parent_beacon_block_root,
            requests_hash=Requests() if fork.header_requests_required(0, 0) else None,
            fork=fork,
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
        t8n: TransitionTool,
        fork: Fork,
        block: Block,
        previous_env: Environment,
        previous_alloc: Alloc,
        eips: Optional[List[int]] = None,
        slow: bool = False,
    ) -> Tuple[FixtureHeader, List[Transaction], List[Bytes] | None, Alloc, Environment]:
        """Generate common block data for both make_fixture and make_hive_fixture."""
        if block.rlp and block.exception is not None:
            raise Exception(
                "test correctness: post-state cannot be verified if the "
                + "block's rlp is supplied and the block is not supposed "
                + "to produce an exception"
            )

        env = block.set_environment(previous_env)
        env = env.set_fork_requirements(fork)

        txs = [tx.with_signature_and_sender() for tx in block.txs]

        if failing_tx_count := len([tx for tx in txs if tx.error]) > 0:
            if failing_tx_count > 1:
                raise Exception(
                    "test correctness: only one transaction can produce an exception in a block"
                )
            if not txs[-1].error:
                raise Exception(
                    "test correctness: the transaction that produces an exception "
                    + "must be the last transaction in the block"
                )

        transition_tool_output = t8n.evaluate(
            alloc=previous_alloc,
            txs=txs,
            env=env,
            fork=fork,
            chain_id=self.chain_id,
            reward=fork.get_reward(env.number, env.timestamp),
            blob_schedule=fork.blob_schedule(),
            eips=eips,
            debug_output_path=self.get_next_transition_tool_output_path(),
            slow_request=slow,
        )

        try:
            rejected_txs = verify_transactions(
                txs=txs,
                exception_mapper=t8n.exception_mapper,
                result=transition_tool_output.result,
            )
            verify_result(transition_tool_output.result, env)
        except Exception as e:
            print_traces(t8n.get_traces())
            pprint(transition_tool_output.result)
            pprint(previous_alloc)
            pprint(transition_tool_output.alloc)
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

        # One special case of the invalid transactions is the blob gas used, since this value
        # is not included in the transition tool result, but it is included in the block header,
        # and some clients check it before executing the block by simply counting the type-3 txs,
        # we need to set the correct value by default.
        blob_gas_used: int | None = None
        if (blob_gas_per_blob := fork.blob_gas_per_blob(env.number, env.timestamp)) > 0:
            blob_gas_used = blob_gas_per_blob * count_blobs(txs)

        header = FixtureHeader(
            **(
                transition_tool_output.result.model_dump(
                    exclude_none=True, exclude={"blob_gas_used", "transactions_trie"}
                )
                | env.model_dump(exclude_none=True, exclude={"blob_gas_used"})
            ),
            blob_gas_used=blob_gas_used,
            transactions_trie=Transaction.list_root(txs),
            extra_data=block.extra_data if block.extra_data is not None else b"",
            fork=fork,
        )

        if block.header_verify is not None:
            # Verify the header after transition tool processing.
            block.header_verify.verify(header)

        requests_list: List[Bytes] | None = None
        if fork.header_requests_required(header.number, header.timestamp):
            assert transition_tool_output.result.requests is not None, (
                "Requests are required for this block"
            )
            requests = Requests(requests_lists=list(transition_tool_output.result.requests))

            if Hash(requests) != header.requests_hash:
                raise Exception(
                    "Requests root in header does not match the requests root in the transition "
                    "tool output: "
                    f"{header.requests_hash} != {Hash(requests)}"
                )

            requests_list = requests.requests_list

        if block.requests is not None:
            header.requests_hash = Hash(Requests(requests_lists=list(block.requests)))
            requests_list = block.requests

        if block.rlp_modifier is not None:
            # Modify any parameter specified in the `rlp_modifier` after
            # transition tool processing.
            header = block.rlp_modifier.apply(header)
            header.fork = fork  # Deleted during `apply` because `exclude=True`

        return (
            header,
            txs,
            requests_list,
            transition_tool_output.alloc,
            env,
        )

    @staticmethod
    def network_info(fork: Fork, eips: Optional[List[int]] = None):
        """Return fixture network information for the fork & EIP/s."""
        return (
            "+".join([fork.blockchain_test_network_name()] + [str(eip) for eip in eips])
            if eips
            else fork.blockchain_test_network_name()
        )

    def verify_post_state(self, t8n, t8n_state: Alloc, expected_state: Alloc | None = None):
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
        fork: Fork,
        eips: Optional[List[int]] = None,
        slow: bool = False,
    ) -> BlockchainFixture:
        """Create a fixture from the blockchain test definition."""
        fixture_blocks: List[FixtureBlock | InvalidFixtureBlock] = []

        pre, genesis = BlockchainTest.make_genesis(self.genesis_environment, self.pre, fork)

        alloc = pre
        env = environment_from_parent_header(genesis.header)
        head = genesis.header.block_hash

        for block in self.blocks:
            if block.rlp is None:
                # This is the most common case, the RLP needs to be constructed
                # based on the transactions to be included in the block.
                # Set the environment according to the block to execute.
                header, txs, _, new_alloc, new_env = self.generate_block_data(
                    t8n=t8n,
                    fork=fork,
                    block=block,
                    previous_env=env,
                    previous_alloc=alloc,
                    eips=eips,
                    slow=slow,
                )
                fixture_block = FixtureBlockBase(
                    header=header,
                    txs=[FixtureTransaction.from_transaction(tx) for tx in txs],
                    ommers=[],
                    withdrawals=(
                        [FixtureWithdrawal.from_withdrawal(w) for w in new_env.withdrawals]
                        if new_env.withdrawals is not None
                        else None
                    ),
                    fork=fork,
                ).with_rlp(txs=txs)
                if block.exception is None:
                    fixture_blocks.append(fixture_block)
                    # Update env, alloc and last block hash for the next block.
                    alloc = new_alloc
                    env = apply_new_parent(new_env, header)
                    head = header.block_hash
                else:
                    fixture_blocks.append(
                        InvalidFixtureBlock(
                            rlp=fixture_block.rlp,
                            expect_exception=block.exception,
                            rlp_decoded=(
                                None
                                if BlockException.RLP_STRUCTURES_ENCODING in block.exception
                                else fixture_block.without_rlp()
                            ),
                        ),
                    )
            else:
                assert block.exception is not None, (
                    "test correctness: if the block's rlp is hard-coded, "
                    + "the block is expected to produce an exception"
                )
                fixture_blocks.append(
                    InvalidFixtureBlock(
                        rlp=block.rlp,
                        expect_exception=block.exception,
                    ),
                )

            if block.expected_post_state:
                self.verify_post_state(
                    t8n, t8n_state=alloc, expected_state=block.expected_post_state
                )

        self.verify_post_state(t8n, t8n_state=alloc)
        network_info = BlockchainTest.network_info(fork, eips)
        return BlockchainFixture(
            fork=network_info,
            genesis=genesis.header,
            genesis_rlp=genesis.rlp,
            blocks=fixture_blocks,
            last_block_hash=head,
            pre=pre,
            post_state=alloc,
            config=FixtureConfig(
                fork=network_info,
                blob_schedule=FixtureBlobSchedule.from_blob_schedule(fork.blob_schedule()),
                chain_id=self.chain_id,
            ),
        )

    def make_hive_fixture(
        self,
        t8n: TransitionTool,
        fork: Fork,
        eips: Optional[List[int]] = None,
        slow: bool = False,
    ) -> BlockchainEngineFixture:
        """Create a hive fixture from the blocktest definition."""
        fixture_payloads: List[FixtureEngineNewPayload] = []

        pre, genesis = BlockchainTest.make_genesis(self.genesis_environment, self.pre, fork)
        alloc = pre
        env = environment_from_parent_header(genesis.header)
        head_hash = genesis.header.block_hash

        for block in self.blocks:
            header, txs, requests, new_alloc, new_env = self.generate_block_data(
                t8n=t8n,
                fork=fork,
                block=block,
                previous_env=env,
                previous_alloc=alloc,
                eips=eips,
                slow=slow,
            )
            if block.rlp is None:
                fixture_payloads.append(
                    FixtureEngineNewPayload.from_fixture_header(
                        fork=fork,
                        header=header,
                        transactions=txs,
                        withdrawals=new_env.withdrawals,
                        requests=requests,
                        validation_error=block.exception,
                        error_code=block.engine_api_error_code,
                    )
                )
                if block.exception is None:
                    alloc = new_alloc
                    env = apply_new_parent(env, header)
                    head_hash = header.block_hash

            if block.expected_post_state:
                self.verify_post_state(
                    t8n, t8n_state=alloc, expected_state=block.expected_post_state
                )

        fcu_version = fork.engine_forkchoice_updated_version(header.number, header.timestamp)
        assert fcu_version is not None, (
            "A hive fixture was requested but no forkchoice update is defined."
            " The framework should never try to execute this test case."
        )

        self.verify_post_state(t8n, t8n_state=alloc)

        sync_payload: Optional[FixtureEngineNewPayload] = None
        if self.verify_sync:
            # Test is marked for syncing verification.
            assert genesis.header.block_hash != head_hash, (
                "Invalid payload tests negative test via sync is not supported yet."
            )

            # Most clients require the header to start the sync process, so we create an empty
            # block on top of the last block of the test to send it as new payload and trigger the
            # sync process.
            sync_header, _, requests, _, _ = self.generate_block_data(
                t8n=t8n,
                fork=fork,
                block=Block(),
                previous_env=env,
                previous_alloc=alloc,
                eips=eips,
            )
            sync_payload = FixtureEngineNewPayload.from_fixture_header(
                fork=fork,
                header=sync_header,
                transactions=[],
                withdrawals=[],
                requests=requests,
                validation_error=None,
                error_code=None,
            )

        network_info = BlockchainTest.network_info(fork, eips)
        return BlockchainEngineFixture(
            fork=network_info,
            genesis=genesis.header,
            payloads=fixture_payloads,
            fcu_version=fcu_version,
            pre=pre,
            post_state=alloc,
            sync_payload=sync_payload,
            last_block_hash=head_hash,
            config=FixtureConfig(
                fork=network_info,
                chain_id=self.chain_id,
                blob_schedule=FixtureBlobSchedule.from_blob_schedule(fork.blob_schedule()),
            ),
        )

    def generate(
        self,
        request: pytest.FixtureRequest,
        t8n: TransitionTool,
        fork: Fork,
        fixture_format: FixtureFormat,
        eips: Optional[List[int]] = None,
    ) -> BaseFixture:
        """Generate the BlockchainTest fixture."""
        t8n.reset_traces()
        if fixture_format == BlockchainEngineFixture:
            return self.make_hive_fixture(t8n, fork, eips, slow=is_slow_test(request))
        elif fixture_format == BlockchainFixture:
            return self.make_fixture(t8n, fork, eips, slow=is_slow_test(request))

        raise Exception(f"Unknown fixture format: {fixture_format}")

    def execute(
        self,
        *,
        fork: Fork,
        execute_format: ExecuteFormat,
        eips: Optional[List[int]] = None,
    ) -> BaseExecute:
        """Generate the list of test fixtures."""
        if execute_format == TransactionPost:
            blocks: List[List[Transaction]] = []
            for block in self.blocks:
                blocks += [block.txs]
            return TransactionPost(
                blocks=blocks,
                post=self.post,
            )
        raise Exception(f"Unsupported execute format: {execute_format}")


BlockchainTestSpec = Callable[[str], Generator[BlockchainTest, None, None]]
BlockchainTestFiller = Type[BlockchainTest]
