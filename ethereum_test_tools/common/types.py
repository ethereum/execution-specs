"""
Useful types for generating Ethereum tests.
"""
from copy import copy, deepcopy
from dataclasses import dataclass, fields, replace
from itertools import count
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    SupportsBytes,
    Tuple,
    Type,
    TypeAlias,
    TypeVar,
)

from coincurve.keys import PrivateKey, PublicKey
from ethereum import rlp as eth_rlp
from ethereum.base_types import Uint
from ethereum.crypto.hash import keccak256
from trie import HexaryTrie

from ethereum_test_forks import Fork
from evm_transition_tool import TransitionTool

from ..reference_spec.reference_spec import ReferenceSpec
from .constants import AddrAA, EmptyOmmersRoot, EngineAPIError, TestPrivateKey
from .conversions import (
    BytesConvertible,
    FixedSizeBytesConvertible,
    NumberConvertible,
    int_or_none,
    str_or_none,
    to_bytes,
    to_fixed_size_bytes,
    to_number,
)
from .json import JSONEncoder, SupportsJSON, field, to_json


# Sentinel classes
class Removable:
    """
    Sentinel class to detect if a parameter should be removed.
    (`None` normally means "do not modify")
    """

    pass


class Auto:
    """
    Class to use as a sentinel value for parameters that should be
    automatically calculated.
    """

    def __repr__(self) -> str:
        """Print the correct test id."""
        return "auto"


# Basic Types


N = TypeVar("N", bound="Number")


class Number(int, SupportsJSON):
    """
    Class that helps represent numbers in tests.
    """

    def __new__(cls, input: NumberConvertible | N):
        """
        Creates a new Number object.
        """
        return super(Number, cls).__new__(cls, to_number(input))

    def __str__(self) -> str:
        """
        Returns the string representation of the number.
        """
        return str(int(self))

    def __json__(self, encoder: JSONEncoder) -> str:
        """
        Returns the JSON representation of the number.
        """
        return str(self)

    def hex(self) -> str:
        """
        Returns the hexadecimal representation of the number.
        """
        return hex(self)

    @classmethod
    def or_none(cls: Type[N], input: N | NumberConvertible | None) -> N | None:
        """
        Converts the input to a Number while accepting None.
        """
        if input is None:
            return input
        return cls(input)


class HexNumber(Number):
    """
    Class that helps represent an hexadecimal numbers in tests.
    """

    def __str__(self) -> str:
        """
        Returns the string representation of the number.
        """
        return self.hex()


class ZeroPaddedHexNumber(HexNumber):
    """
    Class that helps represent zero padded hexadecimal numbers in tests.
    """

    def hex(self) -> str:
        """
        Returns the hexadecimal representation of the number.
        """
        if self == 0:
            return "0x00"
        hex_str = hex(self)[2:]
        if len(hex_str) % 2 == 1:
            return "0x0" + hex_str
        return "0x" + hex_str


class Bytes(bytes, SupportsJSON):
    """
    Class that helps represent bytes of variable length in tests.
    """

    def __new__(cls, input: BytesConvertible):
        """
        Creates a new Bytes object.
        """
        return super(Bytes, cls).__new__(cls, to_bytes(input))

    def __str__(self) -> str:
        """
        Returns the hexadecimal representation of the bytes.
        """
        return self.hex()

    def __json__(self, encoder: JSONEncoder) -> str:
        """
        Returns the JSON representation of the bytes.
        """
        return str(self)

    def hex(self, *args, **kwargs) -> str:
        """
        Returns the hexadecimal representation of the bytes.
        """
        return "0x" + super().hex(*args, **kwargs)

    @classmethod
    def or_none(cls, input: "Bytes | BytesConvertible | None") -> "Bytes | None":
        """
        Converts the input to a Bytes while accepting None.
        """
        if input is None:
            return input
        return cls(input)


T = TypeVar("T", bound="FixedSizeBytes")


class FixedSizeBytes(Bytes):
    """
    Class that helps represent bytes of fixed length in tests.
    """

    byte_length: ClassVar[int]

    def __class_getitem__(cls, length: int) -> Type["FixedSizeBytes"]:
        """
        Creates a new FixedSizeBytes class with the given length.
        """

        class Sized(cls):  # type: ignore
            byte_length = length

        return Sized

    def __new__(cls, input: FixedSizeBytesConvertible | T):
        """
        Creates a new FixedSizeBytes object.
        """
        return super(FixedSizeBytes, cls).__new__(cls, to_fixed_size_bytes(input, cls.byte_length))

    @classmethod
    def or_none(cls: Type[T], input: T | FixedSizeBytesConvertible | None) -> T | None:
        """
        Converts the input to a Fixed Size Bytes while accepting None.
        """
        if input is None:
            return input
        return cls(input)


class Address(FixedSizeBytes[20]):  # type: ignore
    """
    Class that helps represent Ethereum addresses in tests.
    """

    pass


class Hash(FixedSizeBytes[32]):  # type: ignore
    """
    Class that helps represent hashes in tests.
    """

    pass


class Bloom(FixedSizeBytes[256]):  # type: ignore
    """
    Class that helps represent blooms in tests.
    """

    pass


class HeaderNonce(FixedSizeBytes[8]):  # type: ignore
    """
    Class that helps represent the header nonce in tests.
    """

    pass


MAX_STORAGE_KEY_VALUE = 2**256 - 1
MIN_STORAGE_KEY_VALUE = -(2**255)


