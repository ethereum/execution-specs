"""
Useful types for generating Ethereum tests.
"""

import inspect
from dataclasses import dataclass
from enum import IntEnum
from functools import cache, cached_property
from itertools import count
from typing import (
    Any,
    ClassVar,
    Dict,
    Generic,
    Iterator,
    List,
    Sequence,
    SupportsBytes,
    Type,
    TypeAlias,
    TypeVar,
)

from coincurve.keys import PrivateKey, PublicKey
from ethereum import rlp as eth_rlp
from ethereum.base_types import U256, Uint
from ethereum.crypto.hash import keccak256
from ethereum.frontier.fork_types import Account as FrontierAccount
from ethereum.frontier.fork_types import Address as FrontierAddress
from ethereum.frontier.state import State, set_account, set_storage, state_root
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    RootModel,
    TypeAdapter,
    computed_field,
    model_serializer,
    model_validator,
)
from pydantic.alias_generators import to_camel
from trie import HexaryTrie

from ethereum_test_forks import Fork

from ..exceptions import TransactionException
from .base_types import (
    Address,
    Bloom,
    BLSPublicKey,
    BLSSignature,
    Bytes,
    Hash,
    HashInt,
    HexNumber,
    Number,
    NumberBoundTypeVar,
    ZeroPaddedHexNumber,
)
from .constants import TestAddress, TestPrivateKey, TestPrivateKey2
from .conversions import BytesConvertible, FixedSizeBytesConvertible, NumberConvertible


# Sentinel classes
class Removable:
    """
    Sentinel class to detect if a parameter should be removed.
    (`None` normally means "do not modify")
    """

    pass


# Base Models

Model = TypeVar("Model", bound=BaseModel)


class CopyValidateModel(BaseModel):
    """
    Base model for Ethereum tests.
    """

    def copy(self: Model, **kwargs) -> Model:
        """
        Creates a copy of the model with the updated fields.
        """
        return self.__class__(**(self.model_dump() | kwargs))


class CamelModel(CopyValidateModel):
    """
    A base model that converts field names to camel case when serializing.

    For example, the field name `current_timestamp` in a Python model will be represented
    as `currentTimestamp` when it is serialized to json.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        validate_default=True,
    )


StorageKeyValueTypeConvertible = NumberConvertible
StorageKeyValueType = HashInt
StorageKeyValueTypeAdapter = TypeAdapter(StorageKeyValueType)


class Storage(RootModel[Dict[StorageKeyValueType, StorageKeyValueType]]):
    """
    Definition of a storage in pre or post state of a test
    """

    root: Dict[StorageKeyValueType, StorageKeyValueType] = Field(default_factory=dict)

    _current_slot: Iterator[int] = count(0)

    StorageDictType: ClassVar[TypeAlias] = Dict[
        str | int | bytes | SupportsBytes, str | int | bytes | SupportsBytes
    ]
    """
    Dictionary type to be used when defining an input to initialize a storage.
    """

    @dataclass(kw_only=True)
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

    @dataclass(kw_only=True)
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

    @dataclass(kw_only=True)
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
            return "key {0} not found in storage".format(Hash(self.key))

    @dataclass(kw_only=True)
    class KeyValueMismatch(Exception):
        """
        Test expected a certain value in a storage key but value found
        was different.
        """

        address: Address
        key: int
        want: int
        got: int

        def __init__(self, address: Address, key: int, want: int, got: int, *args):
            super().__init__(args)
            self.address = address
            self.key = key
            self.want = want
            self.got = got

        def __str__(self):
            """Print exception string"""
            label_str = ""
            if self.address.label is not None:
                label_str = f" ({self.address.label})"
            return (
                f"incorrect value in address {self.address}{label_str} for "
                + f"key {Hash(self.key)}:"
                + f" want {HexNumber(self.want)} (dec:{self.want}),"
                + f" got {HexNumber(self.got)} (dec:{self.got})"
            )

    def __contains__(self, key: StorageKeyValueTypeConvertible | StorageKeyValueType) -> bool:
        """Checks for an item in the storage"""
        return StorageKeyValueTypeAdapter.validate_python(key) in self.root

    def __getitem__(
        self, key: StorageKeyValueTypeConvertible | StorageKeyValueType
    ) -> StorageKeyValueType:
        """Returns an item from the storage"""
        return self.root[StorageKeyValueTypeAdapter.validate_python(key)]

    def __setitem__(
        self,
        key: StorageKeyValueTypeConvertible | StorageKeyValueType,
        value: StorageKeyValueTypeConvertible | StorageKeyValueType,
    ):  # noqa: SC200
        """Sets an item in the storage"""
        self.root[
            StorageKeyValueTypeAdapter.validate_python(key)
        ] = StorageKeyValueTypeAdapter.validate_python(value)

    def __delitem__(self, key: StorageKeyValueTypeConvertible | StorageKeyValueType):
        """Deletes an item from the storage"""
        del self.root[StorageKeyValueTypeAdapter.validate_python(key)]

    def __iter__(self):
        """Returns an iterator over the storage"""
        return iter(self.root)

    def __eq__(self, other) -> bool:
        """
        Returns True if both storages are equal.
        """
        if not isinstance(other, Storage):
            return False
        return self.root == other.root

    def __ne__(self, other) -> bool:
        """
        Returns True if both storages are not equal.
        """
        if not isinstance(other, Storage):
            return False
        return self.root != other.root

    def __bool__(self) -> bool:
        """Returns True if the storage is not empty"""
        return any(v for v in self.root.values())

    def keys(self) -> set[StorageKeyValueType]:
        """Returns the keys of the storage"""
        return set(self.root.keys())

    def store_next(
        self, value: StorageKeyValueTypeConvertible | StorageKeyValueType | bool
    ) -> StorageKeyValueType:
        """
        Stores a value in the storage and returns the key where the value is stored.

        Increments the key counter so the next time this function is called,
        the next key is used.
        """
        slot = StorageKeyValueTypeAdapter.validate_python(next(self._current_slot))
        self[slot] = StorageKeyValueTypeAdapter.validate_python(value)
        return slot

    def contains(self, other: "Storage") -> bool:
        """
        Returns True if self contains all keys with equal value as
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
                    raise Storage.MissingKey(key=key)
            elif self[key] != other[key]:
                raise Storage.KeyValueMismatch(
                    address=address, key=key, want=self[key], got=other[key]
                )

    def must_be_equal(self, address: Address, other: "Storage | None"):
        """
        Succeeds only if "self" is equal to "other" storage.
        """
        # Test keys contained in both storage objects
        if other is None:
            other = Storage({})
        for key in self.keys() & other.keys():
            if self[key] != other[key]:
                raise Storage.KeyValueMismatch(
                    address=address, key=key, want=self[key], got=other[key]
                )

        # Test keys contained in either one of the storage objects
        for key in self.keys() ^ other.keys():
            if key in self:
                if self[key] != 0:
                    raise Storage.KeyValueMismatch(address=address, key=key, want=self[key], got=0)

            elif other[key] != 0:
                raise Storage.KeyValueMismatch(address=address, key=key, want=0, got=other[key])


