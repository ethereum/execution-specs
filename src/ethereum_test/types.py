"""
Useful types for generating Ethereum tests.
"""
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple, Type, Union

from .code import Code, code_to_hex
from .common import AddrAA, TestPrivateKey


class Storage:
    """
    Definition of a storage in pre or post state of a test
    """

    data: Dict[int, int]

    @staticmethod
    def parse_key_value(input: Union[str, int]) -> int:
        """
        Parses a key or value to a valid int key for storage.
        """
        if type(input) is str:
            if input.startswith("0x"):
                return int(input, 16)
            else:
                return int(input)
        elif type(input) is int:
            return input

        raise Exception("invalid type for key/value of storage")

    @staticmethod
    def key_value_to_string(value: int) -> str:
        """
        Transforms a key or value into a 32-byte hex string.
        """
        return "0x" + value.to_bytes(32, "big").hex()

    def __init__(self, input: Dict[Union[str, int], Union[str, int]]):
        """
        Initializes the storage using a given mapping which can have
        keys and values either as string or int.
        Strings must be valid decimal or hexadecimal (starting with 0x)
        numbers.
        """
        self.data = {}
        for k in input:
            v = Storage.parse_key_value(input[k])
            k = Storage.parse_key_value(k)
            self.data[k] = v
        pass

    def __len__(self) -> int:
        """Returns number of elements in the storage"""
        return len(self.data)

    def __contains__(self, key: Union[str, int]) -> bool:
        """Checks for an item in the storage"""
        key = Storage.parse_key_value(key)
        return key in self.data

    def __getitem__(self, key: Union[str, int]) -> int:
        """Returns an item from the storage"""
        key = Storage.parse_key_value(key)
        if key not in self.data:
            raise KeyError()
        return self.data[key]

    def __setitem__(
        self, key: Union[str, int], value: Union[str, int]  # noqa: SC200
    ):
        """Sets an item in the storage"""
        self.data[Storage.parse_key_value(key)] = Storage.parse_key_value(
            value
        )

    def __delitem__(self, key: Union[str, int]):
        """Deletes an item from the storage"""
        del self.data[Storage.parse_key_value(key)]

    def to_dict(self) -> Mapping[str, str]:
        """
        Converts the storage into a string dict with appropriate 32-byte
        hex string formatting.
        """
        res = {}
        for k in self.data:
            res[Storage.key_value_to_string(k)] = Storage.key_value_to_string(
                self.data[k]
            )
        return res

    def contains(self, other: "Storage") -> bool:
        """
        Returns True if self contains all keys with equal value as
        contained by second storage.
        Used for comparison with test expected post state and alloc returned
        by the transition tool.
        """
        for k in other.data:
            if k not in self.data:
                return False
            if self.data[k] != other.data[k]:
                return False
        return True

    def must_contain(self, other: "Storage"):
        """
        Succeeds only if self contains all keys with equal value as
        contained by second storage.
        Used for comparison with test expected post state and alloc returned
        by the transition tool.
        Raises detailed exception when a difference is found.
        """
        for k in other.data:
            if k not in self.data:
                raise Exception(
                    "key {0} not found in storage".format(
                        Storage.key_value_to_string(k)
                    )
                )
            if self.data[k] != other.data[k]:
                raise Exception(
                    "incorrect value for key {0}: {1}!={2}".format(
                        Storage.key_value_to_string(k),
                        Storage.key_value_to_string(self.data[k]),
                        Storage.key_value_to_string(other.data[k]),
                    )
                )


@dataclass
class Account:
    """
    State associated with an address.
    """

    nonce: Optional[int] = None
    balance: Optional[int] = None
    code: Optional[Union[bytes, str, Code]] = None
    storage: Optional[
        Union[Storage, Dict[Union[str, int], Union[str, int]]]
    ] = None

    def __post_init__(self) -> None:
        """Automatically init account members"""
        if self.storage is not None and type(self.storage) is dict:
            self.storage = Storage(self.storage)

    def check_alloc(self: "Account", account: str, alloc: dict):
        """
        Checks the returned alloc against an expected account in post state.
        Raises exception on failure.
        """
        if self.nonce is not None:
            if "nonce" not in alloc:
                raise Exception(f"nonce not found for account {account}")
            nonce = int(alloc["nonce"], 16)
            if self.nonce != nonce:
                raise Exception(
                    f"unexpected nonce value found for account {account}: "
                    + f"{nonce}, expected {self.nonce}"
                )
        if self.balance is not None:
            if "balance" not in alloc:
                raise Exception(f"balance not found for account {account}")
            balance = int(alloc["balance"], 16)
            if self.balance != balance:
                raise Exception(
                    f"unexpected balance value found for account {account}: "
                    + f"{balance}, expected {self.balance}"
                )
        if self.code is not None:
            if "code" not in alloc:
                raise Exception(f"code not found for account {account}")
            expected_code = code_to_hex(self.code)
            if expected_code != alloc["code"]:
                actual_code = alloc["code"]
                raise Exception(
                    f"unexpected code found for account {account}: "
                    + f"{actual_code}, expected {expected_code}"
                )
        if self.storage is not None:
            if "storage" not in alloc:
                raise Exception(f"storage not found for account {account}")
            assert type(self.storage) is Storage
            Storage(alloc["storage"]).must_contain(self.storage)

    @classmethod
    def with_code(cls: Type, code: Union[bytes, str, Code]) -> "Account":
        """
        Create account with provided `code` and nonce of `1`.
        """
        return Account(nonce=1, code=code)


