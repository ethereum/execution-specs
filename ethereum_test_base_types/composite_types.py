"""Base composite types for Ethereum test cases."""

from dataclasses import dataclass
from typing import Any, ClassVar, Dict, List, SupportsBytes, Type, TypeAlias

from pydantic import Field, PrivateAttr, TypeAdapter

from .base_types import Address, Bytes, Hash, HashInt, HexNumber, ZeroPaddedHexNumber
from .conversions import BytesConvertible, NumberConvertible
from .pydantic import CamelModel, EthereumTestRootModel
from .serialization import RLPSerializable

StorageKeyValueTypeConvertible = NumberConvertible
StorageKeyValueType = HashInt
StorageKeyValueTypeAdapter = TypeAdapter(StorageKeyValueType)
StorageRootType = Dict[NumberConvertible, NumberConvertible]


class Storage(EthereumTestRootModel[Dict[StorageKeyValueType, StorageKeyValueType]]):
    """
    Definition of contract storage in the `pre` or `post` state of a test.

    This model accepts a dictionary with keys and values as any of: str, int,
    bytes, or any type that supports conversion to bytes, and automatically
    casts them to `HashInt`.
    """

    # internal storage is maintained as a dict with HashInt keys and values.
    root: Dict[StorageKeyValueType, StorageKeyValueType] = Field(default_factory=dict)

    _current_slot: int = PrivateAttr(0)
    _hint_map: Dict[StorageKeyValueType, str] = PrivateAttr(default_factory=dict)
    _any_map: Dict[StorageKeyValueType, bool] = PrivateAttr(default_factory=dict)

    StorageDictType: ClassVar[TypeAlias] = Dict[
        str | int | bytes | SupportsBytes, str | int | bytes | SupportsBytes
    ]
    """
    Dictionary type to be used when defining an input to initialize a storage.
    """

    @dataclass(kw_only=True)
    class InvalidTypeError(Exception):
        """Invalid type used when describing test's expected storage key or value."""

        key_or_value: Any

        def __init__(self, key_or_value: Any, *args):
            """Initialize the exception with the invalid type."""
            super().__init__(args)
            self.key_or_value = key_or_value

        def __str__(self):
            """Print exception string."""
            return f"invalid type for key/value: {self.key_or_value}"

    @dataclass(kw_only=True)
    class InvalidValueError(Exception):
        """
        Invalid value used when describing test's expected storage key or
        value.
        """

        key_or_value: Any

        def __init__(self, key_or_value: Any, *args):
            """Initialize the exception with the invalid value."""
            super().__init__(args)
            self.key_or_value = key_or_value

        def __str__(self):
            """Print exception string."""
            return f"invalid value for key/value: {self.key_or_value}"

    @dataclass(kw_only=True)
    class MissingKeyError(Exception):
        """Test expected to find a storage key set but key was missing."""

        key: int

        def __init__(self, key: int, *args):
            """Initialize the exception with the missing key."""
            super().__init__(args)
            self.key = key

        def __str__(self):
            """Print exception string."""
            return "key {0} not found in storage".format(Hash(self.key))

    @dataclass(kw_only=True)
    class KeyValueMismatchError(Exception):
        """
        Test expected a certain value in a storage key but value found
        was different.
        """

        address: Address
        key: int
        want: int
        got: int
        hint: str

        def __init__(self, address: Address, key: int, want: int, got: int, hint: str = "", *args):
            """Initialize the exception with the address, key, wanted and got values."""
            super().__init__(args)
            self.address = address
            self.key = key
            self.want = want
            self.got = got
            self.hint = hint

        def __str__(self):
            """Print exception string."""
            label_str = ""
            if self.address.label is not None:
                label_str = f" ({self.address.label})"
            return (
                f"incorrect value in address {self.address}{label_str} for "
                + f"key {Hash(self.key)}{f' ({self.hint})' if self.hint else ''}:"
                + f" want {HexNumber(self.want)} (dec:{int(self.want)}),"
                + f" got {HexNumber(self.got)} (dec:{int(self.got)})"
            )

    def __contains__(self, key: StorageKeyValueTypeConvertible | StorageKeyValueType) -> bool:
        """Check for an item in the storage."""
        return StorageKeyValueTypeAdapter.validate_python(key) in self.root

    def __getitem__(
        self, key: StorageKeyValueTypeConvertible | StorageKeyValueType
    ) -> StorageKeyValueType:
        """Return an item from the storage."""
        return self.root[StorageKeyValueTypeAdapter.validate_python(key)]

    def __setitem__(
        self,
        key: StorageKeyValueTypeConvertible | StorageKeyValueType,
        value: StorageKeyValueTypeConvertible | StorageKeyValueType,
    ):
        """Set an item in the storage."""
        self.root[StorageKeyValueTypeAdapter.validate_python(key)] = (
            StorageKeyValueTypeAdapter.validate_python(value)
        )

    def __delitem__(self, key: StorageKeyValueTypeConvertible | StorageKeyValueType):
        """Delete an item from the storage."""
        del self.root[StorageKeyValueTypeAdapter.validate_python(key)]

    def __iter__(self):
        """Return an iterator over the storage."""
        return iter(self.root)

    def __eq__(self, other) -> bool:
        """Return True if both storages are equal."""
        if not isinstance(other, Storage):
            return False
        return self.root == other.root

    def __ne__(self, other) -> bool:
        """Return True if both storages are not equal."""
        if not isinstance(other, Storage):
            return False
        return self.root != other.root

    def __bool__(self) -> bool:
        """Return True if the storage is not empty."""
        return any(v for v in self.root.values())

    def __add__(self, other: "Storage") -> "Storage":
        """Return a new storage that is the sum of two storages."""
        return Storage({**self.root, **other.root})

    def keys(self) -> set[StorageKeyValueType]:
        """Return the keys of the storage."""
        return set(self.root.keys())

    def set_next_slot(self, slot: int) -> "Storage":
        """Set the next slot to be used by `store_next`."""
        self._current_slot = slot
        return self

    def items(self):
        """Return the items of the storage."""
        return self.root.items()

    def set_expect_any(self, key: StorageKeyValueTypeConvertible | StorageKeyValueType):
        """Mark key to be able to have any expected value when comparing storages."""
        self._any_map[StorageKeyValueTypeAdapter.validate_python(key)] = True

    def store_next(
        self, value: StorageKeyValueTypeConvertible | StorageKeyValueType | bool, hint: str = ""
    ) -> StorageKeyValueType:
        """
        Store a value in the storage and returns the key where the value is stored.

        Increments the key counter so the next time this function is called,
        the next key is used.
        """
        slot = StorageKeyValueTypeAdapter.validate_python(self._current_slot)
        self._current_slot += 1
        if hint:
            self._hint_map[slot] = hint
        self[slot] = StorageKeyValueTypeAdapter.validate_python(value)
        return slot

    def peek_slot(self) -> int:
        """Peek the next slot that will be used by `store_next`."""
        return self._current_slot

    def contains(self, other: "Storage") -> bool:
        """
        Return True if self contains all keys with equal value as
        contained by second storage.
        Used for comparison with test expected post state and alloc returned
        by the transition tool.
        """
        for key in other.keys():
            if key not in self:
                return False
            if self[key] != other[key]:
                return False
        return True

    def must_contain(self, address: Address, other: "Storage"):
        """
        Succeeds only if self contains all keys with equal value as
        contained by second storage.
        Used for comparison with test expected post state and alloc returned
        by the transition tool.
        Raises detailed exception when a difference is found.
        """
        for key in other.keys():
            if key not in self:
                # storage[key]==0 is equal to missing storage
                if other[key] != 0:
                    raise Storage.MissingKeyError(key=key)
            elif self[key] != other[key]:
                raise Storage.KeyValueMismatchError(
                    address=address,
                    key=key,
                    want=self[key],
                    got=other[key],
                    hint=self._hint_map.get(key, ""),
                )

    def must_be_equal(self, address: Address, other: "Storage | None"):
        """Succeed only if "self" is equal to "other" storage."""
        # Test keys contained in both storage objects
        if other is None:
            other = Storage({})
        for key in self.keys() & other.keys():
            if self[key] != other[key]:
                raise Storage.KeyValueMismatchError(
                    address=address,
                    key=key,
                    want=self[key],
                    got=other[key],
                    hint=self._hint_map.get(key, ""),
                )

        # Test keys contained in either one of the storage objects
        for key in self.keys() ^ other.keys():
            if key in self:
                if self[key] != 0:
                    raise Storage.KeyValueMismatchError(
                        address=address,
                        key=key,
                        want=self[key],
                        got=0,
                        hint=self._hint_map.get(key, ""),
                    )

            elif other[key] != 0:
                # Skip key verification if we allow this key to be ANY
                if self._any_map.get(key) is True:
                    continue
                raise Storage.KeyValueMismatchError(
                    address=address,
                    key=key,
                    want=0,
                    got=other[key],
                    hint=self._hint_map.get(key, ""),
                )

    def canary(self) -> "Storage":
        """
        Return a canary storage filled with non-zero values where the current storage expects
        zero values, to guarantee that the test overwrites the storage.
        """
        return Storage({key: HashInt(0xBA5E) for key in self.keys() if self[key] == 0})


