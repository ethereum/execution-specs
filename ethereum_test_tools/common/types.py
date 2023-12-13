"""
Useful types for generating Ethereum tests.
"""
from copy import copy, deepcopy
from dataclasses import dataclass, fields
from itertools import count
from typing import (
    Any,
    ClassVar,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    SupportsBytes,
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

from .constants import AddrAA, TestPrivateKey
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
from .json import JSONEncoder, SupportsJSON, field


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

    def __init__(self, input: StorageDictType | "Storage" = {}, start_slot: int = 0):
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

    def __iter__(self) -> Iterator[int]:
        """Returns iterator of the storage"""
        return iter(self.data)

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

    def is_empty(self: "Account") -> bool:
        """
        Returns true if an account deemed empty.
        """
        return (
            (self.nonce == 0 or self.nonce is None)
            and (self.balance == 0 or self.balance is None)
            and (not self.code and self.code is None)
            and (not self.storage or self.storage == {} or self.storage is None)
        )

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
            account = Account.from_dict(account)
            assert not account.is_empty(), f"Empty account: {account} for address: {address}"
            self[address] = account

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
        default=b"\x00",
        json_encoder=JSONEncoder.Field(
            skip=True,
        ),
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
        elif res.difficulty is None and res.parent_difficulty is None:
            res.difficulty = 0x20000

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


def transaction_list_root(input_txs: List[Transaction] | None) -> Hash:
    """
    Returns the transactions root of a list of transactions.
    """
    t = HexaryTrie(db={})
    for i, tx in enumerate(input_txs or []):
        t.set(eth_rlp.encode(Uint(i)), tx.serialized_bytes())
    return Hash(t.root_hash)


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