class Account(CopyValidateModel):
    """
    State associated with an address.
    """

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
    class NonceMismatch(Exception):
        """
        Test expected a certain nonce value for an account but a different
        value was found.
        """

        address: Address
        want: int | None
        got: int | None

        def __init__(self, address: Address, want: int | None, got: int | None, *args):
            super().__init__(args)
            self.address = address
            self.want = want
            self.got = got

        def __str__(self):
            """Print exception string"""
            label_str = ""
            if self.address.label is not None:
                label_str = f" ({self.address.label})"
            return (
                f"unexpected nonce for account {self.address}{label_str}: "
                + f"want {self.want}, got {self.got}"
            )

    @dataclass(kw_only=True)
    class BalanceMismatch(Exception):
        """
        Test expected a certain balance for an account but a different
        value was found.
        """

        address: Address
        want: int | None
        got: int | None

        def __init__(self, address: Address, want: int | None, got: int | None, *args):
            super().__init__(args)
            self.address = address
            self.want = want
            self.got = got

        def __str__(self):
            """Print exception string"""
            label_str = ""
            if self.address.label is not None:
                label_str = f" ({self.address.label})"
            return (
                f"unexpected balance for account {self.address}{label_str}: "
                + f"want {self.want}, got {self.got}"
            )

    @dataclass(kw_only=True)
    class CodeMismatch(Exception):
        """
        Test expected a certain bytecode for an account but a different
        one was found.
        """

        address: Address
        want: bytes | None
        got: bytes | None

        def __init__(self, address: Address, want: bytes | None, got: bytes | None, *args):
            super().__init__(args)
            self.address = address
            self.want = want
            self.got = got

        def __str__(self):
            """Print exception string"""
            label_str = ""
            if self.address.label is not None:
                label_str = f" ({self.address.label})"
            return (
                f"unexpected code for account {self.address}{label_str}: "
                + f"want {self.want}, got {self.got}"
            )

    def check_alloc(self: "Account", address: Address, account: "Account"):
        """
        Checks the returned alloc against an expected account in post state.
        Raises exception on failure.
        """
        if "nonce" in self.model_fields_set:
            if self.nonce != account.nonce:
                raise Account.NonceMismatch(
                    address=address,
                    want=self.nonce,
                    got=account.nonce,
                )

        if "balance" in self.model_fields_set:
            if self.balance != account.balance:
                raise Account.BalanceMismatch(
                    address=address,
                    want=self.balance,
                    got=account.balance,
                )

        if "code" in self.model_fields_set:
            if self.code != account.code:
                raise Account.CodeMismatch(
                    address=address,
                    want=self.code,
                    got=account.code,
                )

        if "storage" in self.model_fields_set:
            self.storage.must_be_equal(address=address, other=account.storage)

    def __bool__(self: "Account") -> bool:
        """
        Returns True on a non-empty account.
        """
        return any((self.nonce, self.balance, self.code, self.storage))

    @classmethod
    def with_code(cls: Type, code: BytesConvertible) -> "Account":
        """
        Create account with provided `code` and nonce of `1`.
        """
        return Account(nonce=HexNumber(1), code=Bytes(code))

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
                return account.model_dump(exclude_unset=True)
            raise TypeError(f"Unexpected type for account merge: {type(account)}")

        kwargs = to_kwargs_dict(account_1)
        kwargs.update(to_kwargs_dict(account_2))

        return cls(**kwargs)