ACCOUNT_DEFAULTS = Account(nonce=0, balance=0, code=bytes(), storage={})


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
    data: Union[bytes, str, Code] = bytes()
    gas_limit: int = 21000
    access_list: Optional[List[Tuple[str, List[str]]]] = None

    gas_price: Optional[int] = None
    max_fee_per_gas: Optional[int] = None
    max_priority_fee_per_gas: Optional[int] = None

    signature: Optional[Tuple[str, str, str]] = None
    secret_key: Optional[str] = None
    protected: bool = True
    error: Optional[str] = None

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
    hash: Optional[str] = None

    def to_geth_dict(self) -> Mapping[str, Any]:
        """
        Outputs a dict that can be marshalled to JSON and ingested by geth.
        """
        header = {
            "parentHash": self.parent_hash,
            "sha3Uncles": self.ommers_hash,
            "miner": self.coinbase,
            "stateRoot": self.state_root,
            "transactionsRoot": self.transactions_root,
            "receiptsRoot": self.receipt_root,
            "logsBloom": self.bloom,
            "difficulty": hex(self.difficulty),
            "number": hex(self.number),
            "gasLimit": hex(self.gas_limit),
            "gasUsed": hex(self.gas_used),
            "timestamp": hex(self.timestamp),
            "extraData": self.extra_data
            if len(self.extra_data) != 0
            else "0x",  # noqa: E501
            "mixHash": self.mix_digest,
            "nonce": self.nonce,
        }
        if self.base_fee is not None:
            header["baseFeePerGas"] = hex(self.base_fee)
        return header


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
    post_state: Optional[Mapping[str, Account]]
    seal_engine: str


class JSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for `ethereum_test` types.
    """

    def default(self, obj):
        """
        Enocdes types defined in this module using basic python facilities.
        """
        if isinstance(obj, Storage):
            return obj.to_dict()
        elif isinstance(obj, Account):
            account = {
                "nonce": (
                    hex(obj.nonce)
                    if obj.nonce is not None
                    else hex(ACCOUNT_DEFAULTS.nonce)
                ),
                "balance": (
                    hex(obj.balance)
                    if obj.balance is not None
                    else hex(ACCOUNT_DEFAULTS.balance)
                ),
                "code": code_to_hex(obj.code),
                "storage": json.loads(json.dumps(obj.storage, cls=JSONEncoder))
                if obj.storage is not None
                else {},
            }
            return account
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
                "input": code_to_hex(obj.data),
                "to": obj.to,
                "accessList": obj.access_list,
                "protected": obj.protected,
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
                "extraData": obj.extra_data
                if len(obj.extra_data) != 0
                else "0x",  # noqa: E501
                "mixHash": obj.mix_digest,
                "nonce": obj.nonce,
            }
            if obj.base_fee is not None:
                header["baseFeePerGas"] = hex(obj.base_fee)
            if obj.hash is not None:
                header["hash"] = obj.hash
            return header
        elif isinstance(obj, Fixture):
            f = {
                "_info": {},
                "blocks": list(map(lambda x: {"rlp": x}, obj.blocks)),
                "genesisBlockHeader": self.default(obj.genesis),
                "lastblockhash": obj.head,
                "network": obj.fork,
                "pre": json.loads(json.dumps(obj.pre_state, cls=JSONEncoder)),
                "postState": json.loads(
                    json.dumps(obj.post_state, cls=JSONEncoder)
                ),
                "sealEngine": obj.seal_engine,
            }
            if f["postState"] is None:
                del f["postState"]
            return f
        else:
            return super().default(obj)
