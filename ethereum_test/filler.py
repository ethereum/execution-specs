"""
Filler object definitions.
"""

from dataclasses import dataclass
from typing import Callable, List, Mapping

from ethereum.base_types import Bytes8, Bytes32, Uint
from ethereum.crypto import Hash32
from ethereum.frontier.eth_types import Address, Block, Bloom, Header, Root
from ethereum.utils.hexadecimal import hex_to_hash

from .fork import Fork
from .types import Account, Environment, Fixture, Transaction


@dataclass
class StateTest:
    """
    Filler type that tests transactions over the period of a single block.
    """

    env: Environment
    pre: Mapping[Address, Account]
    post: Mapping[Address, Account]
    txs: List[Transaction]

    def make_genesis(
        self,
    ) -> Block:
        """
        Create a genesis block from the state test definition.
        """
        header = Header(
            parent_hash=self.env.previous,
            ommers_hash=hex_to_hash(
                "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"  # noqa: E501
            ),
            coinbase=self.env.coinbase,
            state_root=Root(bytearray(32)),
            transactions_root=Root(
                hex_to_hash(
                    "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"  # noqa: E501
                )
            ),
            receipt_root=Root(
                hex_to_hash(
                    "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"  # noqa: E501
                )
            ),
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

        return Block(header, (), ())


def test_from(fork: str) -> Callable[[Callable[[], StateTest]], Fixture]:
    """
    Decorator that takes a test generator and fills it for each for fork after
    the specified fork.
    """

    def inner(fn: Callable[[], StateTest]) -> Fixture:
        return Fixture(
            blocks=[],
            genesis=Block(),
            head=Hash32(),
            fork=Fork.LONDON,
            preState={},
            postState={},
            sealEngine="ethash",
        )

    inner.decorator = test_from
    return inner


def test_only(fork: str) -> Callable[[Callable[[], StateTest]], Fixture]:
    """
    Decorator that takes a test generator and fills it only for the specified
    fork.
    """

    def inner(fn: Callable[[], StateTest]) -> Fixture:
        return Fixture(
            blocks=[],
            genesis=Block(),
            head=Hash32(),
            fork=Fork.LONDON,
            preState={},
            postState={},
            sealEngine="ethash",
        )

    inner.decorator = test_only
    return inner
