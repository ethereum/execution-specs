"""Ethereum state test spec definition and filler."""

import warnings
from pprint import pprint
from typing import Any, Callable, ClassVar, Dict, Generator, List, Optional, Sequence, Type

import pytest
from pydantic import Field

from ethereum_clis import TransitionTool
from ethereum_test_base_types import HexNumber
from ethereum_test_exceptions import BlockException, EngineAPIError, TransactionException
from ethereum_test_execution import (
    BaseExecute,
    ExecuteFormat,
    LabeledExecuteFormat,
    TransactionPost,
)
from ethereum_test_fixtures import (
    BaseFixture,
    FixtureFormat,
    LabeledFixtureFormat,
    StateFixture,
)
from ethereum_test_fixtures.common import FixtureBlobSchedule
from ethereum_test_fixtures.state import (
    FixtureConfig,
    FixtureEnvironment,
    FixtureForkPost,
    FixtureTransaction,
)
from ethereum_test_forks import Fork
from ethereum_test_types import Alloc, Environment, Transaction

from .base import BaseTest
from .blockchain import Block, BlockchainTest, Header
from .debugging import print_traces
from .helpers import verify_transactions


class StateTest(BaseTest):
    """Filler type that tests transactions over the period of a single block."""

    env: Environment = Field(default_factory=Environment)
    pre: Alloc
    post: Alloc
    tx: Transaction
    block_exception: (
        List[TransactionException | BlockException] | TransactionException | BlockException | None
    ) = None
    engine_api_error_code: Optional[EngineAPIError] = None
    blockchain_test_header_verify: Optional[Header] = None
    blockchain_test_rlp_modifier: Optional[Header] = None
    chain_id: int = 1

    supported_fixture_formats: ClassVar[Sequence[FixtureFormat | LabeledFixtureFormat]] = [
        StateFixture,
    ] + [
        LabeledFixtureFormat(
            fixture_format,
            f"{fixture_format.format_name}_from_state_test",
            f"A {fixture_format.format_name} generated from a state_test",
        )
        for fixture_format in BlockchainTest.supported_fixture_formats
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

    @classmethod
    def discard_fixture_format_by_marks(
        cls,
        fixture_format: FixtureFormat,
        fork: Fork,
        markers: List[pytest.Mark],
    ) -> bool:
        """Discard a fixture format from filling if the appropriate marker is used."""
        if "state_test_only" in [m.name for m in markers]:
            return fixture_format != StateFixture
        return False

    def _generate_blockchain_genesis_environment(self, *, fork: Fork) -> Environment:
        """Generate the genesis environment for the BlockchainTest formatted test."""
        assert self.env.number >= 1, (
            "genesis block number cannot be negative, set state test env.number to 1"
        )

        # Modify values to the proper values for the genesis block
        # TODO: All of this can be moved to a new method in `Fork`
        updated_values: Dict[str, Any] = {
            "withdrawals": None,
            "parent_beacon_block_root": None,
            "number": self.env.number - 1,
        }
        if self.env.excess_blob_gas:
            # The excess blob gas environment value means the value of the context (block header)
            # where the transaction is executed. In a blockchain test, we need to indirectly
            # set the excess blob gas by setting the excess blob gas of the genesis block
            # to the expected value plus the TARGET_BLOB_GAS_PER_BLOCK, which is the value
            # that will be subtracted from the excess blob gas when the first block is mined.
            updated_values["excess_blob_gas"] = self.env.excess_blob_gas + (
                fork.target_blobs_per_block() * fork.blob_gas_per_blob()
            )
        if self.env.base_fee_per_gas:
            # Calculate genesis base fee per gas from state test's block#1 env
            updated_values["base_fee_per_gas"] = HexNumber(
                int(int(str(self.env.base_fee_per_gas), 0) * 8 / 7)
            )
        if fork.header_prev_randao_required():
            # Set current random
            updated_values["difficulty"] = None
            updated_values["prev_randao"] = (
                self.env.prev_randao if self.env.prev_randao is not None else self.env.difficulty
            )

        return self.env.copy(**updated_values)

    def _generate_blockchain_blocks(self, *, fork: Fork) -> List[Block]:
        """Generate the single block that represents this state test in a BlockchainTest format."""
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
        }
        if not fork.header_prev_randao_required():
            kwargs["difficulty"] = self.env.difficulty
        if "block_exception" in self.model_fields_set:
            kwargs["exception"] = self.block_exception  # type: ignore
        elif "error" in self.tx.model_fields_set:
            kwargs["exception"] = self.tx.error  # type: ignore
        return [Block(**kwargs)]

    def generate_blockchain_test(self, *, fork: Fork) -> BlockchainTest:
        """Generate a BlockchainTest fixture from this StateTest fixture."""
        return BlockchainTest.from_test(
            base_test=self,
            genesis_environment=self._generate_blockchain_genesis_environment(fork=fork),
            pre=self.pre,
            post=self.post,
            blocks=self._generate_blockchain_blocks(fork=fork),
        )

    def make_state_test_fixture(
        self,
        t8n: TransitionTool,
        fork: Fork,
    ) -> StateFixture:
        """Create a fixture from the state test definition."""
        # We can't generate a state test fixture that names a transition fork,
        # so we get the fork at the block number and timestamp of the state test
        fork = fork.fork_at(self.env.number, self.env.timestamp)

        env = self.env.set_fork_requirements(fork)
        tx = self.tx.with_signature_and_sender(keep_secret_key=True)
        if not self.is_tx_gas_heavy_test() and tx.gas_limit >= Environment().gas_limit:
            warnings.warn(
                f"{self.node_id()} uses a high Transaction gas_limit: {tx.gas_limit}",
                stacklevel=2,
            )
        pre_alloc = Alloc.merge(
            Alloc.model_validate(fork.pre_allocation()),
            self.pre,
        )
        if empty_accounts := pre_alloc.empty_accounts():
            raise Exception(f"Empty accounts in pre state: {empty_accounts}")

        transition_tool_output = t8n.evaluate(
            alloc=pre_alloc,
            txs=[tx],
            env=env,
            fork=fork,
            chain_id=self.chain_id,
            reward=0,  # Reward on state tests is always zero
            blob_schedule=fork.blob_schedule(),
            debug_output_path=self.get_next_transition_tool_output_path(),
            state_test=True,
            slow_request=self.is_tx_gas_heavy_test(),
        )

        try:
            self.post.verify_post_alloc(transition_tool_output.alloc)
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
            pprint(transition_tool_output.alloc)
            raise e

        return StateFixture(
            env=FixtureEnvironment(**env.model_dump(exclude_none=True)),
            pre=pre_alloc,
            post={
                fork: [
                    FixtureForkPost(
                        state_root=transition_tool_output.result.state_root,
                        logs_hash=transition_tool_output.result.logs_hash,
                        tx_bytes=tx.rlp(),
                        expect_exception=tx.error,
                        state=transition_tool_output.alloc,
                    )
                ]
            },
            transaction=FixtureTransaction.from_transaction(tx),
            config=FixtureConfig(
                blob_schedule=FixtureBlobSchedule.from_blob_schedule(fork.blob_schedule()),
                chain_id=self.chain_id,
            ),
        )

    def generate(
        self,
        t8n: TransitionTool,
        fork: Fork,
        fixture_format: FixtureFormat,
    ) -> BaseFixture:
        """Generate the BlockchainTest fixture."""
        self.check_exception_test(exception=self.tx.error is not None)
        if fixture_format in BlockchainTest.supported_fixture_formats:
            return self.generate_blockchain_test(fork=fork).generate(
                t8n=t8n, fork=fork, fixture_format=fixture_format
            )
        elif fixture_format == StateFixture:
            return self.make_state_test_fixture(t8n, fork)

        raise Exception(f"Unknown fixture format: {fixture_format}")

    def execute(
        self,
        *,
        fork: Fork,
        execute_format: ExecuteFormat,
    ) -> BaseExecute:
        """Generate the list of test fixtures."""
        if execute_format == TransactionPost:
            return TransactionPost(
                blocks=[[self.tx]],
                post=self.post,
            )
        raise Exception(f"Unsupported execute format: {execute_format}")


StateTestSpec = Callable[[str], Generator[StateTest, None, None]]
StateTestFiller = Type[StateTest]