class EOA(Address):
    """
    An Externally Owned Account (EOA) is an account controlled by a private key.

    The EOA is defined by its address and (optionally) by its corresponding private key.
    """

    key: Hash | None
    nonce: Number

    def __new__(
        cls,
        address: "FixedSizeBytesConvertible | Address | EOA | None" = None,
        *,
        key: FixedSizeBytesConvertible | None = None,
        nonce: NumberConvertible = 0,
    ):
        """
        Init the EOA.
        """
        if address is None:
            if key is None:
                raise ValueError("impossible to initialize EOA without address")
            private_key = PrivateKey(Hash(key))
            public_key = private_key.public_key
            address = Address(keccak256(public_key.format(compressed=False)[1:])[32 - 20 :])
        elif isinstance(address, EOA):
            return address
        instance = super(EOA, cls).__new__(cls, address)
        instance.key = Hash(key) if key is not None else None
        instance.nonce = Number(nonce)
        return instance

    def get_nonce(self) -> Number:
        """
        Returns the current nonce of the EOA and increments it by one.
        """
        nonce = self.nonce
        self.nonce = Number(nonce + 1)
        return nonce

    def copy(self) -> "EOA":
        """
        Returns a copy of the EOA.
        """
        return EOA(Address(self), key=self.key, nonce=self.nonce)


@cache
def eoa_by_index(i: int) -> EOA:
    """
    Returns an EOA by index.
    """
    return EOA(key=TestPrivateKey + i if i != 1 else TestPrivateKey2, nonce=0)


def eoa_iterator() -> Iterator[EOA]:
    """
    Returns an iterator over EOAs copies.
    """
    return iter(eoa_by_index(i).copy() for i in count())


def contract_address_iterator(
    start_address: int = 0x1000, increments: int = 0x100
) -> Iterator[Address]:
    """
    Returns an iterator over contract addresses.
    """
    return iter(Address(start_address + (i * increments)) for i in count())


class AllocMode(IntEnum):
    """
    Allocation mode for the state.
    """

    PERMISSIVE = 0
    STRICT = 1


