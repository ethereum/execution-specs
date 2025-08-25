"""Account-related types for Ethereum tests."""

import json
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Literal, Optional, Self, Tuple

from coincurve.keys import PrivateKey
from ethereum_types.bytes import Bytes20
from ethereum_types.numeric import U256, Bytes32, Uint
from pydantic import PrivateAttr

from ethereum_test_base_types import (
    Account,
    Address,
    Hash,
    Number,
    Storage,
    StorageRootType,
)
from ethereum_test_base_types import Alloc as BaseAlloc
from ethereum_test_base_types.conversions import (
    BytesConvertible,
    FixedSizeBytesConvertible,
    NumberConvertible,
)
from ethereum_test_vm import EVMCodeType

from .trie import EMPTY_TRIE_ROOT, FrontierAccount, Trie, root, trie_get, trie_set
from .utils import keccak256

FrontierAddress = Bytes20


@dataclass
class State:
    """Contains all information that is preserved between transactions."""

    _main_trie: Trie[Bytes20, Optional[FrontierAccount]] = field(
        default_factory=lambda: Trie(secured=True, default=None)
    )
    _storage_tries: Dict[Bytes20, Trie[Bytes32, U256]] = field(default_factory=dict)
    _snapshots: List[
        Tuple[
            Trie[Bytes20, Optional[FrontierAccount]],
            Dict[Bytes20, Trie[Bytes32, U256]],
        ]
    ] = field(default_factory=list)


def set_account(state: State, address: Bytes20, account: Optional[FrontierAccount]) -> None:
    """
    Set the `Account` object at an address. Setting to `None` deletes
    the account (but not its storage, see `destroy_account()`).
    """
    trie_set(state._main_trie, address, account)


def set_storage(state: State, address: Bytes20, key: Bytes32, value: U256) -> None:
    """
    Set a value at a storage key on an account. Setting to `U256(0)` deletes
    the key.
    """
    assert trie_get(state._main_trie, address) is not None

    trie = state._storage_tries.get(address)
    if trie is None:
        trie = Trie(secured=True, default=U256(0))
        state._storage_tries[address] = trie
    trie_set(trie, key, value)
    if trie._data == {}:
        del state._storage_tries[address]


def storage_root(state: State, address: Bytes20) -> Bytes32:
    """Calculate the storage root of an account."""
    assert not state._snapshots
    if address in state._storage_tries:
        return root(state._storage_tries[address])
    else:
        return EMPTY_TRIE_ROOT


def state_root(state: State) -> Bytes32:
    """Calculate the state root."""
    assert not state._snapshots

    def get_storage_root(address: Bytes20) -> Bytes32:
        return storage_root(state, address)

    return root(state._main_trie, get_storage_root=get_storage_root)


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
        """Init the EOA."""
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
        """Return current nonce of the EOA and increments it by one."""
        nonce = self.nonce
        self.nonce = Number(nonce + 1)
        return nonce

    def copy(self) -> Self:
        """Return copy of the EOA."""
        return self.__class__(Address(self), key=self.key, nonce=self.nonce)


