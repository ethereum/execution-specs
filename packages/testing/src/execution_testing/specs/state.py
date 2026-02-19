"""Ethereum state test spec definition and filler."""

from pprint import pprint
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generator,
    List,
    Optional,
    Sequence,
    Type,
)

import pytest
from pydantic import Field

from execution_testing.base_types import HexNumber
from execution_testing.client_clis import (
    Result,
    TransitionTool,
)
from execution_testing.exceptions import (
    BlockException,
    EngineAPIError,
    TransactionException,
)
from execution_testing.execution import (
    BaseExecute,
    ExecuteFormat,
    LabeledExecuteFormat,
    TransactionPost,
)
from execution_testing.fixtures import (
    BaseFixture,
    FixtureFormat,
    LabeledFixtureFormat,
    StateFixture,
)
from execution_testing.fixtures.common import FixtureBlobSchedule
from execution_testing.fixtures.state import (
    FixtureConfig,
    FixtureEnvironment,
    FixtureForkPost,
    FixtureTransaction,
    FixtureTransactionReceipt,
)
from execution_testing.forks import Fork
from execution_testing.logging import (
    get_logger,
)
from execution_testing.test_types import (
    Alloc,
    BlockAccessListExpectation,
    Environment,
    Transaction,
)

from .base import BaseTest, OpMode
from .blockchain import Block, BlockchainTest, Header
from .debugging import print_traces
from .helpers import verify_transactions

logger = get_logger(__name__)