class Storage(SupportsJSON):
    """
    Definition of a storage in pre or post state of a test
    """

    data: Dict[int, int]

    current_slot: Iterator[int]

    StorageDictType: ClassVar[TypeAlias] = Dict[
        str | int | bytes | SupportsBytes, str | int | bytes | SupportsBytes
    ]
    """
    Dictionary type to be used when defining an input to initialize a storage.
    """

    class InvalidType(Exception):
        """
        Invalid type used when describing test's expected storage key or value.
        """

        key_or_value: Any

        def __init__(self, key_or_value: Any, *args):
            super().__init__(args)
            self.key_or_value = key_or_value

        def __str__(self):
            """Print exception string"""
            return f"invalid type for key/value: {self.key_or_value}"

    class InvalidValue(Exception):
        """
        Invalid value used when describing test's expected storage key or
        value.
        """

        key_or_value: Any

        def __init__(self, key_or_value: Any, *args):
            super().__init__(args)
            self.key_or_value = key_or_value

        def __str__(self):
            """Print exception string"""
            return f"invalid value for key/value: {self.key_or_value}"

    class AmbiguousKeyValue(Exception):
        """
        Key is represented twice in the storage.
        """

        key_1: str | int
        val_1: str | int
        key_2: str | int
        val_2: str | int

        def __init__(
            self,
            key_1: str | int,
            val_1: str | int,
            key_2: str | int,
            val_2: str | int,
            *args,
        ):
            super().__init__(args)
            self.key_1 = key_1
            self.val_1 = val_1
            self.key_2 = key_2
            self.val_2 = val_2

        def __str__(self):
            """Print exception string"""
            return f"""
            Key is represented twice (due to negative numbers) with different
            values in storage:
            s[{self.key_1}] = {self.val_1} and s[{self.key_2}] = {self.val_2}
            """

    class MissingKey(Exception):
        """
        Test expected to find a storage key set but key was missing.
        """

        key: int

        def __init__(self, key: int, *args):
            super().__init__(args)
            self.key = key

        def __str__(self):
            """Print exception string"""
            return "key {0} not found in storage".format(Storage.key_value_to_string(self.key))

    class KeyValueMismatch(Exception):
        """
        Test expected a certain value in a storage key but value found
        was different.
        """

        address: str
        key: int
        want: int
        got: int

        def __init__(self, address: str, key: int, want: int, got: int, *args):
            super().__init__(args)
            self.address = address
            self.key = key
            self.want = want
            self.got = got

        def __str__(self):
            """Print exception string"""
            return (
                f"incorrect value in address {self.address} for "
                + f"key {Storage.key_value_to_string(self.key)}:"
                + f" want {Storage.key_value_to_string(self.want)} (dec:{self.want}),"
                + f" got {Storage.key_value_to_string(self.got)} (dec:{self.got})"
            )

    @staticmethod
    def parse_key_value(input: str | int | bytes | SupportsBytes) -> int:
        """
        Parses a key or value to a valid int key for storage.
        """
        if isinstance(input, str):
            input = int(input, 0)
        elif isinstance(input, int):
            pass
        elif isinstance(input, bytes) or isinstance(input, SupportsBytes):
            input = int.from_bytes(bytes(input), "big")
        else:
            raise Storage.InvalidType(input)

        if input > MAX_STORAGE_KEY_VALUE or input < MIN_STORAGE_KEY_VALUE:
            raise Storage.InvalidValue(input)
        return input

    @staticmethod
    def key_value_to_string(value: int) -> str:
        """
        Transforms a key or value into an hex string.
        """
        hex_str = value.to_bytes(32, "big", signed=(value < 0)).hex().lstrip("0")
        if hex_str == "":
            hex_str = "00"
        if len(hex_str) % 2 != 0:
            hex_str = "0" + hex_str
        return "0x" + hex_str

    def __init__(self, input: StorageDictType = {}, start_slot: int = 0):
        """
        Initializes the storage using a given mapping which can have
        keys and values either as string or int.
        Strings must be valid decimal or hexadecimal (starting with 0x)
        numbers.
        """
        self.data = {}
        for key in input:
            value = Storage.parse_key_value(input[key])
            key = Storage.parse_key_value(key)
            self.data[key] = value
        self.current_slot = count(start_slot)

    def __len__(self) -> int:
        """Returns number of elements in the storage"""
        return len(self.data)

    def __contains__(self, key: str | int | bytes) -> bool:
        """Checks for an item in the storage"""
        key = Storage.parse_key_value(key)
        return key in self.data

    def __getitem__(self, key: str | int | bytes) -> int:
        """Returns an item from the storage"""
        key = Storage.parse_key_value(key)
        if key not in self.data:
            raise KeyError()
        return self.data[key]

    def __setitem__(self, key: str | int | bytes, value: str | int | bytes):  # noqa: SC200
        """Sets an item in the storage"""
        self.data[Storage.parse_key_value(key)] = Storage.parse_key_value(value)

    def __delitem__(self, key: str | int | bytes):
        """Deletes an item from the storage"""
        del self.data[Storage.parse_key_value(key)]

    def store_next(self, value: str | int | bytes) -> int:
        """
        Stores a value in the storage and returns the key where the value is stored.

        Increments the key counter so the next time this function is called,
        the next key is used.
        """
        self[slot := next(self.current_slot)] = value
        return slot

    def __json__(self, encoder: JSONEncoder) -> Mapping[str, str]:
        """
        Converts the storage into a string dict with appropriate 32-byte
        hex string formatting.
        """
        res: Dict[str, str] = {}
        for key in self.data:
            key_repr = Storage.key_value_to_string(key)
            val_repr = Storage.key_value_to_string(self.data[key])
            if key_repr in res and val_repr != res[key_repr]:
                raise Storage.AmbiguousKeyValue(key_repr, res[key_repr], key, val_repr)
            res[key_repr] = val_repr
        return res

    def contains(self, other: "Storage") -> bool:
        """
        Returns True if self contains all keys with equal value as
        contained by second storage.
        Used for comparison with test expected post state and alloc returned
        by the transition tool.
        """
        for key in other.data:
            if key not in self.data:
                return False
            if self.data[key] != other.data[key]:
                return False
        return True

    def must_contain(self, address: str, other: "Storage"):
        """
        Succeeds only if self contains all keys with equal value as
        contained by second storage.
        Used for comparison with test expected post state and alloc returned
        by the transition tool.
        Raises detailed exception when a difference is found.
        """
        for key in other.data:
            if key not in self.data:
                # storage[key]==0 is equal to missing storage
                if other[key] != 0:
                    raise Storage.MissingKey(key)
            elif self.data[key] != other.data[key]:
                raise Storage.KeyValueMismatch(address, key, self.data[key], other.data[key])

    def must_be_equal(self, address: str, other: "Storage"):
        """
        Succeeds only if "self" is equal to "other" storage.
        """
        # Test keys contained in both storage objects
        for key in self.data.keys() & other.data.keys():
            if self.data[key] != other.data[key]:
                raise Storage.KeyValueMismatch(address, key, self.data[key], other.data[key])

        # Test keys contained in either one of the storage objects
        for key in self.data.keys() ^ other.data.keys():
            if key in self.data:
                if self.data[key] != 0:
                    raise Storage.KeyValueMismatch(address, key, self.data[key], 0)

            elif other.data[key] != 0:
                raise Storage.KeyValueMismatch(address, key, 0, other.data[key])


@dataclass(kw_only=True)
class Account:
    """
    State associated with an address.
    """

    nonce: Optional[NumberConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="nonce",
            cast_type=ZeroPaddedHexNumber,
            default_value=0,
        ),
    )
    """
    The scalar value equal to a) the number of transactions sent by
    an Externally Owned Account, b) the amount of contracts created by a
    contract.
    """
    balance: Optional[NumberConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="balance",
            cast_type=ZeroPaddedHexNumber,
            default_value=0,
        ),
    )
    """
    The amount of Wei (10<sup>-18</sup> Eth) the account has.
    """
    code: Optional[BytesConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="code",
            cast_type=Bytes,
            default_value=bytes(),
        ),
    )
    """
    Bytecode contained by the account.
    """
    storage: Optional[Storage | Storage.StorageDictType] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="storage",
            cast_type=Storage,
            to_json=True,
            default_value={},
        ),
    )
    """
    Storage within a contract.
    """

    NONEXISTENT: ClassVar[object] = object()
    """
    Sentinel object used to specify when an account should not exist in the
    state.
    """

    class NonceMismatch(Exception):
        """
        Test expected a certain nonce value for an account but a different
        value was found.
        """

        address: str
        want: int | None
        got: int | None

        def __init__(self, address: str, want: int | None, got: int | None, *args):
            super().__init__(args)
            self.address = address
            self.want = want
            self.got = got

        def __str__(self):
            """Print exception string"""
            return (
                f"unexpected nonce for account {self.address}: "
                + f"want {self.want}, got {self.got}"
            )

    class BalanceMismatch(Exception):
        """
        Test expected a certain balance for an account but a different
        value was found.
        """

        address: str
        want: int | None
        got: int | None

        def __init__(self, address: str, want: int | None, got: int | None, *args):
            super().__init__(args)
            self.address = address
            self.want = want
            self.got = got

        def __str__(self):
            """Print exception string"""
            return (
                f"unexpected balance for account {self.address}: "
                + f"want {self.want}, got {self.got}"
            )

    class CodeMismatch(Exception):
        """
        Test expected a certain bytecode for an account but a different
        one was found.
        """

        address: str
        want: str | None
        got: str | None

        def __init__(self, address: str, want: str | None, got: str | None, *args):
            super().__init__(args)
            self.address = address
            self.want = want
            self.got = got

        def __str__(self):
            """Print exception string"""
            return (
                f"unexpected code for account {self.address}: "
                + f"want {self.want}, got {self.got}"
            )

    def check_alloc(self: "Account", address: str, alloc: dict):
        """
        Checks the returned alloc against an expected account in post state.
        Raises exception on failure.
        """
        if self.nonce is not None:
            actual_nonce = int_or_none(alloc.get("nonce"), 0)
            nonce = int(Number(self.nonce))
            if nonce != actual_nonce:
                raise Account.NonceMismatch(
                    address=address,
                    want=nonce,
                    got=actual_nonce,
                )

        if self.balance is not None:
            actual_balance = int_or_none(alloc.get("balance"), 0)
            balance = int(Number(self.balance))
            if balance != actual_balance:
                raise Account.BalanceMismatch(
                    address=address,
                    want=balance,
                    got=actual_balance,
                )

        if self.code is not None:
            expected_code = Bytes(self.code).hex()
            actual_code = str_or_none(alloc.get("code"), "0x")
            if expected_code != actual_code:
                raise Account.CodeMismatch(
                    address=address,
                    want=expected_code,
                    got=actual_code,
                )

        if self.storage is not None:
            expected_storage = (
                self.storage if isinstance(self.storage, Storage) else Storage(self.storage)
            )
            actual_storage = Storage(alloc["storage"]) if "storage" in alloc else Storage({})
            expected_storage.must_be_equal(address=address, other=actual_storage)

    @classmethod
    def from_dict(cls: Type, data: "Dict | Account") -> "Account":
        """
        Create account from dictionary.
        """
        if isinstance(data, cls):
            return data
        return cls(**data)

    @classmethod
    def with_code(cls: Type, code: BytesConvertible) -> "Account":
        """
        Create account with provided `code` and nonce of `1`.
        """
        return Account(nonce=1, code=code)

    @classmethod
    def merge(
        cls: Type, account_1: "Dict | Account | None", account_2: "Dict | Account | None"
    ) -> "Account":
        """
        Create a merged account from two sources.
        """

        def to_kwargs_dict(account: "Dict | Account | None") -> Dict:
            if account is None:
                return {}
            if isinstance(account, dict):
                return account
            elif isinstance(account, cls):
                return {
                    f.name: v for f in fields(cls) if (v := getattr(account, f.name)) is not None
                }
            raise TypeError(f"Unexpected type for account merge: {type(account)}")

        kwargs = to_kwargs_dict(account_1)
        kwargs.update(to_kwargs_dict(account_2))

        return cls(**kwargs)