class Account(CamelModel):
    """State associated with an address."""

    nonce: ZeroPaddedHexNumber = ZeroPaddedHexNumber(0)
    """
    The scalar value equal to a) the number of transactions sent by
    an Externally Owned Account, b) the amount of contracts created by a
    contract.
    """
    balance: ZeroPaddedHexNumber = ZeroPaddedHexNumber(0)
    """
    The amount of Wei (10<sup>-18</sup> Eth) the account has.
    """
    code: Bytes = Bytes(b"")
    """
    Bytecode contained by the account.
    """
    storage: Storage = Field(default_factory=Storage)
    """
    Storage within a contract.
    """

    NONEXISTENT: ClassVar[None] = None
    """
    Sentinel object used to specify when an account should not exist in the
    state.
    """

    @dataclass(kw_only=True)
    class NonceMismatchError(Exception):
        """
        Test expected a certain nonce value for an account but a different
        value was found.
        """

        address: Address
        want: int | None
        got: int | None

        def __init__(self, address: Address, want: int | None, got: int | None, *args):
            """Initialize the exception with the address, wanted and got values."""
            super().__init__(args)
            self.address = address
            self.want = want
            self.got = got

        def __str__(self):
            """Print exception string."""
            label_str = ""
            if self.address.label is not None:
                label_str = f" ({self.address.label})"
            return (
                f"unexpected nonce for account {self.address}{label_str}: "
                + f"want {self.want}, got {self.got}"
            )

    @dataclass(kw_only=True)
    class BalanceMismatchError(Exception):
        """
        Test expected a certain balance for an account but a different
        value was found.
        """

        address: Address
        want: int | None
        got: int | None

        def __init__(self, address: Address, want: int | None, got: int | None, *args):
            """Initialize the exception with the address, wanted and got values."""
            super().__init__(args)
            self.address = address
            self.want = want
            self.got = got

        def __str__(self):
            """Print exception string."""
            label_str = ""
            if self.address.label is not None:
                label_str = f" ({self.address.label})"
            return (
                f"unexpected balance for account {self.address}{label_str}: "
                + f"want {self.want}, got {self.got}"
            )

    @dataclass(kw_only=True)
    class CodeMismatchError(Exception):
        """
        Test expected a certain bytecode for an account but a different
        one was found.
        """

        address: Address
        want: bytes | None
        got: bytes | None

        def __init__(self, address: Address, want: bytes | None, got: bytes | None, *args):
            """Initialize the exception with the address, wanted and got values."""
            super().__init__(args)
            self.address = address
            self.want = want
            self.got = got

        def __str__(self):
            """Print exception string."""
            label_str = ""
            if self.address.label is not None:
                label_str = f" ({self.address.label})"
            return (
                f"unexpected code for account {self.address}{label_str}: "
                + f"want {self.want}, got {self.got}"
            )

    def check_alloc(self: "Account", address: Address, account: "Account"):
        """
        Check the returned alloc against an expected account in post state.
        Raises exception on failure.
        """
        if "nonce" in self.model_fields_set:
            if self.nonce != account.nonce:
                raise Account.NonceMismatchError(
                    address=address,
                    want=self.nonce,
                    got=account.nonce,
                )

        if "balance" in self.model_fields_set:
            if self.balance != account.balance:
                raise Account.BalanceMismatchError(
                    address=address,
                    want=self.balance,
                    got=account.balance,
                )

        if "code" in self.model_fields_set:
            if self.code != account.code:
                raise Account.CodeMismatchError(
                    address=address,
                    want=self.code,
                    got=account.code,
                )

        if "storage" in self.model_fields_set:
            self.storage.must_be_equal(address=address, other=account.storage)

    def __bool__(self: "Account") -> bool:
        """Return True on a non-empty account."""
        return any((self.nonce, self.balance, self.code, self.storage))

    @classmethod
    def with_code(cls: Type, code: BytesConvertible) -> "Account":
        """Create account with provided `code` and nonce of `1`."""
        return Account(nonce=HexNumber(1), code=Bytes(code))

    @classmethod
    def merge(
        cls: Type, account_1: "Dict | Account | None", account_2: "Dict | Account | None"
    ) -> "Account":
        """Create a merged account from two sources."""

        def to_kwargs_dict(account: "Dict | Account | None") -> Dict:
            if account is None:
                return {}
            if isinstance(account, dict):
                return account
            elif isinstance(account, cls):
                return account.model_dump(exclude_unset=True)
            raise TypeError(f"Unexpected type for account merge: {type(account)}")

        kwargs = to_kwargs_dict(account_1)
        kwargs.update(to_kwargs_dict(account_2))

        return cls(**kwargs)


