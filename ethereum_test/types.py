from dataclasses import dataclass
from typing import List, Mapping, Optional, Tuple, Type
from ethereum.base_types import Bytes, Bytes20, U256, Uint
from ethereum.crypto import Hash32
from ethereum.utils.hexadecimal import hex_to_hash
from ethereum.frontier.eth_types import Address, Account, Block, Header, Root
from ethereum.frontier.utils.hexadecimal import hex_to_address

from .code import Code
from .common import AddrAA, Big0, Big1, TestPrivateKey
from .fork import Fork

Address = Bytes20

@dataclass
class Account():
    nonce: U256
    balance: U256
    code: Code
    storage: Mapping[U256, U256]

    @classmethod
    def with_code(cls: Type, code: Code) -> "Account":
        return Account(nonce=Big1, balance=Big0, code=code, storage={})


@dataclass
class Environment():
    coinbase: Address = hex_to_address("2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    difficulty: Uint = Uint(0x20000)
    gas_limit: Uint = Uint(10000000)
    number: Uint = Uint(1)
    timestamp: Uint = Uint(1000)
    previous: Hash32 = hex_to_hash("5e20a0453cecd065ea59c37ac63e079ee08998b6045136a8ce6635c7912ec0b6")
    base_fee: Optional[U256] = None


@dataclass
class Transaction():
    nonce: U256 = Big0
    to: Optional[Address] = AddrAA
    value: U256 = Big0
    data: Bytes = bytearray()
    gas_limit: U256 = U256(21000)
    access_list: Optional[List[Tuple[Address, List[U256]]]] = None

    gas_price: Optional[U256] = None
    max_fee_per_gas: Optional[U256] = None
    max_priority_fee_per_gas: Optional[U256] = None

    signature: Optional[Tuple[U256, U256, U256]] = None
    private_key: Optional[str] = None

    def __post_init__(self) -> None:
        if (
            self.gas_price is not None and
            self.max_fee_per_gas is not None and
            self.max_priority_fee_per_gas is not None
        ):
            raise Exception("only one type of fee payment field can be used in a single tx")

        if (
            self.gas_price is None and
            self.max_fee_per_gas is None and
            self.max_priority_fee_per_gas is None
        ):
            self.gas_price = Big0

        if self.signature is not None and self.private_key is not None:
            raise Exception("can't define both 'signature' and 'private_key'")
        
        if self.signature is None and self.private_key is None:
            self.private_key = TestPrivateKey


@dataclass
class Fixture:
    """
    Cross-client compatible Ethereum test fixture.
    """

    blocks: List[Block]
    genesis: Block
    head: Hash32
    fork: Fork
    preState: Mapping[Address, Account]
    postState: Mapping[Address, Account]
    sealEngine: str
