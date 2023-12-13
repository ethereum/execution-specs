"""
Ethereum state test spec definition and filler.
"""
from copy import copy
from dataclasses import dataclass
from typing import Callable, Generator, List, Mapping, Optional, Type

import pytest

from ethereum_test_forks import Fork
from evm_transition_tool import FixtureFormats, TransitionTool

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

    @classmethod
    def fixture_formats(cls) -> List[FixtureFormats]:
        """
        Returns a list of fixture formats that can be output to the test spec.
        """
        return [
            FixtureFormats.BLOCKCHAIN_TEST,
            FixtureFormats.BLOCKCHAIN_TEST_HIVE,
            FixtureFormats.STATE_TEST,
        ]

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
            fixture_format=self.fixture_format,
        )

    def generate(
        self,
        t8n: TransitionTool,
        fork: Fork,
        eips: Optional[List[int]] = None,
    ) -> BaseFixture:
        """
        Generate the BlockchainTest fixture.
        """
        if self.fixture_format in BlockchainTest.fixture_formats():
            return self.generate_blockchain_test().generate(t8n, fork, eips)
        elif self.fixture_format == FixtureFormats.STATE_TEST:
            # TODO: append fixture in state format
            pytest.skip("StateTest fixture format not implemented.")

        raise Exception(f"Unknown fixture format: {self.fixture_format}")


StateTestSpec = Callable[[str], Generator[StateTest, None, None]]
StateTestFiller = Type[StateTest]
