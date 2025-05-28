"""Account-related types for Ethereum tests."""

from dataclasses import dataclass
from typing import List, Literal

from coincurve.keys import PrivateKey
from ethereum.frontier.fork_types import Account as FrontierAccount
from ethereum.frontier.fork_types import Address as FrontierAddress
from ethereum.frontier.state import State, set_account, set_storage, state_root
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

from .utils import keccak256


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

    def copy(self) -> "EOA":
        """Return copy of the EOA."""
        return EOA(Address(self), key=self.key, nonce=self.nonce)


class Alloc(BaseAlloc):
    """Allocation of accounts in the state, pre and post test execution."""

    _eoa_fund_amount_default: int = PrivateAttr(10**21)

    @dataclass(kw_only=True)
    class UnexpectedAccountError(Exception):
        """Unexpected account found in the allocation."""

        address: Address
        account: Account | None

        def __init__(self, address: Address, account: Account | None, *args):
            """Initialize the exception."""
            super().__init__(args)
            self.address = address
            self.account = account

        def __str__(self):
            """Print exception string."""
            return f"unexpected account in allocation {self.address}: {self.account}"

    @dataclass(kw_only=True)
    class MissingAccountError(Exception):
        """Expected account not found in the allocation."""

        address: Address

        def __init__(self, address: Address, *args):
            """Initialize the exception."""
            super().__init__(args)
            self.address = address

        def __str__(self):
            """Print exception string."""
            return f"Account missing from allocation {self.address}"

    @classmethod
    def merge(cls, alloc_1: "Alloc", alloc_2: "Alloc") -> "Alloc":
        """Return merged allocation of two sources."""
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

    def state_root(self) -> bytes:
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
                    raise Alloc.UnexpectedAccountError(address, got_alloc.root[address])
            else:
                if address in got_alloc.root:
                    got_account = got_alloc.root[address]
                    assert isinstance(got_account, Account)
                    assert isinstance(account, Account)
                    account.check_alloc(address, got_account)
                else:
                    raise Alloc.MissingAccountError(address)

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
