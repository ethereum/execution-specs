"""
Ethereum state test spec definition and filler.
"""

from typing import Any, Callable, ClassVar, Dict, Generator, List, Optional, Type

from ethereum_test_exceptions import EngineAPIError
from ethereum_test_fixtures import BaseFixture, FixtureFormats
from ethereum_test_fixtures.state import (
    Fixture,
    FixtureEnvironment,
    FixtureForkPost,
    FixtureTransaction,
)
from ethereum_test_forks import Fork
from ethereum_test_types import Alloc, Environment, Transaction
from evm_transition_tool import TransitionTool

from .base import BaseTest
from .blockchain import Block, BlockchainTest, Header
from .debugging import print_traces

TARGET_BLOB_GAS_PER_BLOCK = 393216


class StateTest(BaseTest):
    """
    Filler type that tests transactions over the period of a single block.
    """

    env: Environment
    pre: Alloc
    post: Alloc
    tx: Transaction
    engine_api_error_code: Optional[EngineAPIError] = None
    blockchain_test_header_verify: Optional[Header] = None
    blockchain_test_rlp_modifier: Optional[Header] = None
    chain_id: int = 1

    supported_fixture_formats: ClassVar[List[FixtureFormats]] = [
        FixtureFormats.BLOCKCHAIN_TEST,
        FixtureFormats.BLOCKCHAIN_TEST_ENGINE,
        FixtureFormats.STATE_TEST,
    ]

    def _generate_blockchain_genesis_environment(self) -> Environment:
        """
        Generate the genesis environment for the BlockchainTest formatted test.
        """
        assert (
            self.env.number >= 1
        ), "genesis block number cannot be negative, set state test env.number to 1"

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
            updated_values["excess_blob_gas"] = (
                self.env.excess_blob_gas + TARGET_BLOB_GAS_PER_BLOCK
            )

        return self.env.copy(**updated_values)

    def _generate_blockchain_blocks(self) -> List[Block]:
        """
        Generate the single block that represents this state test in a BlockchainTest format.
        """
        return [
            Block(
                number=self.env.number,
                timestamp=self.env.timestamp,
                fee_recipient=self.env.fee_recipient,
                difficulty=self.env.difficulty,
                gas_limit=self.env.gas_limit,
                extra_data=self.env.extra_data,
                withdrawals=self.env.withdrawals,
                parent_beacon_block_root=self.env.parent_beacon_block_root,
                txs=[self.tx],
                ommers=[],
                exception=self.tx.error,
                header_verify=self.blockchain_test_header_verify,
                rlp_modifier=self.blockchain_test_rlp_modifier,
            )
        ]

    def generate_blockchain_test(self) -> BlockchainTest:
        """
        Generate a BlockchainTest fixture from this StateTest fixture.
        """
        return BlockchainTest(
            genesis_environment=self._generate_blockchain_genesis_environment(),
            pre=self.pre,
            post=self.post,
            blocks=self._generate_blockchain_blocks(),
            t8n_dump_dir=self.t8n_dump_dir,
        )

    def make_state_test_fixture(
        self,
        t8n: TransitionTool,
        fork: Fork,
        eips: Optional[List[int]] = None,
    ) -> Fixture:
        """
        Create a fixture from the state test definition.
        """
        # We can't generate a state test fixture that names a transition fork,
        # so we get the fork at the block number and timestamp of the state test
        fork = fork.fork_at(self.env.number, self.env.timestamp)

        env = self.env.set_fork_requirements(fork)
        tx = self.tx.with_signature_and_sender(keep_secret_key=True)
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
            eips=eips,
            debug_output_path=self.get_next_transition_tool_output_path(),
        )

        try:
            self.post.verify_post_alloc(transition_tool_output.alloc)
        except Exception as e:
            print_traces(t8n.get_traces())
            raise e

        return Fixture(
            env=FixtureEnvironment(**env.model_dump(exclude_none=True)),
            pre=pre_alloc,
            post={
                fork.blockchain_test_network_name(): [
                    FixtureForkPost(
                        state_root=transition_tool_output.result.state_root,
                        logs_hash=transition_tool_output.result.logs_hash,
                        tx_bytes=tx.rlp,
                        expect_exception=tx.error,
                    )
                ]
            },
            transaction=FixtureTransaction.from_transaction(tx),
        )

    def generate(
        self,
        t8n: TransitionTool,
        fork: Fork,
        fixture_format: FixtureFormats,
        eips: Optional[List[int]] = None,
    ) -> BaseFixture:
        """
        Generate the BlockchainTest fixture.
        """
        if fixture_format in BlockchainTest.supported_fixture_formats:
            return self.generate_blockchain_test().generate(
                t8n=t8n, fork=fork, fixture_format=fixture_format, eips=eips
            )
        elif fixture_format == FixtureFormats.STATE_TEST:
            return self.make_state_test_fixture(t8n, fork, eips)

        raise Exception(f"Unknown fixture format: {fixture_format}")


class StateTestOnly(StateTest):
    """
    StateTest filler that only generates a state test fixture.
    """

    supported_fixture_formats: ClassVar[List[FixtureFormats]] = [FixtureFormats.STATE_TEST]


StateTestSpec = Callable[[str], Generator[StateTest, None, None]]
StateTestFiller = Type[StateTest]
