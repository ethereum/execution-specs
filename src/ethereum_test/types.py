"""
Useful types for generating Ethereum tests.
"""

from dataclasses import dataclass
from typing import List, Mapping, Optional, Tuple, Type

from ethereum.base_types import U256, Bytes, Uint
from ethereum.crypto import Hash32
from ethereum.frontier.eth_types import Address, Block
from ethereum.frontier.utils.hexadecimal import hex_to_address
from ethereum.utils.hexadecimal import hex_to_hash

from .code import Code
from .common import AddrAA, Big0, Big1, TestPrivateKey
from .fork import Fork


@dataclass
class Account:
    """
    State associated with an address.
    """

    nonce: U256
    balance: U256
    code: Code
    storage: Mapping[U256, U256]

    @classmethod
    def with_code(cls: Type, code: Code) -> "Account":
        """
        Create account with provided `code` and nonce of `1`.
        """
        return Account(nonce=Big1, balance=Big0, code=code, storage={})


@dataclass
class Environment:
    """
    Context in which a test will be executed.
    """

    coinbase: Address = hex_to_address(
        "2adc25665018aa1fe0e6bc666dac8fc2697ff9ba"
    )
    difficulty: Uint = Uint(0x20000)
    gas_limit: Uint = Uint(10000000)
    number: Uint = Uint(1)
    timestamp: U256 = U256(1000)
    previous: Hash32 = hex_to_hash(
        "5e20a0453cecd065ea59c37ac63e079ee08998b6045136a8ce6635c7912ec0b6"
    )
    base_fee: Optional[U256] = None


@dataclass
class Transaction:
    """
    Generic object that can represent all Ethereum transaction types.
    """

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
        """
        Ensures the transaction has no conflicting properties.
        """
        if (
            self.gas_price is not None
            and self.max_fee_per_gas is not None
            and self.max_priority_fee_per_gas is not None
        ):
            raise Exception(
                "only one type of fee payment field can be used in a single tx"
            )

        if (
            self.gas_price is None
            and self.max_fee_per_gas is None
            and self.max_priority_fee_per_gas is None
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