class Alloc(RootModel[Dict[Address, Account | None]]):
    """
    Allocation of accounts in the state, pre and post test execution.
    """

    root: Dict[Address, Account | None] = Field(default_factory=dict, validate_default=True)

    _alloc_mode: AllocMode = PrivateAttr(default=AllocMode.PERMISSIVE)
    _contract_address_iterator: Iterator[Address] = PrivateAttr(
        default_factory=contract_address_iterator
    )
    _eoa_iterator: Iterator[EOA] = PrivateAttr(default_factory=eoa_iterator)

    @dataclass(kw_only=True)
    class UnexpectedAccount(Exception):
        """
        Unexpected account found in the allocation.
        """

        address: Address
        account: Account | None

        def __init__(self, address: Address, account: Account | None, *args):
            super().__init__(args)
            self.address = address
            self.account = account

        def __str__(self):
            """Print exception string"""
            return f"unexpected account in allocation {self.address}: {self.account}"

    @dataclass(kw_only=True)
    class MissingAccount(Exception):
        """
        Expected account not found in the allocation.
        """

        address: Address

        def __init__(self, address: Address, *args):
            super().__init__(args)
            self.address = address

        def __str__(self):
            """Print exception string"""
            return f"Account missing from allocation {self.address}"

    @classmethod
    def merge(cls, alloc_1: "Alloc", alloc_2: "Alloc") -> "Alloc":
        """
        Returns the merged allocation of two sources.
        """
        merged = alloc_1.model_dump()

        for address, other_account in alloc_2.root.items():
            merged_account = Account.merge(merged.get(address, None), other_account)
            if merged_account:
                merged[address] = merged_account
            elif address in merged:
                merged.pop(address, None)

        return Alloc(merged)

    def __iter__(self):
        """
        Returns an iterator over the allocation.
        """
        return iter(self.root)

    def __getitem__(self, address: Address | FixedSizeBytesConvertible) -> Account | None:
        """
        Returns the account associated with an address.
        """
        if not isinstance(address, Address):
            address = Address(address)
        return self.root[address]

    def __setitem__(self, address: Address | FixedSizeBytesConvertible, account: Account | None):
        """
        Sets the account associated with an address.
        """
        if not isinstance(address, Address):
            address = Address(address)
        self.root[address] = account

    def __delitem__(self, address: Address | FixedSizeBytesConvertible):
        """
        Deletes the account associated with an address.
        """
        if not isinstance(address, Address):
            address = Address(address)
        self.root.pop(address, None)

    def __eq__(self, other) -> bool:
        """
        Returns True if both allocations are equal.
        """
        if not isinstance(other, Alloc):
            return False
        return self.root == other.root

    def __contains__(self, address: Address | FixedSizeBytesConvertible) -> bool:
        """
        Checks if an account is in the allocation.
        """
        if not isinstance(address, Address):
            address = Address(address)
        return address in self.root

    def empty_accounts(self) -> List[Address]:
        """
        Returns a list of addresses of empty accounts.
        """
        return [address for address, account in self.root.items() if not account]

    def state_root(self) -> bytes:
        """
        Returns the state root of the allocation.
        """
        state = State()
        for address, account in self.root.items():
            if account is None:
                continue
            set_account(
                state=state,
                address=FrontierAddress(address),
                account=FrontierAccount(
                    nonce=Uint(account.nonce) if account.nonce is not None else Uint(0),
                    balance=(U256(account.balance) if account.balance is not None else U256(0)),
                    code=account.code if account.code is not None else b"",
                ),
            )
            if account.storage is not None:
                for key, value in account.storage.root.items():
                    set_storage(
                        state=state,
                        address=FrontierAddress(address),
                        key=Hash(key),
                        value=U256(value),
                    )
        return state_root(state)

    def verify_post_alloc(self, got_alloc: "Alloc"):
        """
        Verify that the allocation matches the expected post in the test.
        Raises exception on unexpected values.
        """
        assert isinstance(got_alloc, Alloc), f"got_alloc is not an Alloc: {got_alloc}"
        for address, account in self.root.items():
            if account is None:
                # Account must not exist
                if address in got_alloc.root and got_alloc.root[address] is not None:
                    raise Alloc.UnexpectedAccount(address, got_alloc.root[address])
            else:
                if address in got_alloc.root:
                    got_account = got_alloc.root[address]
                    assert isinstance(got_account, Account)
                    assert isinstance(account, Account)
                    account.check_alloc(address, got_account)
                else:
                    raise Alloc.MissingAccount(address)

    def deploy_contract(
        self,
        code: BytesConvertible,
        *,
        storage: Storage
        | Dict[StorageKeyValueTypeConvertible, StorageKeyValueTypeConvertible] = {},
        balance: NumberConvertible = 0,
        nonce: NumberConvertible = 1,
        address: Address | None = None,
        label: str | None = None,
    ) -> Address:
        """
        Deploy a contract to the allocation.

        Warning: `address` parameter is a temporary solution to allow tests to hard-code the
        contract address. Do NOT use in new tests as it will be removed in the future!
        """
        if address is not None:
            assert self._alloc_mode == AllocMode.PERMISSIVE, "address parameter is not supported"
            assert address not in self, f"address {address} already in allocation"
            contract_address = address
        else:
            contract_address = next(self._contract_address_iterator)

        if self._alloc_mode == AllocMode.STRICT:
            assert Number(nonce) >= 1, "impossible to deploy contract with nonce lower than one"

        self[contract_address] = Account(
            nonce=nonce,
            balance=balance,
            code=code,
            storage=storage,
        )
        if label is None:
            # Try to deduce the label from the code
            frame = inspect.currentframe()
            if frame is not None:
                caller_frame = frame.f_back
                if caller_frame is not None:
                    code_context = inspect.getframeinfo(caller_frame).code_context
                    if code_context is not None:
                        line = code_context[0].strip()
                        if "=" in line:
                            label = line.split("=")[0].strip()

        contract_address.label = label
        return contract_address

    def fund_eoa(self, amount: NumberConvertible = 10**21, label: str | None = None) -> EOA:
        """
        Add a previously unused EOA to the pre-alloc with the balance specified by `amount`.
        """
        eoa = next(self._eoa_iterator)
        self[eoa] = Account(
            nonce=0,
            balance=amount,
        )
        return eoa

    def fund_address(self, address: Address, amount: NumberConvertible):
        """
        Fund an address with a given amount.

        If the address is already present in the pre-alloc the amount will be
        added to its existing balance.
        """
        if address in self:
            account = self[address]
            if account is not None:
                current_balance = account.balance or 0
                account.balance = ZeroPaddedHexNumber(current_balance + Number(amount))
                return

        self[address] = Account(balance=amount)


class WithdrawalGeneric(CamelModel, Generic[NumberBoundTypeVar]):
    """
    Withdrawal generic type, used as a parent class for `Withdrawal` and `FixtureWithdrawal`.
    """

    index: NumberBoundTypeVar
    validator_index: NumberBoundTypeVar
    address: Address
    amount: NumberBoundTypeVar

    def to_serializable_list(self) -> List[Any]:
        """
        Returns a list of the withdrawal's attributes in the order they should
        be serialized.
        """
        return [
            Uint(self.index),
            Uint(self.validator_index),
            self.address,
            Uint(self.amount),
        ]

    @staticmethod
    def list_root(withdrawals: Sequence["WithdrawalGeneric"]) -> bytes:
        """
        Returns the withdrawals root of a list of withdrawals.
        """
        t = HexaryTrie(db={})
        for i, w in enumerate(withdrawals):
            t.set(eth_rlp.encode(Uint(i)), eth_rlp.encode(w.to_serializable_list()))
        return t.root_hash


class Withdrawal(WithdrawalGeneric[HexNumber]):
    """
    Withdrawal type
    """

    pass


DEFAULT_BASE_FEE = 7


class EnvironmentGeneric(CamelModel, Generic[NumberBoundTypeVar]):
    """
    Used as a parent class for `Environment` and `FixtureEnvironment`.
    """

    fee_recipient: Address = Field(
        Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba"),
        alias="currentCoinbase",
    )
    gas_limit: NumberBoundTypeVar = Field(
        100_000_000_000_000_000, alias="currentGasLimit"
    )  # type: ignore
    number: NumberBoundTypeVar = Field(1, alias="currentNumber")  # type: ignore
    timestamp: NumberBoundTypeVar = Field(1_000, alias="currentTimestamp")  # type: ignore
    prev_randao: NumberBoundTypeVar | None = Field(None, alias="currentRandom")
    difficulty: NumberBoundTypeVar | None = Field(None, alias="currentDifficulty")
    base_fee_per_gas: NumberBoundTypeVar | None = Field(None, alias="currentBaseFee")
    excess_blob_gas: NumberBoundTypeVar | None = Field(None, alias="currentExcessBlobGas")

    parent_difficulty: NumberBoundTypeVar | None = Field(None)
    parent_timestamp: NumberBoundTypeVar | None = Field(None)
    parent_base_fee_per_gas: NumberBoundTypeVar | None = Field(None, alias="parentBaseFee")
    parent_gas_used: NumberBoundTypeVar | None = Field(None)
    parent_gas_limit: NumberBoundTypeVar | None = Field(None)


