"""
Filler object definitions.
"""
import json

from dataclasses import dataclass
from typing import Callable, List, Mapping, Tuple

from ethereum.base_types import Bytes8, Bytes32, Uint
from ethereum.crypto import Hash32
from ethereum.frontier.eth_types import Address, Bloom, Header
from ethereum.utils.hexadecimal import hex_to_hash

from evm_transition_tool import TransitionTool
from evm_block_builder import BlockBuilder

from .common import EmptyTrieRoot
from .types import (
    Account,
    Environment,
    Fixture,
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
        self,
        t8n: TransitionTool,
    ) -> Header:
        """
        Create a genesis block from the state test definition.
        """
        print("making genesis")
        genesis = Header(
            parent_hash=hex_to_hash(
                "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
            ),
            ommers_hash=hex_to_hash(
                "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"  # noqa: E501
            ),
            coinbase=self.env.coinbase,
            state_root=t8n.calc_state_root(
                json.loads(json.dumps(self.pre, cls=JSONEncoder))
            ),
            transactions_root=EmptyTrieRoot,
            receipt_root=EmptyTrieRoot,
            bloom=Bloom(bytearray(256)),
            difficulty=self.env.difficulty,
            number=self.env.number,
            # TODO: following block will have invalid gas limit after 1559
            gas_limit=self.env.gas_limit,
            gas_used=Uint(0),
            timestamp=self.env.timestamp,
            extra_data=bytearray(),
            mix_digest=Bytes32(bytearray(32)),
            nonce=Bytes8(bytearray(8)),
        )

        return genesis

    def make_block(
        self,
        b11r: BlockBuilder,
        t8n: TransitionTool,
    ) -> Tuple[str, Hash32]:
        """
        Create a block from the state test definition.
        """
        pre = json.loads(json.dumps(self.pre, cls=JSONEncoder))
        txs = json.loads(json.dumps(self.txs, cls=JSONEncoder))
        env = json.loads(json.dumps(self.env, cls=JSONEncoder))

        (_, result) = t8n.evaluate(pre, txs, env)
        header = result | {
            "parentHash": self.env.previous,
            "miner": self.env.coinbase,
            "transactionsRoot": result.get("txRoot"),
            "receiptsRoot": result.get("receiptRoot"),
            "difficulty": self.env.difficulty,
            "number": self.env.number,
            "gasLimit": self.env.gas_limit,
            "timestamp": self.env.timestamp,
            "baseFeePerGas": self.env.base_fee,
        }

        return b11r.build(header, self.txs, [], None)


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


def test_only(fork: str) -> Callable[[Callable[[], StateTest], str], Fixture]:
    """
    Decorator that takes a test generator and fills it only for the specified
    fork.
    """

    def inner(fn: Callable[[], StateTest], engine: str) -> Fixture:
        return fill_fixture(fn(), fork, engine)

    return inner


def fill_fixture(test: StateTest, fork: str, engine: str) -> Fixture:
    """
    Fills a fixture for a certain fork.
    """
    b11r = BlockBuilder()
    t8n = TransitionTool()

    genesis = test.make_genesis(t8n)
    (block, head) = test.make_block(b11r, t8n)

    return Fixture(
        blocks=[block],
        genesis=genesis,
        head=head,
        fork=fork,
        preState=test.pre,
        sealEngine=engine,
    )