class Alloc(BaseAlloc):
    """Allocation of accounts in the state, pre and post test execution."""

    _eoa_fund_amount_default: int = PrivateAttr(10**21)

    @dataclass(kw_only=True)
    class UnexpectedAccountError(Exception):
        """Unexpected account found in the allocation."""

        address: Address
        account: Account | None

        def __str__(self):
            """Print exception string."""
            return f"unexpected account in allocation {self.address}: {self.account}"

    @dataclass(kw_only=True)
    class MissingAccountError(Exception):
        """Expected account not found in the allocation."""

        address: Address

        def __str__(self):
            """Print exception string."""
            return f"Account missing from allocation {self.address}"

    @dataclass(kw_only=True)
    class CollisionError(Exception):
        """Different accounts at the same address."""

        address: Address
        account_1: Account | None
        account_2: Account | None

        def to_json(self) -> Dict[str, Any]:
            """Dump to json object."""
            return {
                "address": self.address.hex(),
                "account_1": self.account_1.model_dump(mode="json")
                if self.account_1 is not None
                else None,
                "account_2": self.account_2.model_dump(mode="json")
                if self.account_2 is not None
                else None,
            }

        @classmethod
        def from_json(cls, obj: Dict[str, Any]) -> Self:
            """Parse from a json dict."""
            return cls(
                address=Address(obj["address"]),
                account_1=Account.model_validate(obj["account_1"])
                if obj["account_1"] is not None
                else None,
                account_2=Account.model_validate(obj["account_2"])
                if obj["account_2"] is not None
                else None,
            )

        def __str__(self) -> str:
            """Print exception string."""
            return (
                "Overlapping key defining different accounts detected:\n"
                f"{json.dumps(self.to_json(), indent=2)}"
            )

    class KeyCollisionMode(Enum):
        """Mode for handling key collisions when merging allocations."""

        ERROR = auto()
        OVERWRITE = auto()
        ALLOW_IDENTICAL_ACCOUNTS = auto()

    @classmethod
    def merge(
        cls,
        alloc_1: "Alloc",
        alloc_2: "Alloc",
        key_collision_mode: KeyCollisionMode = KeyCollisionMode.OVERWRITE,
    ) -> "Alloc":
        """Return merged allocation of two sources."""
        overlapping_keys = alloc_1.root.keys() & alloc_2.root.keys()
        if overlapping_keys:
            if key_collision_mode == cls.KeyCollisionMode.ERROR:
                raise Exception(
                    f"Overlapping keys detected: {[key.hex() for key in overlapping_keys]}"
                )
            elif key_collision_mode == cls.KeyCollisionMode.ALLOW_IDENTICAL_ACCOUNTS:
                # The overlapping keys must point to the exact same account
                for key in overlapping_keys:
                    account_1 = alloc_1[key]
                    account_2 = alloc_2[key]
                    if account_1 != account_2:
                        raise Alloc.CollisionError(
                            address=key,
                            account_1=account_1,
                            account_2=account_2,
                        )
        merged = alloc_1.model_dump()

        for address, other_account in alloc_2.root.items():
            merged_account = Account.merge(merged.get(address, None), other_account)
            if merged_account:
                merged[address] = merged_account
            elif address in merged:
                merged.pop(address, None)

        return Alloc(merged)

    def __iter__(self):
        """Return iterator over the allocation."""
        return iter(self.root)

    def items(self):
        """Return iterator over the allocation items."""
        return self.root.items()

    def __getitem__(self, address: Address | FixedSizeBytesConvertible) -> Account | None:
        """Return account associated with an address."""
        if not isinstance(address, Address):
            address = Address(address)
        return self.root[address]

    def __setitem__(self, address: Address | FixedSizeBytesConvertible, account: Account | None):
        """Set account associated with an address."""
        if not isinstance(address, Address):
            address = Address(address)
        self.root[address] = account

    def __delitem__(self, address: Address | FixedSizeBytesConvertible):
        """Delete account associated with an address."""
        if not isinstance(address, Address):
            address = Address(address)
        self.root.pop(address, None)

    def __eq__(self, other) -> bool:
        """Return True if both allocations are equal."""
        if not isinstance(other, Alloc):
            return False
        return self.root == other.root

    def __contains__(self, address: Address | FixedSizeBytesConvertible) -> bool:
        """Check if an account is in the allocation."""
        if not isinstance(address, Address):
            address = Address(address)
        return address in self.root

    def empty_accounts(self) -> List[Address]:
        """Return list of addresses of empty accounts."""
        return [address for address, account in self.root.items() if not account]

    def state_root(self) -> Hash:
        """Return state root of the allocation."""
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
                        key=Bytes32(Hash(key)),
                        value=U256(value),
                    )
        return Hash(state_root(state))

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
                    raise Alloc.UnexpectedAccountError(
                        address=address, account=got_alloc.root[address]
                    )
            else:
                if address in got_alloc.root:
                    got_account = got_alloc.root[address]
                    assert isinstance(got_account, Account)
                    assert isinstance(account, Account)
                    account.check_alloc(address, got_account)
                else:
                    raise Alloc.MissingAccountError(address=address)

    def deploy_contract(
        self,
        code: BytesConvertible,
        *,
        storage: Storage | StorageRootType | None = None,
        balance: NumberConvertible = 0,
        nonce: NumberConvertible = 1,
        address: Address | None = None,
        evm_code_type: EVMCodeType | None = None,
        label: str | None = None,
    ) -> Address:
        """Deploy a contract to the allocation."""
        raise NotImplementedError("deploy_contract is not implemented in the base class")

    def fund_eoa(
        self,
        amount: NumberConvertible | None = None,
        label: str | None = None,
        storage: Storage | None = None,
        delegation: Address | Literal["Self"] | None = None,
        nonce: NumberConvertible | None = None,
    ) -> EOA:
        """Add a previously unused EOA to the pre-alloc with the balance specified by `amount`."""
        raise NotImplementedError("fund_eoa is not implemented in the base class")

    def fund_address(self, address: Address, amount: NumberConvertible):
        """
        Fund an address with a given amount.

        If the address is already present in the pre-alloc the amount will be
        added to its existing balance.
        """
        raise NotImplementedError("fund_address is not implemented in the base class")

    def empty_account(self) -> Address:
        """
        Return a previously unused account guaranteed to be empty.

        This ensures the account has zero balance, zero nonce, no code, and no storage.
        The account is not a precompile or a system contract.
        """
        raise NotImplementedError("empty_account is not implemented in the base class")
