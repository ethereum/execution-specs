from dataclasses import dataclass
from typing import Callable, List, Mapping

from ethereum.crypto import Hash32
from ethereum.frontier.eth_types import (
    Account,
    Address,
    Block,
    Bloom,
    Header,
    Root,
)
from ethereum.utils.hexadecimal import hex_to_bytes, hex_to_bytes8, hex_to_hash

from .fork import Fork
from .types import Block, Environment, Fixture, Transaction


@dataclass
class StateTest:
    env: Environment
    pre: Mapping[Address, Account]
    post: Mapping[Address, Account]
    txs: List[Transaction]

    def make_genesis(
        self,
    ) -> Block:
        header = Header(
            parent_hash=self.env.previous,
            ommers_hash=hex_to_hash(
                "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"
            ),
            coinbase=self.env.coinbase,
            state_root=Root(hex_to_hash("0x00")),
            transactions_root=Root(
                hex_to_hash(
                    "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
                )
            ),
            receipt_root=Root(
                hex_to_hash(
                    "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
                )
            ),
            bloom=Bloom(
                hex_to_bytes(
                    "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                )
            ),
            difficulty=self.env.difficulty,
            number=self.env.number,
            # TODO: following block will have invalid gas limit after 1559
            gas_limit=self.env.gas_limit,
            gas_used=0,
            timestamp=self.env.timestamp,
            extra_data=bytearray(),
            mix_digest=hex_to_hash(
                "0x0000000000000000000000000000000000000000000000000000000000000000"
            ),
            nonce=hex_to_bytes8("0x0000000000000000"),
        )

        return Block(header, [], [])


def test_from(fork: str) -> Callable[[Callable[[], StateTest]], Fixture]:
    def inner(func: Callable[[], StateTest]) -> Fixture:
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
    def inner(func: Callable[[], StateTest]) -> Fixture:
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
