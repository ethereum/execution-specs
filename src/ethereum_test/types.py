"""
Useful types for generating Ethereum tests.
"""
import json

from dataclasses import dataclass
from typing import List, Mapping, Optional, Tuple, Type

from ethereum.crypto import Hash32
from ethereum.frontier.eth_types import Header

from .common import AddrAA, TestPrivateKey


@dataclass
class Account:
    """
    State associated with an address.
    """

    nonce: int = 0
    balance: int = 0
    code: str = ""
    storage: Optional[Mapping[str, str]] = None

    @classmethod
    def with_code(cls: Type, code: str) -> "Account":
        """
        Create account with provided `code` and nonce of `1`.
        """
        return Account(nonce=1, code=code)


@dataclass
class Environment:
    """
    Context in which a test will be executed.
    """

    coinbase: str = "0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba"
    difficulty: int = 0x20000
    gas_limit: int = 10000000
    number: int = 1
    timestamp: int = 1000
    previous: str = "0x5e20a0453cecd065ea59c37ac63e079ee08998b6045136a8ce6635c7912ec0b6"  # noqa: E501
    base_fee: Optional[int] = None


@dataclass
class Transaction:
    """
    Generic object that can represent all Ethereum transaction types.
    """

    ty: int
    nonce: int = 0
    to: Optional[str] = AddrAA
    value: int = 0
    data: str = ""
    gas_limit: int = 21000
    access_list: Optional[List[Tuple[str, List[str]]]] = None

    gas_price: Optional[int] = None
    max_fee_per_gas: Optional[int] = None
    max_priority_fee_per_gas: Optional[int] = None

    signature: Optional[Tuple[str, str, str]] = None
    secret_key: Optional[str] = None

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
            self.gas_price = 0

        if self.signature is not None and self.secret_key is not None:
            raise Exception("can't define both 'signature' and 'private_key'")

        if self.signature is None and self.secret_key is None:
            self.secret_key = TestPrivateKey


@dataclass
class Fixture:
    """
    Cross-client compatible Ethereum test fixture.
    """

    blocks: List[str]
    genesis: Header
    head: Hash32
    fork: str
    preState: Mapping[str, Account]
    sealEngine: str


class JSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for `ethereum_test` types.
    """

    def default(self, obj):
        """
        Enocdes types defined in this module using basic python facilities.
        """
        if isinstance(obj, Account):
            return {
                "nonce": str(obj.nonce),
                "balance": str(obj.balance),
                "code": obj.code,
                "storage": obj.storage,
            }
        elif isinstance(obj, Transaction):
            tx = {
                "type": hex(obj.ty),
                "chainId": hex(1),
                "nonce": hex(obj.nonce),
                "gasPrice": None,
                "maxPriorityFeePerGas": None,
                "maxFeePerGas": None,
                "gas": hex(obj.gas_limit),
                "value": hex(obj.value),
                "input": obj.data,
                "to": obj.to,
                "accessList": obj.access_list,
            }

            if obj.signature is None:
                tx["v"] = hex(0x0)
                tx["r"] = hex(0x0)
                tx["s"] = hex(0x0)
            else:
                tx["v"] = obj.signature[0]
                tx["r"] = obj.signature[1]
                tx["s"] = obj.signature[2]

            if obj.gas_price is not None:
                tx["gasPrice"] = hex(obj.gas_price)
            if obj.max_priority_fee_per_gas is not None:
                tx["maxPriorityFeePerGas"] = hex(obj.max_priority_fee_per_gas)
            if obj.max_fee_per_gas is not None:
                tx["maxFeePerGas"] = hex(obj.max_fee_per_gas)
            if obj.secret_key is not None:
                tx["secretKey"] = obj.secret_key

            return tx
        elif isinstance(obj, Environment):
            return {
                "currentCoinbase": obj.coinbase,
                "currentDifficulty": hex(obj.difficulty),
                "parentDifficulty": None,
                "currentGasLimit": str(obj.gas_limit),
                "currentNumber": str(obj.number),
                "currentTimestamp": str(obj.timestamp),
                "parentTimstamp": None,
                "blockHashes": {},
                "ommers": [],
                "currentBaseFee": str(obj.base_fee)
                if obj.base_fee is not None
                else None,
                "parentUncleHash": None,
            }
        else:
            return super().default(obj)