class Environment(EnvironmentGeneric[Number]):
    """
    Structure used to keep track of the context in which a block
    must be executed.
    """

    blob_gas_used: Number | None = Field(None, alias="currentBlobGasUsed")
    parent_ommers_hash: Hash = Field(Hash(0), alias="parentUncleHash")
    parent_blob_gas_used: Number | None = Field(None)
    parent_excess_blob_gas: Number | None = Field(None)
    parent_beacon_block_root: Hash | None = Field(None)

    block_hashes: Dict[Number, Hash] = Field(default_factory=dict)
    ommers: List[Hash] = Field(default_factory=list)
    withdrawals: List[Withdrawal] | None = Field(None)
    extra_data: Bytes = Field(Bytes(b"\x00"), exclude=True)

    @computed_field  # type: ignore[misc]
    @cached_property
    def parent_hash(self) -> Hash | None:
        """
        Obtains the latest hash according to the highest block number in
        `block_hashes`.
        """
        if len(self.block_hashes) == 0:
            return None

        last_index = max(self.block_hashes.keys())
        return Hash(self.block_hashes[last_index])

    def set_fork_requirements(self, fork: Fork) -> "Environment":
        """
        Fills the required fields in an environment depending on the fork.
        """
        number = self.number
        timestamp = self.timestamp

        updated_values: Dict[str, Any] = {}

        if fork.header_prev_randao_required(number, timestamp) and self.prev_randao is None:
            updated_values["prev_randao"] = 0

        if fork.header_withdrawals_required(number, timestamp) and self.withdrawals is None:
            updated_values["withdrawals"] = []

        if (
            fork.header_base_fee_required(number, timestamp)
            and self.base_fee_per_gas is None
            and self.parent_base_fee_per_gas is None
        ):
            updated_values["base_fee_per_gas"] = DEFAULT_BASE_FEE

        if fork.header_zero_difficulty_required(number, timestamp):
            updated_values["difficulty"] = 0
        elif self.difficulty is None and self.parent_difficulty is None:
            updated_values["difficulty"] = 0x20000

        if (
            fork.header_excess_blob_gas_required(number, timestamp)
            and self.excess_blob_gas is None
            and self.parent_excess_blob_gas is None
        ):
            updated_values["excess_blob_gas"] = 0

        if (
            fork.header_blob_gas_used_required(number, timestamp)
            and self.blob_gas_used is None
            and self.parent_blob_gas_used is None
        ):
            updated_values["blob_gas_used"] = 0

        if (
            fork.header_beacon_root_required(number, timestamp)
            and self.parent_beacon_block_root is None
        ):
            updated_values["parent_beacon_block_root"] = 0

        return self.copy(**updated_values)


class AccessList(CamelModel):
    """
    Access List for transactions.
    """

    address: Address
    storage_keys: List[Hash]

    def to_list(self) -> List[Address | List[Hash]]:
        """
        Returns the access list as a list of serializable elements.
        """
        return [self.address, self.storage_keys]


class TransactionGeneric(BaseModel, Generic[NumberBoundTypeVar]):
    """
    Generic transaction type used as a parent for Transaction and FixtureTransaction (blockchain).
    """

    ty: NumberBoundTypeVar = Field(0, alias="type")  # type: ignore
    chain_id: NumberBoundTypeVar = Field(1)  # type: ignore
    nonce: NumberBoundTypeVar = Field(0)  # type: ignore
    gas_price: NumberBoundTypeVar | None = None
    max_priority_fee_per_gas: NumberBoundTypeVar | None = None
    max_fee_per_gas: NumberBoundTypeVar | None = None
    gas_limit: NumberBoundTypeVar = Field(21_000)  # type: ignore
    to: Address | None = None
    value: NumberBoundTypeVar = Field(0)  # type: ignore
    data: Bytes = Field(Bytes(b""))
    access_list: List[AccessList] | None = None
    max_fee_per_blob_gas: NumberBoundTypeVar | None = None
    blob_versioned_hashes: Sequence[Hash] | None = None

    v: NumberBoundTypeVar | None = None
    r: NumberBoundTypeVar | None = None
    s: NumberBoundTypeVar | None = None
    sender: EOA | None = None


class TransactionFixtureConverter(CamelModel):
    """
    Handler for serializing and validating the `to` field as an empty string.
    """

    @model_validator(mode="before")
    @classmethod
    def validate_to_as_empty_string(cls, data: Any) -> Any:
        """
        If the `to` field is an empty string, set the model value to None.
        """
        if isinstance(data, dict) and "to" in data and data["to"] == "":
            data["to"] = None
        return data

    @model_serializer(mode="wrap", when_used="json-unless-none")
    def serialize_to_as_empty_string(self, serializer):
        """
        Serialize the `to` field as the empty string if the model value is None.
        """
        default = serializer(self)
        if default is not None and "to" not in default:
            default["to"] = ""
        return default