class Alloc(dict, Mapping[Address, Account], SupportsJSON):
    """
    Allocation of accounts in the state, pre and post test execution.
    """

    def __init__(self, d: Mapping[FixedSizeBytesConvertible, Account | Dict] = {}):
        for address, account in d.items():
            address = Address(address)
            assert address not in self, f"Duplicate address in alloc: {address}"
            self[address] = Account.from_dict(account)

    @classmethod
    def merge(cls, alloc_1: "Alloc", alloc_2: "Alloc") -> "Alloc":
        """
        Returns the merged allocation of two sources.
        """
        merged = alloc_1.copy()

        for address, other_account in alloc_2.items():
            merged[address] = Account.merge(merged.get(address, None), other_account)

        return Alloc(merged)

    def __json__(self, encoder: JSONEncoder) -> Mapping[str, Any]:
        """
        Returns the JSON representation of the allocation.
        """
        return encoder.default(
            {Address(address): Account.from_dict(account) for address, account in self.items()}
        )


def alloc_to_accounts(got_alloc: Dict[str, Any]) -> Mapping[str, Account]:
    """
    Converts the post state alloc returned from t8n to a mapping of accounts.
    """
    accounts = {}
    for address, value in got_alloc.items():
        account = Account(
            nonce=int_or_none(value.get("nonce", None)),
            balance=int_or_none(value.get("balance", None)),
            code=value.get("code", None),
            storage=value.get("storage", None),
        )
        accounts[address] = account
    return accounts


@dataclass(kw_only=True)
class Withdrawal:
    """
    Structure to represent a single withdrawal of a validator's balance from
    the beacon chain.
    """

    index: NumberConvertible = field(
        json_encoder=JSONEncoder.Field(
            cast_type=HexNumber,
        ),
    )
    validator: NumberConvertible = field(
        json_encoder=JSONEncoder.Field(
            name="validatorIndex",
            cast_type=HexNumber,
        ),
    )
    address: FixedSizeBytesConvertible = field(
        json_encoder=JSONEncoder.Field(
            cast_type=Address,
        ),
    )
    amount: NumberConvertible = field(
        json_encoder=JSONEncoder.Field(
            cast_type=HexNumber,
        ),
    )

    def to_serializable_list(self) -> List[Any]:
        """
        Returns a list of the withdrawal's attributes in the order they should
        be serialized.
        """
        return [
            Uint(Number(self.index)),
            Uint(Number(self.validator)),
            Address(self.address),
            Uint(Number(self.amount)),
        ]


def withdrawals_root(withdrawals: List[Withdrawal]) -> bytes:
    """
    Returns the withdrawals root of a list of withdrawals.
    """
    t = HexaryTrie(db={})
    for i, w in enumerate(withdrawals):
        t.set(eth_rlp.encode(Uint(i)), eth_rlp.encode(w.to_serializable_list()))
    return t.root_hash


@dataclass(kw_only=True)
class FixtureWithdrawal(Withdrawal):
    """
    Structure to represent a single withdrawal of a validator's balance from
    the beacon chain in the output fixture.
    """

    index: NumberConvertible = field(
        json_encoder=JSONEncoder.Field(
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    validator: NumberConvertible = field(
        json_encoder=JSONEncoder.Field(
            name="validatorIndex",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    amount: NumberConvertible = field(
        json_encoder=JSONEncoder.Field(
            cast_type=ZeroPaddedHexNumber,
        ),
    )

    @classmethod
    def from_withdrawal(cls, w: Withdrawal) -> "FixtureWithdrawal":
        """
        Returns a FixtureWithdrawal from a Withdrawal.
        """
        kwargs = {field.name: getattr(w, field.name) for field in fields(w)}
        return cls(**kwargs)


DEFAULT_BASE_FEE = 7


@dataclass(kw_only=True)
class Environment:
    """
    Structure used to keep track of the context in which a block
    must be executed.
    """

    coinbase: FixedSizeBytesConvertible = field(
        default="0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
        json_encoder=JSONEncoder.Field(
            name="currentCoinbase",
            cast_type=Address,
        ),
    )
    gas_limit: NumberConvertible = field(
        default=100000000000000000,
        json_encoder=JSONEncoder.Field(
            name="currentGasLimit",
            cast_type=Number,
        ),
    )
    number: NumberConvertible = field(
        default=1,
        json_encoder=JSONEncoder.Field(
            name="currentNumber",
            cast_type=Number,
        ),
    )
    timestamp: NumberConvertible = field(
        default=1000,
        json_encoder=JSONEncoder.Field(
            name="currentTimestamp",
            cast_type=Number,
        ),
    )
    prev_randao: Optional[NumberConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="currentRandom",
            cast_type=Number,
        ),
    )
    difficulty: Optional[NumberConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="currentDifficulty",
            cast_type=Number,
        ),
    )
    block_hashes: Dict[NumberConvertible, FixedSizeBytesConvertible] = field(
        default_factory=dict,
        json_encoder=JSONEncoder.Field(
            name="blockHashes",
            cast_type=lambda x: {str(Number(k)): str(Hash(v)) for k, v in x.items()},
            skip_string_convert=True,
        ),
    )
    ommers: List[FixedSizeBytesConvertible] = field(
        default_factory=list,
        json_encoder=JSONEncoder.Field(
            name="ommers",
            cast_type=lambda x: [str(Hash(y)) for y in x],
            skip_string_convert=True,
        ),
    )
    withdrawals: Optional[List[Withdrawal]] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="withdrawals",
            to_json=True,
        ),
    )

    base_fee: Optional[NumberConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="currentBaseFee",
            cast_type=Number,
        ),
    )
    parent_difficulty: Optional[NumberConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="parentDifficulty",
            cast_type=Number,
        ),
    )

    parent_timestamp: Optional[NumberConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="parentTimestamp",
            cast_type=Number,
        ),
    )
    parent_base_fee: Optional[NumberConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="parentBaseFee",
            cast_type=Number,
        ),
    )
    parent_gas_used: Optional[NumberConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="parentGasUsed",
            cast_type=Number,
        ),
    )
    parent_gas_limit: Optional[NumberConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="parentGasLimit",
            cast_type=Number,
        ),
    )
    parent_ommers_hash: FixedSizeBytesConvertible = field(
        default=0,
        json_encoder=JSONEncoder.Field(
            name="parentUncleHash",
            cast_type=Hash,
        ),
    )
    parent_blob_gas_used: Optional[NumberConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="parentBlobGasUsed",
            cast_type=Number,
        ),
    )
    parent_excess_blob_gas: Optional[NumberConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="parentExcessBlobGas",
            cast_type=Number,
        ),
    )
    blob_gas_used: Optional[NumberConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="currentBlobGasUsed",
            cast_type=Number,
        ),
    )
    excess_blob_gas: Optional[NumberConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="currentExcessBlobGas",
            cast_type=Number,
        ),
    )
    beacon_root: Optional[FixedSizeBytesConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="parentBeaconBlockRoot",
            cast_type=Hash,
        ),
    )
    extra_data: Optional[BytesConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            skip=True,
        ),
    )

    @staticmethod
    def from_parent_header(parent: "FixtureHeader") -> "Environment":
        """
        Instantiates a new environment with the provided header as parent.
        """
        return Environment(
            parent_difficulty=parent.difficulty,
            parent_timestamp=parent.timestamp,
            parent_base_fee=parent.base_fee,
            parent_blob_gas_used=parent.blob_gas_used,
            parent_excess_blob_gas=parent.excess_blob_gas,
            parent_gas_used=parent.gas_used,
            parent_gas_limit=parent.gas_limit,
            parent_ommers_hash=parent.ommers_hash,
            block_hashes={parent.number: parent.hash if parent.hash is not None else 0},
        )

    def parent_hash(self) -> bytes:
        """
        Obtains the latest hash according to the highest block number in
        `block_hashes`.
        """
        if len(self.block_hashes) == 0:
            return bytes([0] * 32)

        last_index = max([Number(k) for k in self.block_hashes.keys()])
        return Hash(self.block_hashes[last_index])

    def apply_new_parent(self, new_parent: "FixtureHeader") -> "Environment":
        """
        Applies a header as parent to a copy of this environment.
        """
        env = copy(self)
        env.parent_difficulty = new_parent.difficulty
        env.parent_timestamp = new_parent.timestamp
        env.parent_base_fee = new_parent.base_fee
        env.parent_blob_gas_used = new_parent.blob_gas_used
        env.parent_excess_blob_gas = new_parent.excess_blob_gas
        env.parent_gas_used = new_parent.gas_used
        env.parent_gas_limit = new_parent.gas_limit
        env.parent_ommers_hash = new_parent.ommers_hash
        env.block_hashes[new_parent.number] = new_parent.hash if new_parent.hash is not None else 0
        return env

    def set_fork_requirements(self, fork: Fork, in_place: bool = False) -> "Environment":
        """
        Fills the required fields in an environment depending on the fork.
        """
        res = self if in_place else copy(self)
        number = Number(res.number)
        timestamp = Number(res.timestamp)
        if fork.header_prev_randao_required(number, timestamp) and res.prev_randao is None:
            res.prev_randao = 0

        if fork.header_withdrawals_required(number, timestamp) and res.withdrawals is None:
            res.withdrawals = []

        if (
            fork.header_base_fee_required(number, timestamp)
            and res.base_fee is None
            and res.parent_base_fee is None
        ):
            res.base_fee = DEFAULT_BASE_FEE

        if fork.header_zero_difficulty_required(number, timestamp):
            res.difficulty = 0

        if (
            fork.header_excess_blob_gas_required(number, timestamp)
            and res.excess_blob_gas is None
            and res.parent_excess_blob_gas is None
        ):
            res.excess_blob_gas = 0

        if (
            fork.header_blob_gas_used_required(number, timestamp)
            and res.blob_gas_used is None
            and res.parent_blob_gas_used is None
        ):
            res.blob_gas_used = 0

        if fork.header_beacon_root_required(number, timestamp) and res.beacon_root is None:
            res.beacon_root = 0

        return res