class Alloc(EthereumTestRootModel[Dict[Address, Account | None]]):
    """Allocation of accounts in the state, pre and post test execution."""

    root: Dict[Address, Account | None] = Field(default_factory=dict, validate_default=True)


class AccessList(CamelModel, RLPSerializable):
    """Access List for transactions."""

    address: Address
    storage_keys: List[Hash]

    rlp_fields: ClassVar[List[str]] = ["address", "storage_keys"]


class ForkBlobSchedule(CamelModel):
    """Representation of the blob schedule of a given fork."""

    target_blobs_per_block: HexNumber = Field(..., alias="target")
    max_blobs_per_block: HexNumber = Field(..., alias="max")
    base_fee_update_fraction: HexNumber = Field(...)


class BlobSchedule(EthereumTestRootModel[Dict[str, ForkBlobSchedule]]):
    """Blob schedule configuration dictionary."""

    root: Dict[str, ForkBlobSchedule] = Field(default_factory=dict, validate_default=True)

    def append(self, *, fork: str, schedule: Any):
        """Append a new fork schedule."""
        if not isinstance(schedule, ForkBlobSchedule):
            schedule = ForkBlobSchedule(**schedule)
        self.root[fork] = schedule

    def last(self) -> ForkBlobSchedule | None:
        """Return the last schedule."""
        if len(self.root) == 0:
            return None
        return list(self.root.values())[-1]
