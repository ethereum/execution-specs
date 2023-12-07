"""
Ethereum state test spec definition and filler.
"""
from copy import copy
from dataclasses import dataclass
from typing import Callable, Generator, List, Mapping, Optional, Type

from ethereum_test_forks import Fork
from evm_transition_tool import TransitionTool

from ...common import Environment, Number, Transaction
from ...common.constants import EngineAPIError
from ..base.base_test import BaseFixture, BaseTest
from ..blockchain.blockchain_test import Block, BlockchainTest


@dataclass(kw_only=True)
class StateTest(BaseTest):
    """
    Filler type that tests transactions over the period of a single block.
    """

    env: Environment
    pre: Mapping
    post: Mapping
    txs: List[Transaction]
    engine_api_error_code: Optional[EngineAPIError] = None
    tag: str = ""
    chain_id: int = 1

    @classmethod
    def pytest_parameter_name(cls) -> str:
        """
        Returns the parameter name used to identify this filler in a test.
        """
        return "state_test"

    def _generate_blockchain_genesis_environment(self) -> Environment:
        """
        Generate the genesis environment for the BlockchainTest formatted test.
        """
        genesis_env = copy(self.env)

        # Modify values to the proper values for the genesis block
        genesis_env.withdrawals = None
        genesis_env.beacon_root = None
        genesis_env.number = Number(genesis_env.number) - 1
        assert (
            genesis_env.number >= 0
        ), "genesis block number cannot be negative, set state test env.number to 1"

        return genesis_env

    def _generate_blockchain_blocks(self) -> List[Block]:
        """
        Generate the single block that represents this state test in a BlockchainTest format.
        """
        return [
            Block(
                number=self.env.number,
                timestamp=self.env.timestamp,
                coinbase=self.env.coinbase,
                difficulty=self.env.difficulty,
                gas_limit=self.env.gas_limit,
                extra_data=self.env.extra_data,
                withdrawals=self.env.withdrawals,
                beacon_root=self.env.beacon_root,
                txs=self.txs,
                ommers=[],
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
            base_test_config=self.base_test_config,
        )

    def generate(
        self,
        t8n: TransitionTool,
        fork: Fork,
        eips: Optional[List[int]] = None,
    ) -> Optional[BaseFixture]:
        """
        Generate the BlockchainTest fixture.
        """
        t8n.reset_traces()
        if self.base_test_config.state_test:
            raise Exception("StateTest format is not yet implemented!")
        else:
            return self.generate_blockchain_test().generate(t8n, fork, eips)


StateTestSpec = Callable[[str], Generator[StateTest, None, None]]
StateTestFiller = Type[StateTest]