@dataclass(kw_only=True)
class AccessList:
    """
    Access List for transactions.
    """

    address: FixedSizeBytesConvertible = field(
        json_encoder=JSONEncoder.Field(
            cast_type=Address,
        ),
    )
    storage_keys: List[FixedSizeBytesConvertible] = field(
        default_factory=list,
        json_encoder=JSONEncoder.Field(
            name="storageKeys",
            cast_type=lambda x: [str(Hash(k)) for k in x],
            skip_string_convert=True,
        ),
    )

    def to_list(self) -> List[bytes | List[bytes]]:
        """
        Returns the access list as a list of serializable elements.
        """
        return [Address(self.address), [Hash(k) for k in self.storage_keys]]


@dataclass(kw_only=True)
class Transaction:
    """
    Generic object that can represent all Ethereum transaction types.
    """

    ty: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="type",
            cast_type=HexNumber,
        ),
    )
    """
    Transaction type value.
    """
    chain_id: int = field(
        default=1,
        json_encoder=JSONEncoder.Field(
            name="chainId",
            cast_type=HexNumber,
        ),
    )
    nonce: int = field(
        default=0,
        json_encoder=JSONEncoder.Field(
            cast_type=HexNumber,
        ),
    )
    gas_price: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="gasPrice",
            cast_type=HexNumber,
        ),
    )
    max_priority_fee_per_gas: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="maxPriorityFeePerGas",
            cast_type=HexNumber,
        ),
    )
    max_fee_per_gas: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="maxFeePerGas",
            cast_type=HexNumber,
        ),
    )
    gas_limit: int = field(
        default=21000,
        json_encoder=JSONEncoder.Field(
            name="gas",
            cast_type=HexNumber,
        ),
    )
    to: Optional[FixedSizeBytesConvertible] = field(
        default=AddrAA,
        json_encoder=JSONEncoder.Field(
            cast_type=Address,
        ),
    )
    value: int = field(
        default=0,
        json_encoder=JSONEncoder.Field(
            cast_type=HexNumber,
        ),
    )
    data: BytesConvertible = field(
        default_factory=bytes,
        json_encoder=JSONEncoder.Field(
            name="input",
            cast_type=Bytes,
        ),
    )
    access_list: Optional[List[AccessList]] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="accessList",
            to_json=True,
        ),
    )
    max_fee_per_blob_gas: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="maxFeePerBlobGas",
            cast_type=HexNumber,
        ),
    )
    blob_versioned_hashes: Optional[Sequence[FixedSizeBytesConvertible]] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="blobVersionedHashes",
            cast_type=lambda x: [Hash(k) for k in x],
            to_json=True,
        ),
    )
    v: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            cast_type=HexNumber,
        ),
    )
    r: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            cast_type=HexNumber,
        ),
    )
    s: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            cast_type=HexNumber,
        ),
    )
    wrapped_blob_transaction: bool = field(
        default=False,
        json_encoder=JSONEncoder.Field(
            skip=True,
        ),
    )
    blobs: Optional[Sequence[bytes]] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            skip=True,
        ),
    )
    blob_kzg_commitments: Optional[Sequence[bytes]] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            skip=True,
        ),
    )
    blob_kzg_proofs: Optional[Sequence[bytes]] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            skip=True,
        ),
    )
    sender: Optional[FixedSizeBytesConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            cast_type=Address,
        ),
    )
    secret_key: Optional[FixedSizeBytesConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="secretKey",
            cast_type=Hash,
        ),
    )
    protected: bool = field(
        default=True,
        json_encoder=JSONEncoder.Field(
            skip=True,
        ),
    )
    error: Optional[str] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            skip=True,
        ),
    )

    class InvalidFeePayment(Exception):
        """
        Transaction described more than one fee payment type.
        """

        def __str__(self):
            """Print exception string"""
            return "only one type of fee payment field can be used in a single tx"

    class InvalidSignaturePrivateKey(Exception):
        """
        Transaction describes both the signature and private key of
        source account.
        """

        def __str__(self):
            """Print exception string"""
            return "can't define both 'signature' and 'private_key'"

    def __post_init__(self) -> None:
        """
        Ensures the transaction has no conflicting properties.
        """
        if self.gas_price is not None and (
            self.max_fee_per_gas is not None
            or self.max_priority_fee_per_gas is not None
            or self.max_fee_per_blob_gas is not None
        ):
            raise Transaction.InvalidFeePayment()

        if (
            self.gas_price is None
            and self.max_fee_per_gas is None
            and self.max_priority_fee_per_gas is None
            and self.max_fee_per_blob_gas is None
        ):
            self.gas_price = 10

        if self.v is not None and self.secret_key is not None:
            raise Transaction.InvalidSignaturePrivateKey()

        if self.v is None and self.secret_key is None:
            self.secret_key = TestPrivateKey

        if self.ty is None:
            # Try to deduce transaction type from included fields
            if self.max_fee_per_blob_gas is not None:
                self.ty = 3
            elif self.max_fee_per_gas is not None:
                self.ty = 2
            elif self.access_list is not None:
                self.ty = 1
            else:
                self.ty = 0

        # Set default values for fields that are required for certain tx types
        if self.ty >= 1 and self.access_list is None:
            self.access_list = []

        if self.ty >= 2 and self.max_priority_fee_per_gas is None:
            self.max_priority_fee_per_gas = 0

    def with_error(self, error: str) -> "Transaction":
        """
        Create a copy of the transaction with an added error.
        """
        tx = copy(self)
        tx.error = error
        return tx

    def with_nonce(self, nonce: int) -> "Transaction":
        """
        Create a copy of the transaction with a modified nonce.
        """
        tx = copy(self)
        tx.nonce = nonce
        return tx

    def with_fields(self, **kwargs) -> "Transaction":
        """
        Create a deepcopy of the transaction with modified fields.
        """
        tx = deepcopy(self)
        for key, value in kwargs.items():
            if hasattr(tx, key):
                setattr(tx, key, value)
            else:
                raise ValueError(f"Invalid field '{key}' for Transaction")
        return tx

    def payload_body(self) -> List[Any]:
        """
        Returns the list of values included in the transaction body.
        """
        if self.v is None or self.r is None or self.s is None:
            raise ValueError("signature must be set before serializing any tx type")

        if self.gas_limit is None:
            raise ValueError("gas_limit must be set for all tx types")
        to = Address(self.to) if self.to is not None else bytes()

        if self.ty == 3:
            # EIP-4844: https://eips.ethereum.org/EIPS/eip-4844
            if self.max_priority_fee_per_gas is None:
                raise ValueError("max_priority_fee_per_gas must be set for type 3 tx")
            if self.max_fee_per_gas is None:
                raise ValueError("max_fee_per_gas must be set for type 3 tx")
            if self.max_fee_per_blob_gas is None:
                raise ValueError("max_fee_per_blob_gas must be set for type 3 tx")
            if self.blob_versioned_hashes is None:
                raise ValueError("blob_versioned_hashes must be set for type 3 tx")
            if self.access_list is None:
                raise ValueError("access_list must be set for type 3 tx")

            if self.wrapped_blob_transaction:
                if self.blobs is None:
                    raise ValueError("blobs must be set for network version of type 3 tx")
                if self.blob_kzg_commitments is None:
                    raise ValueError(
                        "blob_kzg_commitments must be set for network version of type 3 tx"
                    )
                if self.blob_kzg_proofs is None:
                    raise ValueError(
                        "blob_kzg_proofs must be set for network version of type 3 tx"
                    )

                return [
                    [
                        Uint(self.chain_id),
                        Uint(self.nonce),
                        Uint(self.max_priority_fee_per_gas),
                        Uint(self.max_fee_per_gas),
                        Uint(self.gas_limit),
                        to,
                        Uint(self.value),
                        Bytes(self.data),
                        [a.to_list() for a in self.access_list],
                        Uint(self.max_fee_per_blob_gas),
                        [Hash(h) for h in self.blob_versioned_hashes],
                        Uint(self.v),
                        Uint(self.r),
                        Uint(self.s),
                    ],
                    self.blobs,
                    self.blob_kzg_commitments,
                    self.blob_kzg_proofs,
                ]
            else:
                return [
                    Uint(self.chain_id),
                    Uint(self.nonce),
                    Uint(self.max_priority_fee_per_gas),
                    Uint(self.max_fee_per_gas),
                    Uint(self.gas_limit),
                    to,
                    Uint(self.value),
                    Bytes(self.data),
                    [a.to_list() for a in self.access_list],
                    Uint(self.max_fee_per_blob_gas),
                    [Hash(h) for h in self.blob_versioned_hashes],
                    Uint(self.v),
                    Uint(self.r),
                    Uint(self.s),
                ]
        elif self.ty == 2:
            # EIP-1559: https://eips.ethereum.org/EIPS/eip-1559
            if self.max_priority_fee_per_gas is None:
                raise ValueError("max_priority_fee_per_gas must be set for type 2 tx")
            if self.max_fee_per_gas is None:
                raise ValueError("max_fee_per_gas must be set for type 2 tx")
            if self.access_list is None:
                raise ValueError("access_list must be set for type 2 tx")
            return [
                Uint(self.chain_id),
                Uint(self.nonce),
                Uint(self.max_priority_fee_per_gas),
                Uint(self.max_fee_per_gas),
                Uint(self.gas_limit),
                to,
                Uint(self.value),
                Bytes(self.data),
                [a.to_list() for a in self.access_list],
                Uint(self.v),
                Uint(self.r),
                Uint(self.s),
            ]
        elif self.ty == 1:
            # EIP-2930: https://eips.ethereum.org/EIPS/eip-2930
            if self.gas_price is None:
                raise ValueError("gas_price must be set for type 1 tx")
            if self.access_list is None:
                raise ValueError("access_list must be set for type 1 tx")

            return [
                Uint(self.chain_id),
                Uint(self.nonce),
                Uint(self.gas_price),
                Uint(self.gas_limit),
                to,
                Uint(self.value),
                Bytes(self.data),
                [a.to_list() for a in self.access_list],
                Uint(self.v),
                Uint(self.r),
                Uint(self.s),
            ]
        elif self.ty == 0:
            if self.gas_price is None:
                raise ValueError("gas_price must be set for type 0 tx")
            # EIP-155: https://eips.ethereum.org/EIPS/eip-155
            return [
                Uint(self.nonce),
                Uint(self.gas_price),
                Uint(self.gas_limit),
                to,
                Uint(self.value),
                Bytes(self.data),
                Uint(self.v),
                Uint(self.r),
                Uint(self.s),
            ]

        raise NotImplementedError(f"serialized_bytes not implemented for tx type {self.ty}")

    def serialized_bytes(self) -> bytes:
        """
        Returns bytes of the serialized representation of the transaction,
        which is almost always RLP encoding.
        """
        if self.ty is None:
            raise ValueError("ty must be set for all tx types")

        if self.ty > 0:
            return bytes([self.ty]) + eth_rlp.encode(self.payload_body())
        else:
            return eth_rlp.encode(self.payload_body())

    def signing_envelope(self) -> List[Any]:
        """
        Returns the list of values included in the envelope used for signing.
        """
        if self.gas_limit is None:
            raise ValueError("gas_limit must be set for all tx types")
        to = Address(self.to) if self.to is not None else bytes()

        if self.ty == 3:
            # EIP-4844: https://eips.ethereum.org/EIPS/eip-4844
            if self.max_priority_fee_per_gas is None:
                raise ValueError("max_priority_fee_per_gas must be set for type 3 tx")
            if self.max_fee_per_gas is None:
                raise ValueError("max_fee_per_gas must be set for type 3 tx")
            if self.max_fee_per_blob_gas is None:
                raise ValueError("max_fee_per_blob_gas must be set for type 3 tx")
            if self.blob_versioned_hashes is None:
                raise ValueError("blob_versioned_hashes must be set for type 3 tx")
            return [
                Uint(self.chain_id),
                Uint(self.nonce),
                Uint(self.max_priority_fee_per_gas),
                Uint(self.max_fee_per_gas),
                Uint(self.gas_limit),
                to,
                Uint(self.value),
                Bytes(self.data),
                [a.to_list() for a in self.access_list] if self.access_list is not None else [],
                Uint(self.max_fee_per_blob_gas),
                [Hash(h) for h in self.blob_versioned_hashes],
            ]
        elif self.ty == 2:
            # EIP-1559: https://eips.ethereum.org/EIPS/eip-1559
            if self.max_priority_fee_per_gas is None:
                raise ValueError("max_priority_fee_per_gas must be set for type 2 tx")
            if self.max_fee_per_gas is None:
                raise ValueError("max_fee_per_gas must be set for type 2 tx")
            return [
                Uint(self.chain_id),
                Uint(self.nonce),
                Uint(self.max_priority_fee_per_gas),
                Uint(self.max_fee_per_gas),
                Uint(self.gas_limit),
                to,
                Uint(self.value),
                Bytes(self.data),
                [a.to_list() for a in self.access_list] if self.access_list is not None else [],
            ]
        elif self.ty == 1:
            # EIP-2930: https://eips.ethereum.org/EIPS/eip-2930
            if self.gas_price is None:
                raise ValueError("gas_price must be set for type 1 tx")

            return [
                Uint(self.chain_id),
                Uint(self.nonce),
                Uint(self.gas_price),
                Uint(self.gas_limit),
                to,
                Uint(self.value),
                Bytes(self.data),
                [a.to_list() for a in self.access_list] if self.access_list is not None else [],
            ]
        elif self.ty == 0:
            if self.gas_price is None:
                raise ValueError("gas_price must be set for type 0 tx")

            if self.protected:
                # EIP-155: https://eips.ethereum.org/EIPS/eip-155
                return [
                    Uint(self.nonce),
                    Uint(self.gas_price),
                    Uint(self.gas_limit),
                    to,
                    Uint(self.value),
                    Bytes(self.data),
                    Uint(self.chain_id),
                    Uint(0),
                    Uint(0),
                ]
            else:
                return [
                    Uint(self.nonce),
                    Uint(self.gas_price),
                    Uint(self.gas_limit),
                    to,
                    Uint(self.value),
                    Bytes(self.data),
                ]
        raise NotImplementedError("signing for transaction type {self.ty} not implemented")

    def signing_bytes(self) -> bytes:
        """
        Returns the serialized bytes of the transaction used for signing.
        """
        if self.ty is None:
            raise ValueError("ty must be set for all tx types")

        if self.ty > 0:
            return bytes([self.ty]) + eth_rlp.encode(self.signing_envelope())
        else:
            return eth_rlp.encode(self.signing_envelope())

    def signature_bytes(self) -> bytes:
        """
        Returns the serialized bytes of the transaction signature.
        """
        assert self.v is not None and self.r is not None and self.s is not None
        v = self.v
        if self.ty == 0:
            if self.protected:
                assert self.chain_id is not None
                v -= 35 + (self.chain_id * 2)
            else:
                v -= 27
        return (
            self.r.to_bytes(32, byteorder="big")
            + self.s.to_bytes(32, byteorder="big")
            + bytes([v])
        )

    def with_signature_and_sender(self) -> "Transaction":
        """
        Returns a signed version of the transaction using the private key.
        """
        tx = copy(self)

        if tx.v is not None:
            # Transaction already signed
            if tx.sender is None:
                public_key = PublicKey.from_signature_and_message(
                    tx.signature_bytes(), keccak256(tx.signing_bytes()), hasher=None
                )
                tx.sender = keccak256(public_key.format(compressed=False)[1:])[32 - 20 :]
            return tx

        if tx.secret_key is None:
            raise ValueError("secret_key must be set to sign a transaction")

        # Get the signing bytes
        signing_hash = keccak256(tx.signing_bytes())

        # Sign the bytes

        private_key = PrivateKey(
            secret=Hash(tx.secret_key) if tx.secret_key is not None else bytes(32)
        )
        signature_bytes = private_key.sign_recoverable(signing_hash, hasher=None)
        public_key = PublicKey.from_signature_and_message(
            signature_bytes, signing_hash, hasher=None
        )
        tx.sender = keccak256(public_key.format(compressed=False)[1:])[32 - 20 :]

        tx.v, tx.r, tx.s = (
            signature_bytes[64],
            int.from_bytes(signature_bytes[0:32], byteorder="big"),
            int.from_bytes(signature_bytes[32:64], byteorder="big"),
        )
        if tx.ty == 0:
            if tx.protected:
                tx.v += 35 + (tx.chain_id * 2)
            else:  # not protected
                tx.v += 27

        # Remove the secret key because otherwise we might attempt to sign again (?)
        tx.secret_key = None
        return tx