class TransactionTransitionToolConverter(CamelModel):
    """
    Handler for serializing and validating the `to` field as an empty string.
    """

    @model_validator(mode="before")
    @classmethod
    def validate_to_as_empty_string(cls, data: Any) -> Any:
        """
        If the `to` field is an empty string, set the model value to None.
        """
        if isinstance(data, dict) and "to" in data and data["to"] == "":
            data["to"] = None
        return data

    @model_serializer(mode="wrap", when_used="json-unless-none")
    def serialize_to_as_none(self, serializer):
        """
        Serialize the `to` field as `None` if the model value is None.

        This is required as we use `exclude_none=True` when serializing, but the
        t8n tool explicitly requires a value of `None` (respectively null), for
        if the `to` field should be unset (contract creation).
        """
        default = serializer(self)
        if default is not None and "to" not in default:
            default["to"] = None
        return default


class Transaction(TransactionGeneric[HexNumber], TransactionTransitionToolConverter):
    """
    Generic object that can represent all Ethereum transaction types.
    """

    gas_limit: HexNumber = Field(HexNumber(21_000), serialization_alias="gas")
    to: Address | None = Field(Address(0xAA))
    data: Bytes = Field(Bytes(b""), alias="input")

    secret_key: Hash | None = None
    error: List[TransactionException] | TransactionException | None = Field(None, exclude=True)

    protected: bool = Field(True, exclude=True)
    rlp_override: bytes | None = Field(None, exclude=True)

    wrapped_blob_transaction: bool = Field(False, exclude=True)
    blobs: Sequence[Bytes] | None = Field(None, exclude=True)
    blob_kzg_commitments: Sequence[Bytes] | None = Field(None, exclude=True)
    blob_kzg_proofs: Sequence[Bytes] | None = Field(None, exclude=True)

    model_config = ConfigDict(validate_assignment=True)

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

    def model_post_init(self, __context):
        """
        Ensures the transaction has no conflicting properties.
        """
        super().model_post_init(__context)

        if self.gas_price is not None and (
            self.max_fee_per_gas is not None
            or self.max_priority_fee_per_gas is not None
            or self.max_fee_per_blob_gas is not None
        ):
            raise Transaction.InvalidFeePayment()

        if "ty" not in self.model_fields_set:
            # Try to deduce transaction type from included fields
            if self.max_fee_per_blob_gas is not None or self.blob_kzg_commitments is not None:
                self.ty = 3
            elif self.max_fee_per_gas is not None or self.max_priority_fee_per_gas is not None:
                self.ty = 2
            elif self.access_list is not None:
                self.ty = 1
            else:
                self.ty = 0

        if self.v is not None and self.secret_key is not None:
            raise Transaction.InvalidSignaturePrivateKey()

        if self.v is None and self.secret_key is None:
            if self.sender is not None:
                self.secret_key = self.sender.key
            else:
                self.secret_key = Hash(TestPrivateKey)
                self.sender = EOA(address=TestAddress, key=self.secret_key, nonce=0)

        # Set default values for fields that are required for certain tx types
        if self.ty <= 1 and self.gas_price is None:
            self.gas_price = 10
        if self.ty >= 1 and self.access_list is None:
            self.access_list = []

        if self.ty >= 2 and self.max_fee_per_gas is None:
            self.max_fee_per_gas = 7
        if self.ty >= 2 and self.max_priority_fee_per_gas is None:
            self.max_priority_fee_per_gas = 0

        if self.ty == 3 and self.max_fee_per_blob_gas is None:
            self.max_fee_per_blob_gas = 1

        if "nonce" not in self.model_fields_set and self.sender is not None:
            self.nonce = HexNumber(self.sender.get_nonce())

    def with_error(
        self, error: List[TransactionException] | TransactionException
    ) -> "Transaction":
        """
        Create a copy of the transaction with an added error.
        """
        return self.copy(error=error)

    def with_nonce(self, nonce: int) -> "Transaction":
        """
        Create a copy of the transaction with a modified nonce.
        """
        return self.copy(nonce=nonce)

    def with_signature_and_sender(self, *, keep_secret_key: bool = False) -> "Transaction":
        """
        Returns a signed version of the transaction using the private key.
        """
        updated_values: Dict[str, Any] = {}

        if self.v is not None:
            # Transaction already signed
            if self.sender is not None:
                return self

            public_key = PublicKey.from_signature_and_message(
                self.signature_bytes, keccak256(self.signing_bytes), hasher=None
            )
            updated_values["sender"] = Address(
                keccak256(public_key.format(compressed=False)[1:])[32 - 20 :]
            )
            return self.copy(**updated_values)

        if self.secret_key is None:
            raise ValueError("secret_key must be set to sign a transaction")

        # Get the signing bytes
        signing_hash = keccak256(self.signing_bytes)

        # Sign the bytes
        signature_bytes = PrivateKey(secret=self.secret_key).sign_recoverable(
            signing_hash, hasher=None
        )
        public_key = PublicKey.from_signature_and_message(
            signature_bytes, signing_hash, hasher=None
        )

        sender = keccak256(public_key.format(compressed=False)[1:])[32 - 20 :]
        updated_values["sender"] = Address(sender)

        v, r, s = (
            signature_bytes[64],
            int.from_bytes(signature_bytes[0:32], byteorder="big"),
            int.from_bytes(signature_bytes[32:64], byteorder="big"),
        )
        if self.ty == 0:
            if self.protected:
                v += 35 + (self.chain_id * 2)
            else:  # not protected
                v += 27

        updated_values["v"] = HexNumber(v)
        updated_values["r"] = HexNumber(r)
        updated_values["s"] = HexNumber(s)

        updated_values["secret_key"] = None

        updated_tx = self.model_copy(update=updated_values)

        # Remove the secret key if requested
        if keep_secret_key:
            updated_tx.secret_key = self.secret_key
        return updated_tx

    @cached_property
    def signing_envelope(self) -> List[Any]:
        """
        Returns the list of values included in the envelope used for signing.
        """
        to = self.to if self.to else bytes()
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
            return [
                Uint(self.chain_id),
                Uint(self.nonce),
                Uint(self.max_priority_fee_per_gas),
                Uint(self.max_fee_per_gas),
                Uint(self.gas_limit),
                to,
                Uint(self.value),
                self.data,
                [a.to_list() for a in self.access_list],
                Uint(self.max_fee_per_blob_gas),
                list(self.blob_versioned_hashes),
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
                self.data,
                [a.to_list() for a in self.access_list],
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
                self.data,
                [a.to_list() for a in self.access_list],
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
                    self.data,
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
                    self.data,
                ]
        raise NotImplementedError("signing for transaction type {self.ty} not implemented")

    @cached_property
    def payload_body(self) -> List[Any]:
        """
        Returns the list of values included in the transaction body.
        """
        if self.v is None or self.r is None or self.s is None:
            raise ValueError("signature must be set before serializing any tx type")

        signing_envelope = self.signing_envelope

        if self.ty == 0 and self.protected:
            # Remove the chain_id and the two zeros from the signing envelope
            signing_envelope = signing_envelope[:-3]
        elif self.ty == 3 and self.wrapped_blob_transaction:
            # EIP-4844: https://eips.ethereum.org/EIPS/eip-4844
            if self.blobs is None:
                raise ValueError("blobs must be set for type 3 tx")
            if self.blob_kzg_commitments is None:
                raise ValueError("blob_kzg_commitments must be set for type 3 tx")
            if self.blob_kzg_proofs is None:
                raise ValueError("blob_kzg_proofs must be set for type 3 tx")
            return [
                signing_envelope + [Uint(self.v), Uint(self.r), Uint(self.s)],
                list(self.blobs),
                list(self.blob_kzg_commitments),
                list(self.blob_kzg_proofs),
            ]

        return signing_envelope + [Uint(self.v), Uint(self.r), Uint(self.s)]

    @cached_property
    def rlp(self) -> bytes:
        """
        Returns bytes of the serialized representation of the transaction,
        which is almost always RLP encoding.
        """
        if self.rlp_override is not None:
            return self.rlp_override
        if self.ty > 0:
            return bytes([self.ty]) + eth_rlp.encode(self.payload_body)
        else:
            return eth_rlp.encode(self.payload_body)

    @cached_property
    def signing_bytes(self) -> bytes:
        """
        Returns the serialized bytes of the transaction used for signing.
        """
        return (
            bytes([self.ty]) + eth_rlp.encode(self.signing_envelope)
            if self.ty > 0
            else eth_rlp.encode(self.signing_envelope)
        )

    @cached_property
    def signature_bytes(self) -> bytes:
        """
        Returns the serialized bytes of the transaction signature.
        """
        assert self.v is not None and self.r is not None and self.s is not None
        v = int(self.v)
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

    @cached_property
    def serializable_list(self) -> Any:
        """
        Returns the list of values included in the transaction as a serializable object.
        """
        return self.rlp if self.ty > 0 else self.payload_body

    @staticmethod
    def list_root(input_txs: List["Transaction"]) -> Hash:
        """
        Returns the transactions root of a list of transactions.
        """
        t = HexaryTrie(db={})
        for i, tx in enumerate(input_txs):
            t.set(eth_rlp.encode(Uint(i)), tx.rlp)
        return Hash(t.root_hash)

    @staticmethod
    def list_blob_versioned_hashes(input_txs: List["Transaction"]) -> List[Hash]:
        """
        Gets a list of ordered blob versioned hashes from a list of transactions.
        """
        return [
            blob_versioned_hash
            for tx in input_txs
            if tx.blob_versioned_hashes is not None
            for blob_versioned_hash in tx.blob_versioned_hashes
        ]

    @cached_property
    def created_contract(self) -> Address:
        """
        Returns the address of the contract created by the transaction.
        """
        if self.to is not None:
            raise ValueError("transaction is not a contract creation")
        nonce_bytes = (
            bytes() if self.nonce == 0 else self.nonce.to_bytes(length=1, byteorder="big")
        )
        hash = keccak256(eth_rlp.encode([self.sender, nonce_bytes]))
        return Address(hash[-20:])


