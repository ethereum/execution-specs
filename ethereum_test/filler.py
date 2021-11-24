"""
Filler object definitions.
"""
import json
import os
import tempfile

from dataclasses import dataclass
from typing import Callable, List, Mapping, Tuple

from evm_transition_tool import TransitionTool
from evm_block_builder import BlockBuilder

from .common import EmptyTrieRoot
from .types import (
    Account,
    Environment,
    Fixture,
    Header,
    JSONEncoder,
    Transaction,
)


@dataclass
class StateTest:
    """
    Filler type that tests transactions over the period of a single block.
    """

    env: Environment
    pre: Mapping[str, Account]
    post: Mapping[str, Account]
    txs: List[Transaction]

    def make_genesis(
        self, b11r: BlockBuilder, t8n: TransitionTool, fork: str
    ) -> Header:
        """
        Create a genesis block from the state test definition.
        """
        genesis = Header(
            parent_hash="0x0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            ommers_hash="0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",  # noqa: E501
            coinbase=self.env.coinbase,
            state_root=t8n.calc_state_root(
                json.loads(json.dumps(self.pre, cls=JSONEncoder)), fork
            ),
            transactions_root=EmptyTrieRoot,
            receipt_root=EmptyTrieRoot,
            bloom="0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            difficulty=self.env.difficulty,
            number=self.env.number - 1,
            gas_limit=self.env.gas_limit,
            gas_used=0,
            timestamp=0,
            extra_data="0x00",
            mix_digest="0x0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            nonce="0x0000000000000000",
            base_fee=None,
        )

        (_, h) = b11r.build(genesis.to_geth_dict(), "", [])
        genesis.hash = h

        return genesis

    def make_block(
        self,
        b11r: BlockBuilder,
        t8n: TransitionTool,
        fork: str,
        chain_id=1,
        reward=0,
    ) -> Tuple[str, str]:
        """
        Create a block from the state test definition.
        """
        pre = json.loads(json.dumps(self.pre, cls=JSONEncoder))
        txs = json.loads(json.dumps(self.txs, cls=JSONEncoder))
        env = json.loads(json.dumps(self.env, cls=JSONEncoder))

        with tempfile.TemporaryDirectory() as directory:
            txsRlp = os.path.join(directory, "txs.rlp")
            (_, result) = t8n.evaluate(
                pre,
                txs,
                env,
                fork,
                txsPath=txsRlp,
                chain_id=chain_id,
                reward=reward,
            )
            with open(txsRlp, "r") as file:
                txs = file.read().strip('"')

        header = result | {
            "parentHash": self.env.previous,
            "miner": self.env.coinbase,
            "transactionsRoot": result.get("txRoot"),
            "difficulty": hex(self.env.difficulty),
            "number": str(self.env.number),
            "gasLimit": str(self.env.gas_limit),
            "timestamp": str(self.env.timestamp),
            "extraData": self.env.extra_data
            if len(self.env.extra_data) != 0
            else "0x",
        }
        if self.env.base_fee is not None:
            header["baseFeePerGas"] = str(self.env.base_fee)

        return b11r.build(header, txs, [], None)


#  def test_from(
#      fork: str,
#  ) -> Callable[[Callable[[], StateTest]], Callable[[], List[Fixture]]]:
#      """
#      Decorator that takes a test generator and fills it for each for fork after  # noqa
#      the specified fork.
#      """

#      def inner(fn: Callable[[], StateTest]) -> Fixture:
#          return fill_fixture(fork, fn())

#      inner.decorator = test_from
#      return inner


def test_only(
    fork: str,
) -> Callable[[Callable[[], StateTest]], Callable[[str], Fixture]]:
    """
    Decorator that takes a test generator and fills it only for the specified
    fork.
    """
    fork = fork.capitalize()

    def decorator(fn: Callable[[], StateTest]) -> Callable[[str], Fixture]:
        def inner(engine) -> Fixture:
            return fill_fixture(fn(), fork, engine)

        inner.__filler_metadata__ = {
            "fork": fork,
            "name": fn.__name__,
        }

        return inner

    return decorator


def fill_fixture(test: StateTest, fork: str, engine: str) -> Fixture:
    """
    Fills a fixture for a certain fork.
    """
    b11r = BlockBuilder()
    t8n = TransitionTool()

    genesis = test.make_genesis(b11r, t8n, fork)
    (block, head) = test.make_block(
        b11r, t8n, fork, reward=2000000000000000000
    )

    return Fixture(
        blocks=[block],
        genesis=genesis,
        head=head,
        fork=fork,
        pre_state=test.pre,
        seal_engine=engine,
    )