class StateTest(BaseTest):
    """
    Filler type that tests transactions over the period of a single block.
    """

    env: Environment = Field(default_factory=Environment)
    pre: Alloc
    post: Alloc
    tx: Transaction
    block_exception: (
        List[TransactionException | BlockException]
        | TransactionException
        | BlockException
        | None
    ) = None
    engine_api_error_code: Optional[EngineAPIError] = None
    blockchain_test_header_verify: Optional[Header] = None
    blockchain_test_rlp_modifier: Optional[Header] = None
    expected_block_access_list: Optional[BlockAccessListExpectation] = None
    chain_id: int = 1

    supported_fixture_formats: ClassVar[
        Sequence[FixtureFormat | LabeledFixtureFormat]
    ] = [
        StateFixture,
    ] + [
        LabeledFixtureFormat(
            fixture_format,
            f"{fixture_format.format_name}_from_state_test",
            f"A {fixture_format.format_name} generated from a state_test",
        )
        for fixture_format in BlockchainTest.supported_fixture_formats
        # Exclude sync fixtures from state tests - they don't make sense for
        # state tests
        if not (
            (
                hasattr(fixture_format, "__name__")
                and "Sync" in fixture_format.__name__
            )
            or (
                hasattr(fixture_format, "format")
                and "Sync" in fixture_format.format.__name__
            )
        )
    ]
    supported_execute_formats: ClassVar[Sequence[LabeledExecuteFormat]] = [
        LabeledExecuteFormat(
            TransactionPost,
            "state_test",
            "An execute test derived from a state test",
        ),
    ]

    supported_markers: ClassVar[Dict[str, str]] = {
        "state_test_only": "Only generate a state test fixture",
    }

    def verify_modified_gas_limit(
        self,
        *,
        t8n: TransitionTool,
        base_tool_result: Result,
        base_tool_alloc: Alloc,
        fork: Fork,
        current_gas_limit: int,
        pre_alloc: Alloc,
        env: Environment,
        enable_post_processing: bool,
    ) -> bool:
        """Verify a new lower gas limit yields the same transaction outcome."""
        base_traces = base_tool_result.traces
        assert base_traces is not None, (
            "Traces not collected for gas optimization"
        )
        new_tx = self.tx.copy(
            gas_limit=current_gas_limit
        ).with_signature_and_sender()
        modified_tool_output = t8n.evaluate(
            transition_tool_data=TransitionTool.TransitionToolData(
                alloc=pre_alloc,
                txs=[new_tx],
                env=env,
                fork=fork,
                chain_id=self.chain_id,
                reward=0,  # Reward on state tests is always zero
                blob_schedule=fork.blob_schedule(),
                state_test=True,
            ),
            debug_output_path=self.get_next_transition_tool_output_path(),
            slow_request=self.is_tx_gas_heavy_test(),
        )
        modified_traces = modified_tool_output.result.traces
        assert modified_traces is not None, (
            "Traces not collected for gas optimization"
        )
        if not base_traces.are_equivalent(
            modified_tool_output.result.traces,
            enable_post_processing,
        ):
            logger.debug(
                f"Traces are not equivalent (gas_limit={current_gas_limit})"
            )
            return False
        modified_tool_alloc = modified_tool_output.alloc.get()
        try:
            self.post.verify_post_alloc(modified_tool_alloc)
        except Exception as e:
            logger.debug(
                f"Post alloc is not equivalent (gas_limit={current_gas_limit})"
            )
            logger.debug(e)
            return False
        try:
            verify_transactions(
                txs=[new_tx],
                result=modified_tool_output.result,
                transition_tool_exceptions_reliable=t8n.exception_mapper.reliable,
            )
        except Exception as e:
            logger.debug(
                "Transactions are not equivalent "
                f"(gas_limit={current_gas_limit})"
            )
            logger.debug(e)
            return False
        if len(base_tool_alloc.root) != len(modified_tool_alloc.root):
            logger.debug(
                f"Post alloc is not equivalent (gas_limit={current_gas_limit})"
            )
            return False
        if base_tool_alloc.root.keys() != modified_tool_alloc.root.keys():
            logger.debug(
                f"Post alloc is not equivalent (gas_limit={current_gas_limit})"
            )
            return False
        for k in base_tool_alloc.root.keys():
            if k not in modified_tool_alloc:
                logger.debug(
                    "Post alloc is not equivalent "
                    f"(gas_limit={current_gas_limit})"
                )
                return False
            base_account = base_tool_alloc[k]
            modified_account = modified_tool_alloc[k]
            if (modified_account is None) != (base_account is None):
                logger.debug(
                    "Post alloc is not equivalent "
                    f"(gas_limit={current_gas_limit})"
                )
                return False
            if (
                modified_account is not None
                and base_account is not None
                and base_account.nonce != modified_account.nonce
            ):
                logger.debug(
                    "Post alloc is not equivalent "
                    f"(gas_limit={current_gas_limit})"
                )
                return False
        logger.debug(
            f"Gas limit is equivalent (gas_limit={current_gas_limit})"
        )
        return True

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

        if "state_test_only" in [m.name for m in markers]:
            return fixture_format != StateFixture
        return False

    def _generate_blockchain_genesis_environment(self) -> Environment:
        """
        Generate the genesis environment for the BlockchainTest formatted test.
        """
        assert self.env.number >= 1, (
            "genesis block number cannot be negative, set state test "
            "env.number to at least 1"
        )
        assert self.env.timestamp >= 1, (
            "genesis timestamp cannot be negative, set state test "
            "env.timestamp to at least 1"
        )
        # There's only a handful of values that we need to set in the genesis
        # for the environment values at block 1 to make sense:
        # - Number: Needs to be N minus 1
        # - Timestamp: Needs to be zero, because the subsequent
        #              block can come at any time.
        # - Gas Limit: Changes from parent to child, needs to be set in genesis
        # - Base Fee Per Gas: Block's base fee depends on the parent's value
        # - Excess Blob Gas: Block's excess blob gas value depends on
        #                    the parent's value
        kwargs: Dict[str, Any] = {
            "number": self.env.number - 1,
            "timestamp": 0,
        }

        if "gas_limit" in self.env.model_fields_set:
            kwargs["gas_limit"] = self.env.gas_limit

        if self.env.base_fee_per_gas:
            # Calculate genesis base fee per gas from state test's block#1 env
            kwargs["base_fee_per_gas"] = HexNumber(
                int(int(str(self.env.base_fee_per_gas), 0) * 8 / 7)
            )

        if self.env.excess_blob_gas:
            # The excess blob gas environment value means the value of the
            # context (block header) where the transaction is executed. In a
            # blockchain test, we need to indirectly set the excess blob gas by
            # setting the excess blob gas of the genesis block to the expected
            # value plus the TARGET_BLOB_GAS_PER_BLOCK, which is the value that
            # will be subtracted from the excess blob gas when the first block
            # is mined.
            kwargs["excess_blob_gas"] = self.env.excess_blob_gas + (
                self.fork.target_blobs_per_block()
                * self.fork.blob_gas_per_blob()
            )

        return Environment(**kwargs)

    def _generate_blockchain_blocks(self) -> List[Block]:
        """
        Generate the single block that represents this state test in a
        BlockchainTest format.
        """
        kwargs = {
            "number": self.env.number,
            "timestamp": self.env.timestamp,
            "prev_randao": self.env.prev_randao,
            "fee_recipient": self.env.fee_recipient,
            "gas_limit": self.env.gas_limit,
            "extra_data": self.env.extra_data,
            "withdrawals": self.env.withdrawals,
            "parent_beacon_block_root": self.env.parent_beacon_block_root,
            "txs": [self.tx],
            "ommers": [],
            "header_verify": self.blockchain_test_header_verify,
            "rlp_modifier": self.blockchain_test_rlp_modifier,
            "expected_block_access_list": self.expected_block_access_list,
        }
        if not self.fork.header_prev_randao_required():
            kwargs["difficulty"] = self.env.difficulty
        if "block_exception" in self.model_fields_set:
            kwargs["exception"] = self.block_exception  # type: ignore
        elif "error" in self.tx.model_fields_set:
            kwargs["exception"] = self.tx.error  # type: ignore
        return [Block(**kwargs)]

    def generate_blockchain_test(self) -> BlockchainTest:
        """Generate a BlockchainTest fixture from this StateTest fixture."""
        return BlockchainTest.from_test(
            base_test=self,
            genesis_environment=self._generate_blockchain_genesis_environment(),
            pre=self.pre,
            post=self.post,
            blocks=self._generate_blockchain_blocks(),
        )

    def make_state_test_fixture(
        self,
        t8n: TransitionTool,
    ) -> StateFixture:
        """Create a fixture from the state test definition."""
        # We can't generate a state test fixture that names a transition fork,
        # so we get the fork at the block number and timestamp of the state
        # test
        fork = self.fork.fork_at(
            block_number=self.env.number, timestamp=self.env.timestamp
        )

        env = self.env.set_fork_requirements(fork)
        tx = self.tx.with_signature_and_sender(keep_secret_key=True)
        pre_alloc = Alloc.merge(
            Alloc.model_validate(fork.pre_allocation()),
            self.pre,
        )
        if empty_accounts := pre_alloc.empty_accounts():
            raise Exception(f"Empty accounts in pre state: {empty_accounts}")

        transition_tool_output = t8n.evaluate(
            transition_tool_data=TransitionTool.TransitionToolData(
                alloc=pre_alloc,
                txs=[tx],
                env=env,
                fork=fork,
                chain_id=self.chain_id,
                reward=0,  # Reward on state tests is always zero
                blob_schedule=fork.blob_schedule(),
                state_test=True,
            ),
            debug_output_path=self.get_next_transition_tool_output_path(),
            slow_request=self.is_tx_gas_heavy_test(),
        )
        output_alloc = transition_tool_output.alloc.get()

        try:
            self.post.verify_post_alloc(output_alloc)
        except Exception as e:
            print_traces(t8n.get_traces())
            raise e

        try:
            verify_transactions(
                txs=[tx],
                result=transition_tool_output.result,
                transition_tool_exceptions_reliable=t8n.exception_mapper.reliable,
            )
        except Exception as e:
            print_traces(t8n.get_traces())
            pprint(transition_tool_output.result)
            pprint(output_alloc)
            raise e

        if (
            self._operation_mode == OpMode.OPTIMIZE_GAS
            or self._operation_mode == OpMode.OPTIMIZE_GAS_POST_PROCESSING
        ):
            enable_post_processing = (
                self._operation_mode == OpMode.OPTIMIZE_GAS_POST_PROCESSING
            )
            base_tool_output = transition_tool_output
            base_tool_alloc = base_tool_output.alloc.get()
            base_tool_result = base_tool_output.result

            assert base_tool_result.traces is not None, "Traces not found."

            # First try reducing the gas limit only by one, if the validation
            # fails, it means that the traces change even with the slightest
            # modification to the gas.
            if self.verify_modified_gas_limit(
                t8n=t8n,
                base_tool_result=base_tool_result,
                base_tool_alloc=base_tool_alloc,
                fork=fork,
                current_gas_limit=self.tx.gas_limit - 1,
                pre_alloc=pre_alloc,
                env=env,
                enable_post_processing=enable_post_processing,
            ):
                minimum_gas_limit = 0
                maximum_gas_limit = int(self.tx.gas_limit)
                while minimum_gas_limit < maximum_gas_limit:
                    current_gas_limit = (
                        maximum_gas_limit + minimum_gas_limit
                    ) // 2
                    if self.verify_modified_gas_limit(
                        t8n=t8n,
                        base_tool_result=base_tool_result,
                        base_tool_alloc=base_tool_alloc,
                        fork=fork,
                        current_gas_limit=current_gas_limit,
                        pre_alloc=pre_alloc,
                        env=env,
                        enable_post_processing=enable_post_processing,
                    ):
                        maximum_gas_limit = current_gas_limit
                    else:
                        minimum_gas_limit = current_gas_limit + 1
                        if (
                            self._gas_optimization_max_gas_limit is not None
                            and minimum_gas_limit
                            > self._gas_optimization_max_gas_limit
                        ):
                            raise Exception(
                                "Requires more than the minimum "
                                f"{self._gas_optimization_max_gas_limit} "
                                "wanted."
                            )

                assert self.verify_modified_gas_limit(
                    t8n=t8n,
                    base_tool_result=base_tool_result,
                    base_tool_alloc=base_tool_alloc,
                    fork=fork,
                    current_gas_limit=minimum_gas_limit,
                    pre_alloc=pre_alloc,
                    env=env,
                    enable_post_processing=enable_post_processing,
                )
                self._gas_optimization = current_gas_limit
            else:
                raise Exception("Impossible to compare.")

        if self._operation_mode == OpMode.BENCHMARKING:
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
        if len(transition_tool_output.result.receipts) == 1:
            receipt = FixtureTransactionReceipt.from_transaction_receipt(
                transition_tool_output.result.receipts[0], tx
            )
            receipt_root = FixtureTransactionReceipt.list_root([receipt])
            assert (
                transition_tool_output.result.receipts_root == receipt_root
            ), (
                f"Receipts root mismatch: "
                f"{transition_tool_output.result.receipts_root} != "
                f"{receipt_root.hex()}"
                f"Receipt: {receipt.rlp()}"
            )
        else:
            receipt = None

        return StateFixture(
            env=FixtureEnvironment(**env.model_dump(exclude_none=True)),
            pre=pre_alloc,
            post={
                fork: [
                    FixtureForkPost(
                        state_root=transition_tool_output.result.state_root,
                        logs_hash=transition_tool_output.result.logs_hash,
                        receipt=receipt,
                        tx_bytes=tx.rlp(),
                        expect_exception=tx.error,
                        state=output_alloc,
                    )
                ]
            },
            transaction=FixtureTransaction.from_transaction(tx),
            config=FixtureConfig(
                blob_schedule=FixtureBlobSchedule.from_blob_schedule(
                    fork.blob_schedule()
                ),
                chain_id=self.chain_id,
            ),
        )

    def get_genesis_environment(self) -> Environment:
        """Get the genesis environment for pre-allocation groups."""
        return self.generate_blockchain_test().get_genesis_environment()

    def generate(
        self,
        t8n: TransitionTool,
        fixture_format: FixtureFormat,
    ) -> BaseFixture:
        """Generate the BlockchainTest fixture."""
        self.check_exception_test(exception=self.tx.error is not None)
        if fixture_format in BlockchainTest.supported_fixture_formats:
            return self.generate_blockchain_test().generate(
                t8n=t8n, fixture_format=fixture_format
            )
        elif fixture_format == StateFixture:
            return self.make_state_test_fixture(t8n)

        raise Exception(f"Unknown fixture format: {fixture_format}")

    def execute(
        self,
        *,
        execute_format: ExecuteFormat,
    ) -> BaseExecute:
        """Generate the list of test fixtures."""
        if execute_format == TransactionPost:
            # Pass gas validation params for benchmark tests
            # If not benchmark mode, skip gas used validation
            if self._operation_mode != OpMode.BENCHMARKING:
                self.skip_gas_used_validation = True
            return TransactionPost(
                blocks=[[self.tx]],
                post=self.post,
                expected_benchmark_gas_used=self.expected_benchmark_gas_used,
                skip_gas_used_validation=self.skip_gas_used_validation,
            )
        raise Exception(f"Unsupported execute format: {execute_format}")


StateTestSpec = Callable[[str], Generator[StateTest, None, None]]
StateTestFiller = Type[StateTest]