class RequestBase:
    """
    Base class for requests.
    """

    @classmethod
    def type_byte(cls) -> bytes:
        """
        Returns the request type.
        """
        raise NotImplementedError("request_type must be implemented in child classes")

    def to_serializable_list(self) -> List[Any]:
        """
        Returns the request's attributes as a list of serializable elements.
        """
        raise NotImplementedError("to_serializable_list must be implemented in child classes")


class DepositRequestGeneric(RequestBase, CamelModel, Generic[NumberBoundTypeVar]):
    """
    Generic deposit type used as a parent for DepositRequest and FixtureDepositRequest.
    """

    pubkey: BLSPublicKey
    withdrawal_credentials: Hash
    amount: NumberBoundTypeVar
    signature: BLSSignature
    index: NumberBoundTypeVar

    @classmethod
    def type_byte(cls) -> bytes:
        """
        Returns the deposit request type.
        """
        return b"\0"

    def to_serializable_list(self) -> List[Any]:
        """
        Returns the deposit's attributes as a list of serializable elements.
        """
        return [
            self.pubkey,
            self.withdrawal_credentials,
            Uint(self.amount),
            self.signature,
            Uint(self.index),
        ]


class DepositRequest(DepositRequestGeneric[HexNumber]):
    """
    Deposit Request type
    """

    pass


