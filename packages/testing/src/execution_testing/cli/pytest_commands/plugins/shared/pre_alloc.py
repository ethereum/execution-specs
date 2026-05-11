"""Shared pre-alloc functionality."""

from enum import IntFlag, auto
from typing import Any, Dict, Literal, Set

from pydantic import PrivateAttr

from execution_testing.base_types import (
    Account,
    Address,
    Hash,
    Number,
    Storage,
    StorageRootType,
)
from execution_testing.base_types.conversions import (
    BytesConvertible,
    FixedSizeBytesConvertible,
    NumberConvertible,
)
from execution_testing.forks import Fork, TransitionFork
from execution_testing.test_types import EOA
from execution_testing.test_types import Alloc as BaseAlloc


class AllocFlags(IntFlag):
    """Feature flags for allocation behavior."""

    NONE = 0
    MUTABLE = auto()


class Alloc(BaseAlloc):
    """
    Allocation subclass that enforces rules set by the allocation flags.
    """

    _fork: Fork | TransitionFork = PrivateAttr()
    _flags: AllocFlags = PrivateAttr(AllocFlags.NONE)
    _set_addresses: Set[Address] = PrivateAttr(default_factory=set)
    _deleted_addresses: Set[Address] = PrivateAttr(default_factory=set)
    _pre_funded_addresses: Set[Address] = PrivateAttr(default_factory=set)
    _hardcoded_addresses_deployed_to: Set[Address] = PrivateAttr(
        default_factory=set
    )
    _stub_eoas: Dict[str, EOA] = PrivateAttr(default_factory=dict)

    def is_mutable(self) -> bool:
        """Return whether the pre-alloc is mutable."""
        return bool(self._flags & AllocFlags.MUTABLE)

    def assert_mutable(self) -> None:
        """Raises an exception if the MUTABLE flag is not set."""
        if not self.is_mutable():
            raise ValueError(
                "Cannot set items in immutable mode. "
                "Use `pytest.mark.pre_alloc_mutable` to allow mutable mode."
            )
        return

    def __init__(
        self,
        *args: Any,
        fork: Fork,
        flags: AllocFlags,
        stub_eoas: Dict[str, EOA] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize allocation with the given properties."""
        super().__init__(*args, **kwargs)
        self._fork = fork
        self._flags = flags
        if stub_eoas is not None:
            self._stub_eoas = stub_eoas

    def stub_eoa(self, label: str) -> EOA:
        """Return the EOA for a key-bearing stub."""
        if label not in self._stub_eoas:
            raise ValueError(
                f"Stub EOA '{label}' not found. "
                "Provide --address-stubs with a pkey entry."
            )
        return self._stub_eoas[label].copy()

    def __setitem__(
        self,
        address: Address | FixedSizeBytesConvertible,
        account: Account | None,
    ) -> None:
        """Set account associated with an address."""
        self.assert_mutable()
        if not isinstance(address, Address):
            address = Address(address)
        self._set_addresses.add(address)
        self.__internal_setitem__(address, account)

    def __internal_setitem__(
        self,
        address: Address,
        account: Account | None,
    ) -> None:
        """
        Set account associated with an address.

        Called by the pre-alloc implementation to set an account.
        """
        self.root[address] = account

    def __delitem__(
        self, address: Address | FixedSizeBytesConvertible
    ) -> None:
        """Delete account associated with an address."""
        self.assert_mutable()
        if not isinstance(address, Address):
            address = Address(address)
        self._deleted_addresses.add(address)
        self.__internal_delitem__(address)

    def __internal_delitem__(
        self,
        address: Address,
    ) -> None:
        """
        Delete account associated with an address.

        Called by the pre-alloc implementation to delete an account.
        """
        self.root.pop(address, None)

    def deterministic_deploy_contract(
        self,
        *,
        deploy_code: BytesConvertible,
        salt: Hash | int = 0,
        initcode: BytesConvertible | None = None,
        storage: Storage | StorageRootType | None = None,
        label: str | None = None,
    ) -> Address:
        """
        Deploy a contract to the allocation at a deterministic location
        using a deterministic deployment proxy.

        The initcode is not executed during test filling; it is executed only
        when the tests run on live networks. Therefore, if the initcode
        performs modifications to the storage, these must be specified using
        the `storage` parameter.

        Args:
            deploy_code: Contract code to deploy.
            salt: Salt to use for deterministic deployment.
            initcode: Initcode to use for deterministic deployment.
                      If `None`, the initcode is derived from `deploy_code`.
            storage: The expected storage state of the deployed contract after
                     initcode execution.
            label: Label to use for the contract.

        """
        return self._deterministic_deploy_contract(
            deploy_code=deploy_code,
            salt=salt,
            initcode=initcode,
            storage=storage,
            label=label,
        )

    def _deterministic_deploy_contract(
        self,
        *,
        deploy_code: BytesConvertible,
        salt: Hash | int,
        initcode: BytesConvertible | None,
        storage: Storage | StorageRootType | None,
        label: str | None,
    ) -> Address:
        """
        Sub-class implementation of deterministic contract deployment.
        """
        raise NotImplementedError(
            "_deterministic_deploy_contract is not implemented in the base "
            "class"
        )

    def deploy_contract(
        self,
        code: BytesConvertible,
        *,
        storage: Storage | StorageRootType | None = None,
        balance: NumberConvertible = 0,
        nonce: NumberConvertible = 1,
        address: Address | None = None,
        label: str | None = None,
        stub: str | None = None,
    ) -> Address:
        """
        Deploy a contract to the allocation.

        Warning: `address` parameter is a temporary solution to allow tests to
        hard-code the contract address. Do NOT use in new tests as it will be
        removed in the future!
        """
        if address is not None:
            self.assert_mutable()
            self._hardcoded_addresses_deployed_to.add(Address(address))

        if Number(nonce) == 0:
            self.assert_mutable()

        return self._deploy_contract(
            code=code,
            storage=storage,
            balance=balance,
            nonce=nonce,
            address=address,
            label=label,
            stub=stub,
        )

    def _deploy_contract(
        self,
        code: BytesConvertible,
        *,
        storage: Storage | StorageRootType | None,
        balance: NumberConvertible,
        nonce: NumberConvertible,
        address: Address | None,
        label: str | None,
        stub: str | None,
    ) -> Address:
        """
        Sub-class implementation of deploy_contract.
        """
        raise NotImplementedError(
            "_deploy_contract is not implemented in the base class"
        )

    def fund_eoa(
        self,
        amount: NumberConvertible | None = None,
        label: str | None = None,
        storage: Storage | None = None,
        code: BytesConvertible | None = None,
        delegation: Address | Literal["Self"] | None = None,
        nonce: NumberConvertible | None = None,
    ) -> EOA:
        """
        Add a previously unused EOA to the pre-alloc with the balance specified
        by `amount`.

        If amount is 0, nothing will be added to the pre-alloc but a new and
        unique EOA will be returned.
        """
        if code is not None:
            self.assert_mutable()

        if nonce is not None:
            self.assert_mutable()

        return self._fund_eoa(
            amount=amount,
            label=label,
            storage=storage,
            code=code,
            delegation=delegation,
            nonce=nonce,
        )

    def _fund_eoa(
        self,
        amount: NumberConvertible | None,
        label: str | None,
        storage: Storage | None,
        code: BytesConvertible | None,
        delegation: Address | Literal["Self"] | None,
        nonce: NumberConvertible | None,
    ) -> EOA:
        """
        Sub-class implementation of fund_eoa.
        """
        raise NotImplementedError(
            "_fund_eoa is not implemented in the base class"
        )

    def fund_address(
        self,
        address: Address,
        amount: NumberConvertible,
        *,
        minimum_balance: bool = False,
    ) -> None:
        """
        Fund an address with a given amount.

        Add a funded account to the pre-allocation.
        The address must not already exist in the pre-allocation. To set the
        balance of an account, use the `amount` parameter in `fund_eoa()` or
        the `balance` parameter in `deploy_contract()` at creation time.

        Args:
            address: Address to fund
            amount: Amount to fund in Wei
            minimum_balance: If set to True, account will be checked to have a
                minimum balance of `amount` and only fund if the balance is
                insufficient

        """
        if address in self:
            raise Exception(
                "Cannot fund an account already in state. "
                "Use the appropriate `amount`, `balance` arguments "
                "when creating the account."
            )
        self._pre_funded_addresses.add(address)
        return self._fund_address(
            address=address,
            amount=int(Number(amount)),
            minimum_balance=minimum_balance,
        )

    def _fund_address(
        self,
        address: Address,
        amount: int,
        *,
        minimum_balance: bool,
    ) -> None:
        """
        Sub-class implementation of fund_address.
        """
        raise NotImplementedError(
            "_fund_address is not implemented in the base class"
        )

    def nonexistent_account(self) -> Address:
        """
        Return the address of a previously unused nonexistent account.

        The address is guaranteed to not be a precompile or a system contract.
        No account is created — it remains nonexistent in the pre-state.
        """
        return self._nonexistent_account()

    def _nonexistent_account(self) -> Address:
        """
        Sub-class implementation of nonexistent_account.
        """
        raise NotImplementedError(
            "_nonexistent_account is not implemented in the base class"
        )