def transaction_list_to_serializable_list(input_txs: List[Transaction] | None) -> List[Any]:
    """
    Returns the transaction list as a list of serializable objects.
    """
    if input_txs is None:
        return []

    txs: List[Any] = []
    for tx in input_txs:
        if tx.ty is None:
            raise ValueError("ty must be set for all tx types")

        if tx.ty > 0:
            txs.append(tx.serialized_bytes())
        else:
            txs.append(tx.payload_body())
    return txs


def serialize_transactions(input_txs: List[Transaction] | None) -> bytes:
    """
    Serialize a list of transactions into a single byte string, usually RLP encoded.
    """
    return eth_rlp.encode(transaction_list_to_serializable_list(input_txs))


def blob_versioned_hashes_from_transactions(
    input_txs: List[Transaction] | None,
) -> List[FixedSizeBytesConvertible]:
    """
    Gets a list of ordered blob versioned hashes from a list of transactions.
    """
    versioned_hashes: List[FixedSizeBytesConvertible] = []

    if input_txs is None:
        return versioned_hashes

    for tx in input_txs:
        if tx.blob_versioned_hashes is not None and tx.ty == 3:
            versioned_hashes.extend(tx.blob_versioned_hashes)

    return versioned_hashes


@dataclass
class FixtureTransaction(Transaction):
    """
    Representation of an Ethereum transaction within a test Fixture.
    """

    ty: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="type",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    """
    Transaction type value.
    """
    chain_id: int = field(
        default=1,
        json_encoder=JSONEncoder.Field(
            name="chainId",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    nonce: int = field(
        default=0,
        json_encoder=JSONEncoder.Field(
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    gas_price: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="gasPrice",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    max_priority_fee_per_gas: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="maxPriorityFeePerGas",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    max_fee_per_gas: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="maxFeePerGas",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    gas_limit: int = field(
        default=21000,
        json_encoder=JSONEncoder.Field(
            name="gasLimit",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    to: Optional[FixedSizeBytesConvertible] = field(
        default=AddrAA,
        json_encoder=JSONEncoder.Field(
            cast_type=Address,
            default_value_skip_cast="",
        ),
    )
    value: int = field(
        default=0,
        json_encoder=JSONEncoder.Field(
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    data: BytesConvertible = field(
        default_factory=bytes,
        json_encoder=JSONEncoder.Field(
            cast_type=Bytes,
        ),
    )
    max_fee_per_blob_gas: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="maxFeePerBlobGas",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    v: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    r: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    s: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            cast_type=ZeroPaddedHexNumber,
        ),
    )

    @classmethod
    def from_transaction(cls, tx: Transaction) -> "FixtureTransaction":
        """
        Returns a FixtureTransaction from a Transaction.
        """
        kwargs = {field.name: getattr(tx, field.name) for field in fields(tx)}
        return cls(**kwargs)


@dataclass(kw_only=True)
class Header:
    """
    Header type used to describe block header properties in test specs.
    """

    parent_hash: Optional[FixedSizeBytesConvertible] = None
    ommers_hash: Optional[FixedSizeBytesConvertible] = None
    coinbase: Optional[FixedSizeBytesConvertible] = None
    state_root: Optional[FixedSizeBytesConvertible] = None
    transactions_root: Optional[FixedSizeBytesConvertible] = None
    receipt_root: Optional[FixedSizeBytesConvertible] = None
    bloom: Optional[FixedSizeBytesConvertible] = None
    difficulty: Optional[NumberConvertible] = None
    number: Optional[NumberConvertible] = None
    gas_limit: Optional[NumberConvertible] = None
    gas_used: Optional[NumberConvertible] = None
    timestamp: Optional[NumberConvertible] = None
    extra_data: Optional[BytesConvertible] = None
    mix_digest: Optional[FixedSizeBytesConvertible] = None
    nonce: Optional[FixedSizeBytesConvertible] = None
    base_fee: Optional[NumberConvertible | Removable] = None
    withdrawals_root: Optional[FixedSizeBytesConvertible | Removable] = None
    blob_gas_used: Optional[NumberConvertible | Removable] = None
    excess_blob_gas: Optional[NumberConvertible | Removable] = None
    beacon_root: Optional[FixedSizeBytesConvertible | Removable] = None
    hash: Optional[FixedSizeBytesConvertible] = None

    REMOVE_FIELD: ClassVar[Removable] = Removable()
    """
    Sentinel object used to specify that a header field should be removed.
    """
    EMPTY_FIELD: ClassVar[Removable] = Removable()
    """
    Sentinel object used to specify that a header field must be empty during verification.
    """


@dataclass(kw_only=True)
class HeaderFieldSource:
    """
    Block header field metadata specifying the source used to populate the field when collecting
    the block header from different sources, and to validate it.
    """

    required: bool = True
    """
    Whether the field is required or not, regardless of the fork.
    """
    fork_requirement_check: Optional[str] = None
    """
    Name of the method to call to check if the field is required for the current fork.
    """
    default: Optional[Any] = None
    """
    Default value for the field if no value was provided by either the transition tool or the
    environment
    """
    parse_type: Optional[Callable] = None
    """
    The type or function to use to parse the field to before initializing the object.
    """
    source_environment: Optional[str] = None
    """
    Name of the field in the environment object, which can be a callable.
    """
    source_transition_tool: Optional[str] = None
    """
    Name of the field in the transition tool result dictionary.
    """

    def collect(
        self,
        *,
        target: Dict[str, Any],
        field_name: str,
        fork: Fork,
        number: int,
        timestamp: int,
        transition_tool_result: Dict[str, Any],
        environment: Environment,
    ) -> None:
        """
        Collects the field from the different sources according to the
        metadata description.
        """
        value = None
        required = self.required
        if self.fork_requirement_check is not None:
            required = getattr(fork, self.fork_requirement_check)(number, timestamp)

        if self.source_transition_tool is not None:
            if self.source_transition_tool in transition_tool_result:
                got_value = transition_tool_result.get(self.source_transition_tool)
                if got_value is not None:
                    value = got_value

        if self.source_environment is not None:
            got_value = getattr(environment, self.source_environment, None)
            if callable(got_value):
                got_value = got_value()
            if got_value is not None:
                value = got_value

        if required:
            if value is None:
                if self.default is not None:
                    value = self.default
                else:
                    raise ValueError(f"missing required field '{field_name}'")

        if value is not None and self.parse_type is not None:
            value = self.parse_type(value)

        target[field_name] = value


def header_field(*args, source: Optional[HeaderFieldSource] = None, **kwargs) -> Any:
    """
    A wrapper around `dataclasses.field` that allows for json configuration info and header
    metadata.
    """
    if "metadata" in kwargs:
        metadata = kwargs["metadata"]
    else:
        metadata = {}
    assert isinstance(metadata, dict)

    if source is not None:
        metadata["source"] = source

    kwargs["metadata"] = metadata
    return field(*args, **kwargs)


@dataclass(kw_only=True)
class FixtureHeader:
    """
    Representation of an Ethereum header within a test Fixture.
    """

    parent_hash: Hash = header_field(
        source=HeaderFieldSource(
            parse_type=Hash,
            source_environment="parent_hash",
        ),
        json_encoder=JSONEncoder.Field(name="parentHash"),
    )

    ommers_hash: Hash = header_field(
        source=HeaderFieldSource(
            parse_type=Hash,
            source_transition_tool="sha3Uncles",
            default=EmptyOmmersRoot,
        ),
        json_encoder=JSONEncoder.Field(name="uncleHash"),
    )

    coinbase: Address = header_field(
        source=HeaderFieldSource(
            parse_type=Address,
            source_environment="coinbase",
        ),
        json_encoder=JSONEncoder.Field(),
    )

    state_root: Hash = header_field(
        source=HeaderFieldSource(
            parse_type=Hash,
            source_transition_tool="stateRoot",
        ),
        json_encoder=JSONEncoder.Field(name="stateRoot"),
    )

    transactions_root: Hash = header_field(
        source=HeaderFieldSource(
            parse_type=Hash,
            source_transition_tool="txRoot",
        ),
        json_encoder=JSONEncoder.Field(name="transactionsTrie"),
    )

    receipt_root: Hash = header_field(
        source=HeaderFieldSource(
            parse_type=Hash,
            source_transition_tool="receiptsRoot",
        ),
        json_encoder=JSONEncoder.Field(name="receiptTrie"),
    )

    bloom: Bloom = header_field(
        source=HeaderFieldSource(
            parse_type=Bloom,
            source_transition_tool="logsBloom",
        ),
        json_encoder=JSONEncoder.Field(),
    )

    difficulty: int = header_field(
        source=HeaderFieldSource(
            parse_type=Number,
            source_transition_tool="currentDifficulty",
            source_environment="difficulty",
            default=0,
        ),
        json_encoder=JSONEncoder.Field(cast_type=ZeroPaddedHexNumber),
    )

    number: int = header_field(
        source=HeaderFieldSource(
            parse_type=Number,
            source_environment="number",
        ),
        json_encoder=JSONEncoder.Field(cast_type=ZeroPaddedHexNumber),
    )

    gas_limit: int = header_field(
        source=HeaderFieldSource(
            parse_type=Number,
            source_environment="gas_limit",
        ),
        json_encoder=JSONEncoder.Field(name="gasLimit", cast_type=ZeroPaddedHexNumber),
    )

    gas_used: int = header_field(
        source=HeaderFieldSource(
            parse_type=Number,
            source_transition_tool="gasUsed",
        ),
        json_encoder=JSONEncoder.Field(name="gasUsed", cast_type=ZeroPaddedHexNumber),
    )

    timestamp: int = header_field(
        source=HeaderFieldSource(
            parse_type=Number,
            source_environment="timestamp",
        ),
        json_encoder=JSONEncoder.Field(cast_type=ZeroPaddedHexNumber),
    )

    extra_data: Bytes = header_field(
        source=HeaderFieldSource(
            parse_type=Bytes,
            source_environment="extra_data",
            default=b"",
        ),
        json_encoder=JSONEncoder.Field(name="extraData"),
    )

    mix_digest: Hash = header_field(
        source=HeaderFieldSource(
            parse_type=Hash,
            source_environment="prev_randao",
            default=b"",
        ),
        json_encoder=JSONEncoder.Field(name="mixHash"),
    )

    nonce: HeaderNonce = header_field(
        source=HeaderFieldSource(
            parse_type=HeaderNonce,
            default=b"",
        ),
        json_encoder=JSONEncoder.Field(),
    )

    base_fee: Optional[int] = header_field(
        default=None,
        source=HeaderFieldSource(
            parse_type=Number,
            fork_requirement_check="header_base_fee_required",
            source_transition_tool="currentBaseFee",
            source_environment="base_fee",
        ),
        json_encoder=JSONEncoder.Field(name="baseFeePerGas", cast_type=ZeroPaddedHexNumber),
    )

    withdrawals_root: Optional[Hash] = header_field(
        default=None,
        source=HeaderFieldSource(
            parse_type=Hash,
            fork_requirement_check="header_withdrawals_required",
            source_transition_tool="withdrawalsRoot",
        ),
        json_encoder=JSONEncoder.Field(name="withdrawalsRoot"),
    )

    blob_gas_used: Optional[int] = header_field(
        default=None,
        source=HeaderFieldSource(
            parse_type=Number,
            fork_requirement_check="header_blob_gas_used_required",
            source_transition_tool="blobGasUsed",
        ),
        json_encoder=JSONEncoder.Field(name="blobGasUsed", cast_type=ZeroPaddedHexNumber),
    )

    excess_blob_gas: Optional[int] = header_field(
        default=None,
        source=HeaderFieldSource(
            parse_type=Number,
            fork_requirement_check="header_excess_blob_gas_required",
            source_transition_tool="currentExcessBlobGas",
        ),
        json_encoder=JSONEncoder.Field(name="excessBlobGas", cast_type=ZeroPaddedHexNumber),
    )

    beacon_root: Optional[Hash] = header_field(
        default=None,
        source=HeaderFieldSource(
            parse_type=Hash,
            fork_requirement_check="header_beacon_root_required",
            source_environment="beacon_root",
        ),
        json_encoder=JSONEncoder.Field(name="parentBeaconBlockRoot"),
    )

    hash: Optional[Hash] = header_field(
        default=None,
        source=HeaderFieldSource(
            required=False,
        ),
        json_encoder=JSONEncoder.Field(),
    )

    @classmethod
    def collect(
        cls,
        *,
        fork: Fork,
        transition_tool_result: Dict[str, Any],
        environment: Environment,
    ) -> "FixtureHeader":
        """
        Collects a FixtureHeader object from multiple sources:
        - The transition tool result
        - The test's current environment
        """
        # We depend on the environment to get the number and timestamp to check the fork
        # requirements
        number, timestamp = Number(environment.number), Number(environment.timestamp)

        # Collect the header fields
        kwargs: Dict[str, Any] = {}
        for header_field in fields(cls):
            field_name = header_field.name
            metadata = header_field.metadata
            assert metadata is not None, f"Field {field_name} has no header field metadata"
            field_metadata = metadata.get("source")
            assert isinstance(field_metadata, HeaderFieldSource), (
                f"Field {field_name} has invalid header_field " f"metadata: {field_metadata}"
            )
            field_metadata.collect(
                target=kwargs,
                field_name=field_name,
                fork=fork,
                number=number,
                timestamp=timestamp,
                transition_tool_result=transition_tool_result,
                environment=environment,
            )

        # Pass the collected fields as keyword arguments to the constructor
        return cls(**kwargs)

    def join(self, modifier: Header) -> "FixtureHeader":
        """
        Produces a fixture header copy with the set values from the modifier.
        """
        new_fixture_header = copy(self)
        for header_field in self.__dataclass_fields__:
            value = getattr(modifier, header_field)
            if value is not None:
                if value is Header.REMOVE_FIELD:
                    setattr(new_fixture_header, header_field, None)
                else:
                    setattr(new_fixture_header, header_field, value)
        return new_fixture_header

    def verify(self, baseline: Header):
        """
        Verifies that the header fields from the baseline are as expected.
        """
        for header_field in fields(self):
            field_name = header_field.name
            baseline_value = getattr(baseline, field_name)
            if baseline_value is not None:
                assert baseline_value is not Header.REMOVE_FIELD, "invalid baseline header"
                value = getattr(self, field_name)
                if baseline_value is Header.EMPTY_FIELD:
                    assert value is None, f"invalid header field {header_field}"
                    continue
                metadata = header_field.metadata
                field_metadata = metadata.get("source")
                # type check is performed on collect()
                if field_metadata.parse_type is not None:  # type: ignore
                    baseline_value = field_metadata.parse_type(baseline_value)  # type: ignore
                assert value == baseline_value, f"invalid header field {header_field}"

    def build(
        self,
        *,
        txs: List[Transaction],
        ommers: List[Header],
        withdrawals: List[Withdrawal] | None,
    ) -> Tuple[Bytes, Hash]:
        """
        Returns the serialized version of the block and its hash.
        """
        header = [
            self.parent_hash,
            self.ommers_hash,
            self.coinbase,
            self.state_root,
            self.transactions_root,
            self.receipt_root,
            self.bloom,
            Uint(int(self.difficulty)),
            Uint(int(self.number)),
            Uint(int(self.gas_limit)),
            Uint(int(self.gas_used)),
            Uint(int(self.timestamp)),
            self.extra_data,
            self.mix_digest,
            self.nonce,
        ]
        if self.base_fee is not None:
            header.append(Uint(int(self.base_fee)))
        if self.withdrawals_root is not None:
            header.append(self.withdrawals_root)
        if self.blob_gas_used is not None:
            header.append(Uint(int(self.blob_gas_used)))
        if self.excess_blob_gas is not None:
            header.append(Uint(self.excess_blob_gas))
        if self.beacon_root is not None:
            header.append(self.beacon_root)

        block = [
            header,
            transaction_list_to_serializable_list(txs),
            ommers,  # TODO: This is incorrect, and we probably need to serialize the ommers
        ]

        if withdrawals is not None:
            block.append([w.to_serializable_list() for w in withdrawals])

        serialized_bytes = Bytes(eth_rlp.encode(block))

        return serialized_bytes, Hash(keccak256(eth_rlp.encode(header)))


@dataclass(kw_only=True)
class Block(Header):
    """
    Block type used to describe block properties in test specs
    """

    rlp: Optional[BytesConvertible] = None
    """
    If set, blockchain test will skip generating the block and will pass this value directly to
    the Fixture.

    Only meant to be used to simulate blocks with bad formats, and therefore
    requires the block to produce an exception.
    """
    header_verify: Optional[Header] = None
    """
    If set, the block header will be verified against the specified values.
    """
    rlp_modifier: Optional[Header] = None
    """
    An RLP modifying header which values would be used to override the ones
    returned by the  `evm_transition_tool`.
    """
    exception: Optional[str] = None
    """
    If set, the block is expected to be rejected by the client.
    """
    engine_api_error_code: Optional[EngineAPIError] = None
    """
    If set, the block is expected to produce an error response from the Engine API.
    """
    txs: Optional[List[Transaction]] = None
    """
    List of transactions included in the block.
    """
    ommers: Optional[List[Header]] = None
    """
    List of ommer headers included in the block.
    """
    withdrawals: Optional[List[Withdrawal]] = None
    """
    List of withdrawals to perform for this block.
    """

    def set_environment(self, env: Environment) -> Environment:
        """
        Creates a copy of the environment with the characteristics of this
        specific block.
        """
        new_env = copy(env)

        """
        Values that need to be set in the environment and are `None` for
        this block need to be set to their defaults.
        """
        environment_default = Environment()
        new_env.difficulty = self.difficulty
        new_env.coinbase = (
            self.coinbase if self.coinbase is not None else environment_default.coinbase
        )
        new_env.gas_limit = (
            self.gas_limit if self.gas_limit is not None else environment_default.gas_limit
        )
        if not isinstance(self.base_fee, Removable):
            new_env.base_fee = self.base_fee
        new_env.withdrawals = self.withdrawals
        if not isinstance(self.excess_blob_gas, Removable):
            new_env.excess_blob_gas = self.excess_blob_gas
        if not isinstance(self.blob_gas_used, Removable):
            new_env.blob_gas_used = self.blob_gas_used
        if not isinstance(self.beacon_root, Removable):
            new_env.beacon_root = self.beacon_root
        """
        These values are required, but they depend on the previous environment,
        so they can be calculated here.
        """
        if self.number is not None:
            new_env.number = self.number
        else:
            # calculate the next block number for the environment
            if len(new_env.block_hashes) == 0:
                new_env.number = 0
            else:
                new_env.number = max([Number(n) for n in new_env.block_hashes.keys()]) + 1

        if self.timestamp is not None:
            new_env.timestamp = self.timestamp
        else:
            assert new_env.parent_timestamp is not None
            new_env.timestamp = int(Number(new_env.parent_timestamp) + 12)

        return new_env

    def copy_with_rlp(self, rlp: Bytes | BytesConvertible | None) -> "Block":
        """
        Creates a copy of the block and adds the specified RLP.
        """
        new_block = deepcopy(self)
        new_block.rlp = Bytes.or_none(rlp)
        return new_block


@dataclass(kw_only=True)
class FixtureExecutionPayload(FixtureHeader):
    """
    Representation of the execution payload of a block within a test fixture.
    """

    # Skipped fields in the Engine API
    ommers_hash: Hash = field(
        json_encoder=JSONEncoder.Field(
            skip=True,
        ),
    )
    transactions_root: Hash = field(
        json_encoder=JSONEncoder.Field(
            skip=True,
        ),
    )
    difficulty: int = field(
        json_encoder=JSONEncoder.Field(
            skip=True,
        )
    )
    nonce: HeaderNonce = field(
        json_encoder=JSONEncoder.Field(
            skip=True,
        )
    )
    withdrawals_root: Optional[Hash] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            skip=True,
        ),
    )

    # Fields with different names
    coinbase: Address = field(
        json_encoder=JSONEncoder.Field(
            name="feeRecipient",
        )
    )
    receipt_root: Hash = field(
        json_encoder=JSONEncoder.Field(
            name="receiptsRoot",
        ),
    )
    bloom: Bloom = field(
        json_encoder=JSONEncoder.Field(
            name="logsBloom",
        )
    )
    mix_digest: Hash = field(
        json_encoder=JSONEncoder.Field(
            name="prevRandao",
        ),
    )
    hash: Optional[Hash] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="blockHash",
        ),
    )

    # Fields with different formatting
    number: int = field(
        json_encoder=JSONEncoder.Field(
            name="blockNumber",
            cast_type=HexNumber,
        )
    )
    gas_limit: int = field(json_encoder=JSONEncoder.Field(name="gasLimit", cast_type=HexNumber))
    gas_used: int = field(json_encoder=JSONEncoder.Field(name="gasUsed", cast_type=HexNumber))
    timestamp: int = field(json_encoder=JSONEncoder.Field(cast_type=HexNumber))
    base_fee: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(name="baseFeePerGas", cast_type=HexNumber),
    )
    blob_gas_used: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(name="blobGasUsed", cast_type=HexNumber),
    )
    excess_blob_gas: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(name="excessBlobGas", cast_type=HexNumber),
    )

    # Fields only used in the Engine API
    transactions: Optional[List[Transaction]] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            cast_type=lambda txs: [Bytes(tx.serialized_bytes()) for tx in txs],
            to_json=True,
        ),
    )
    withdrawals: Optional[List[Withdrawal]] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            to_json=True,
        ),
    )

    @classmethod
    def from_fixture_header(
        cls,
        header: FixtureHeader,
        transactions: Optional[List[Transaction]] = None,
        withdrawals: Optional[List[Withdrawal]] = None,
    ) -> "FixtureExecutionPayload":
        """
        Returns a FixtureExecutionPayload from a FixtureHeader, a list
        of transactions and a list of withdrawals.
        """
        kwargs = {field.name: getattr(header, field.name) for field in fields(header)}
        return cls(**kwargs, transactions=transactions, withdrawals=withdrawals)