class WithdrawalRequestGeneric(RequestBase, CamelModel, Generic[NumberBoundTypeVar]):
    """
    Generic withdrawal request type used as a parent for WithdrawalRequest and
    FixtureWithdrawalRequest.
    """

    source_address: Address = Address(0)
    validator_public_key: BLSPublicKey
    amount: NumberBoundTypeVar

    @classmethod
    def type_byte(cls) -> bytes:
        """
        Returns the withdrawal request type.
        """
        return b"\1"

    def to_serializable_list(self) -> List[Any]:
        """
        Returns the deposit's attributes as a list of serializable elements.
        """
        return [
            self.source_address,
            self.validator_public_key,
            Uint(self.amount),
        ]


class WithdrawalRequest(WithdrawalRequestGeneric[HexNumber]):
    """
    Withdrawal Request type
    """

    pass


class Requests(RootModel[List[DepositRequest | WithdrawalRequest]]):
    """
    Requests for the transition tool.
    """

    root: List[DepositRequest | WithdrawalRequest] = Field(default_factory=list)

    def to_serializable_list(self) -> List[Any]:
        """
        Returns the requests as a list of serializable elements.
        """
        return [r.type_byte() + eth_rlp.encode(r.to_serializable_list()) for r in self.root]

    @cached_property
    def trie_root(self) -> Hash:
        """
        Returns the root hash of the requests.
        """
        t = HexaryTrie(db={})
        for i, r in enumerate(self.root):
            t.set(
                eth_rlp.encode(Uint(i)),
                r.type_byte() + eth_rlp.encode(r.to_serializable_list()),
            )
        return Hash(t.root_hash)

    def deposit_requests(self) -> List[DepositRequest]:
        """
        Returns the list of deposit requests.
        """
        return [d for d in self.root if isinstance(d, DepositRequest)]

    def withdrawal_requests(self) -> List[WithdrawalRequest]:
        """
        Returns the list of withdrawal requests.
        """
        return [w for w in self.root if isinstance(w, WithdrawalRequest)]


# TODO: Move to other file
# Transition tool models


class TransactionLog(CamelModel):
    """
    Transaction log
    """

    address: Address
    topics: List[Hash]
    data: Bytes
    block_number: HexNumber
    transaction_hash: Hash
    transaction_index: HexNumber
    block_hash: Hash
    log_index: HexNumber
    removed: bool


class TransactionReceipt(CamelModel):
    """
    Transaction receipt
    """

    transaction_hash: Hash
    gas_used: HexNumber
    root: Bytes | None = None
    status: HexNumber | None = None
    cumulative_gas_used: HexNumber | None = None
    logs_bloom: Bloom | None = None
    logs: List[TransactionLog] | None = None
    contract_address: Address | None = None
    effective_gas_price: HexNumber | None = None
    block_hash: Hash | None = None
    transaction_index: HexNumber | None = None
    blob_gas_used: HexNumber | None = None
    blob_gas_price: HexNumber | None = None


class RejectedTransaction(CamelModel):
    """
    Rejected transaction
    """

    index: HexNumber
    error: str


class Result(CamelModel):
    """
    Result of a t8n
    """

    state_root: Hash
    ommers_hash: Hash | None = Field(None, validation_alias="sha3Uncles")
    transactions_trie: Hash = Field(..., alias="txRoot")
    receipts_root: Hash
    logs_hash: Hash
    logs_bloom: Bloom
    receipts: List[TransactionReceipt]
    rejected_transactions: List[RejectedTransaction] = Field(
        default_factory=list, alias="rejected"
    )
    difficulty: HexNumber | None = Field(None, alias="currentDifficulty")
    gas_used: HexNumber
    base_fee_per_gas: HexNumber | None = Field(None, alias="currentBaseFee")
    withdrawals_root: Hash | None = None
    excess_blob_gas: HexNumber | None = Field(None, alias="currentExcessBlobGas")
    blob_gas_used: HexNumber | None = None
    requests_root: Hash | None = None
    deposit_requests: List[DepositRequest] | None = None
    withdrawal_requests: List[WithdrawalRequest] | None = None


class TransitionToolOutput(CamelModel):
    """
    Transition tool output
    """

    alloc: Alloc
    result: Result
