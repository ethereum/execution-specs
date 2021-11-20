"""
Useful types for generating Ethereum tests.
"""
import json

from dataclasses import dataclass
from typing import List, Mapping, Optional, Tuple, Type

from ethereum.crypto import Hash32

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
    extra_data: str = "0x"
    base_fee: Optional[int] = None


@dataclass
class Transaction:
    """
    Generic object that can represent all Ethereum transaction types.
    """

    ty: int
    chain_id: int = 1
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
    protected: bool = True

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
class Header:
    """
    Ethereum header object.
    """

    parent_hash: str
    ommers_hash: str
    coinbase: str
    state_root: str
    transactions_root: str
    receipt_root: str
    bloom: str
    difficulty: int
    number: int
    gas_limit: int
    gas_used: int
    timestamp: int
    extra_data: str
    mix_digest: str
    nonce: str
    base_fee: Optional[int]


@dataclass
class Fixture:
    """
    Cross-client compatible Ethereum test fixture.
    """

    blocks: List[str]
    genesis: Header
    head: str
    fork: str
    pre_state: Mapping[str, Account]
    seal_engine: str


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
                "nonce": hex(obj.nonce),
                "balance": hex(obj.balance),
                "code": obj.code if len(obj.code) != 0 else "0x",
                "storage": obj.storage if obj.storage is not None else {},
            }
        elif isinstance(obj, Transaction):
            tx = {
                "type": hex(obj.ty),
                "chainId": hex(obj.chain_id),
                "nonce": hex(obj.nonce),
                "gasPrice": None,
                "maxPriorityFeePerGas": None,
                "maxFeePerGas": None,
                "gas": hex(obj.gas_limit),
                "value": hex(obj.value),
                "input": obj.data,
                "to": obj.to,
                "accessList": obj.access_list,
                "protected": obj.protected
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
        elif isinstance(obj, Header):
            header = {
                "parentHash": obj.parent_hash,
                "uncleHash": obj.ommers_hash,
                "coinbase": obj.coinbase,
                "stateRoot": obj.state_root,
                "transactionsTrie": obj.transactions_root,
                "receiptTrie": obj.receipt_root,
                "bloom": obj.bloom,
                "difficulty": hex(obj.difficulty),
                "number": hex(obj.number),
                "gasLimit": hex(obj.gas_limit),
                "gasUsed": hex(obj.gas_used),
                "timestamp": hex(obj.timestamp),
                "extraData": obj.extra_data if len(obj.extra_data) != 0 else "0x",  # noqa: E501
                "mixHash": obj.mix_digest,
                "nonce": obj.nonce,
            }
            if obj.base_fee is not None:
                header["baseFeePerGas"] = hex(obj.base_fee)
            return header
        elif isinstance(obj, Fixture):
            return {
                "_info": {},
                "blocks": list(map(lambda x: {"rlp": x}, obj.blocks)),
                "genesisBlockHeader": self.default(obj.genesis),
                "lastblockhash": obj.head,
                "network": obj.fork,
                "pre": json.loads(json.dumps(obj.pre_state, cls=JSONEncoder)),
                "sealEngine": obj.seal_engine,
            }
        else:
            return super().default(obj)