@dataclass(kw_only=True)
class FixtureEngineNewPayload:
    """
    Representation of the `engine_newPayloadVX` information to be
    sent using the block information.
    """

    payload: FixtureExecutionPayload = field(
        json_encoder=JSONEncoder.Field(
            name="executionPayload",
            to_json=True,
        )
    )
    blob_versioned_hashes: Optional[List[FixedSizeBytesConvertible]] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="expectedBlobVersionedHashes",
            cast_type=lambda hashes: [Hash(hash) for hash in hashes],
            to_json=True,
        ),
    )
    version: int = field(
        json_encoder=JSONEncoder.Field(),
    )
    beacon_root: Optional[FixedSizeBytesConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="parentBeaconBlockRoot",
            cast_type=Hash,
        ),
    )
    error_code: Optional[EngineAPIError] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="errorCode",
            cast_type=int,
        ),
    )

    @classmethod
    def from_fixture_header(
        cls,
        fork: Fork,
        header: FixtureHeader,
        transactions: List[Transaction],
        withdrawals: Optional[List[Withdrawal]],
        error_code: Optional[EngineAPIError],
    ) -> Optional["FixtureEngineNewPayload"]:
        """
        Creates a `FixtureEngineNewPayload` from a `FixtureHeader`.
        """
        new_payload_version = fork.engine_new_payload_version(header.number, header.timestamp)

        if new_payload_version is None:
            return None

        new_payload = cls(
            payload=FixtureExecutionPayload.from_fixture_header(
                header=replace(header, beacon_root=None),
                transactions=transactions,
                withdrawals=withdrawals,
            ),
            version=new_payload_version,
            error_code=error_code,
        )

        if fork.engine_new_payload_blob_hashes(header.number, header.timestamp):
            new_payload.blob_versioned_hashes = blob_versioned_hashes_from_transactions(
                transactions
            )

        if fork.engine_new_payload_beacon_root(header.number, header.timestamp):
            new_payload.beacon_root = header.beacon_root

        return new_payload


@dataclass(kw_only=True)
class FixtureBlock:
    """
    Representation of an Ethereum block within a test Fixture.
    """

    rlp: Bytes = field(
        json_encoder=JSONEncoder.Field(),
    )
    block_header: Optional[FixtureHeader] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="blockHeader",
            to_json=True,
        ),
    )
    new_payload: Optional[FixtureEngineNewPayload] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="engineNewPayload",
            to_json=True,
        ),
    )
    expected_exception: Optional[str] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="expectException",
        ),
    )
    block_number: Optional[NumberConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="blocknumber",
            cast_type=Number,
        ),
    )
    txs: Optional[List[Transaction]] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="transactions",
            cast_type=lambda txs: [FixtureTransaction.from_transaction(tx) for tx in txs],
            to_json=True,
        ),
    )
    ommers: Optional[List[FixtureHeader]] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="uncleHeaders",
            to_json=True,
        ),
    )
    withdrawals: Optional[List[Withdrawal]] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="withdrawals",
            cast_type=lambda withdrawals: [
                FixtureWithdrawal.from_withdrawal(w) for w in withdrawals
            ],
            to_json=True,
        ),
    )


@dataclass(kw_only=True)
class Fixture:
    """
    Cross-client compatible Ethereum test fixture.
    """

    info: Dict[str, str] = field(
        default_factory=dict,
        json_encoder=JSONEncoder.Field(
            name="_info",
            to_json=True,
        ),
    )
    blocks: List[FixtureBlock] = field(
        json_encoder=JSONEncoder.Field(
            name="blocks",
            to_json=True,
        ),
    )
    genesis: FixtureHeader = field(
        json_encoder=JSONEncoder.Field(
            name="genesisBlockHeader",
            to_json=True,
        ),
    )
    genesis_rlp: Bytes = field(
        json_encoder=JSONEncoder.Field(
            name="genesisRLP",
        ),
    )
    head: Hash = field(
        json_encoder=JSONEncoder.Field(
            name="lastblockhash",
        ),
    )
    fork: str = field(
        json_encoder=JSONEncoder.Field(
            name="network",
        ),
    )
    pre_state: Mapping[str, Account] = field(
        json_encoder=JSONEncoder.Field(
            name="pre",
            cast_type=Alloc,
            to_json=True,
        ),
    )
    post_state: Optional[Mapping[str, Account]] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="postState",
            cast_type=Alloc,
            to_json=True,
        ),
    )
    seal_engine: str = field(
        json_encoder=JSONEncoder.Field(
            name="sealEngine",
        ),
    )
    name: str = field(
        default="",
        json_encoder=JSONEncoder.Field(
            skip=True,
        ),
    )

    _json: Dict[str, Any] | None = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            skip=True,
        ),
    )

    def __post_init__(self):
        """
        Post init hook to convert to JSON after instantiation.
        """
        self._json = to_json(self)

    def to_json(self) -> Dict[str, Any]:
        """
        Convert to JSON.
        """
        assert self._json is not None, "Fixture not initialized"
        self._json["_info"] = self.info
        return self._json

    def fill_info(
        self,
        t8n: TransitionTool,
        ref_spec: ReferenceSpec | None,
    ):
        """
        Fill the info field for this fixture
        """
        self.info["filling-transition-tool"] = t8n.version()
        if ref_spec is not None:
            ref_spec.write_info(self.info)
