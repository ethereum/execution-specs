"""Shared pre-alloc functionality."""

from enum import IntFlag, auto
from typing import Any, Literal

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
from execution_testing.forks import Fork
from execution_testing.test_types import EOA
from execution_testing.test_types import Alloc as BaseAlloc


class AllocFlags(IntFlag):
    """Feature flags for allocation behavior."""

    NONE = 0
    ALLOW_ADDRESS_SET_TO_ACCOUNT = auto()
    ALLOW_DEPLOY_TO_HARDCODED_ADDRESS = auto()
    ALLOW_ZERO_NONCE_CONTRACTS = auto()
    ALLOW_EOA_WITH_CODE = auto()
    ALLOW_EOA_WITH_HARDCODED_NONCE = auto()
    ALLOW_FUND_ADDRESS = auto()

    MUTABLE = (
        ALLOW_ADDRESS_SET_TO_ACCOUNT
        | ALLOW_DEPLOY_TO_HARDCODED_ADDRESS
        | ALLOW_ZERO_NONCE_CONTRACTS
        | ALLOW_EOA_WITH_CODE
        | ALLOW_EOA_WITH_HARDCODED_NONCE
    )

    def is_mutable(self) -> bool:
        """Return whether the pre-alloc is mutable."""
        return bool(self & AllocFlags.MUTABLE)

    def incompatible_with_alloc_grouping(self) -> bool:
        """Return True if the restrictions allow pre-alloc grouping."""
        if (
            AllocFlags.ALLOW_ADDRESS_SET_TO_ACCOUNT in self
            or AllocFlags.ALLOW_DEPLOY_TO_HARDCODED_ADDRESS in self
            or AllocFlags.ALLOW_FUND_ADDRESS in self
        ):
            return True
        return False

    def assert_allow_account_address_set(self) -> None:
        """
        Raise an exception if the ALLOW_ADDRESS_SET_TO_ACCOUNT flag is not set.
        """
        if AllocFlags.ALLOW_ADDRESS_SET_TO_ACCOUNT not in self:
            raise ValueError(
                "Cannot set an account to an address (pre[a] = b) without "
                "proper marker. "
                "Use `pytest.mark.pre_address_set_to_account` to allow this."
            )
        return

    def assert_allow_deploy_to_hardcoded_address(self) -> None:
        """
        Raise an exception if the ALLOW_DEPLOY_TO_HARDCODED_ADDRESS flag is
        not set.
        """
        if AllocFlags.ALLOW_DEPLOY_TO_HARDCODED_ADDRESS not in self:
            raise ValueError(
                "Cannot deploy to hardcoded address without proper marker. "
                "Use `pytest.mark.pre_deploy_to_hardcoded_address` to allow "
                "this."
            )
        return

    def assert_allow_zero_nonce_contracts(self) -> None:
        """
        Raise an exception if the ALLOW_ZERO_NONCE_CONTRACTS flag is not set.
        """
        if AllocFlags.ALLOW_ZERO_NONCE_CONTRACTS not in self:
            raise ValueError(
                "Cannot deploy contracts with zero nonce without proper "
                "marker. "
                "Use `pytest.mark.pre_zero_nonce_contracts` to allow this."
            )
        return

    def assert_allow_fund_address(self) -> None:
        """Raise an exception if the ALLOW_FUND_ADDRESS flag is not set."""
        if AllocFlags.ALLOW_FUND_ADDRESS not in self:
            raise ValueError(
                "Cannot use pre.fund_address without proper marker. "
                "Use `pytest.mark.pre_fund_address` to allow this."
            )
        return

    def assert_allow_eoa_with_code(self) -> None:
        """Raise an exception if the ALLOW_EOA_WITH_CODE flag is not set."""
        if AllocFlags.ALLOW_EOA_WITH_CODE not in self:
            raise ValueError(
                "Cannot create EOAs with code without proper marker. "
                "Use `pytest.mark.pre_eoa_with_code` to allow this."
            )
        return

    def assert_allow_eoa_with_hardcoded_nonce(self) -> None:
        """
        Raise an exception if the ALLOW_EOA_WITH_HARDCODED_NONCE flag is not
        set.
        """
        if AllocFlags.ALLOW_EOA_WITH_HARDCODED_NONCE not in self:
            raise ValueError(
                "Cannot create EOAs with a hardcoded nonce without proper "
                "marker. "
                "Use `pytest.mark.pre_eoa_with_hardcoded_nonce` to allow this."
            )
        return

    def assert_mutable(self) -> None:
        """Raises an exception if the MUTABLE flag is not set."""
        if self.is_mutable():
            raise ValueError(
                "Cannot set items in immutable mode. "
                "Use `pytest.mark.pre_alloc_mutable` to allow mutable mode."
            )
        return


class Alloc(BaseAlloc):
    """
    Allocation subclass that enforces rules set by the allocation flags.
    """

    _fork: Fork = PrivateAttr()
    _flags: AllocFlags = PrivateAttr(AllocFlags.NONE)

    def __init__(
        self,
        *args: Any,
        fork: Fork,
        flags: AllocFlags,
        **kwargs: Any,
    ) -> None:
        """Initialize allocation with the given properties."""
        super().__init__(*args, **kwargs)
        self._fork = fork
        self._flags = flags

    def __setitem__(
        self,
        address: Address | FixedSizeBytesConvertible,
        account: Account | None,
    ) -> None:
        """Set account associated with an address."""
        self._flags.assert_allow_account_address_set()
        self.__internal_setitem__(address, account)

    def __internal_setitem__(
        self,
        address: Address | FixedSizeBytesConvertible,
        account: Account | None,
    ) -> None:
        """
        Set account associated with an address.

        Called by the pre-alloc implementation to set an account.
        """
        if not isinstance(address, Address):
            address = Address(address)
        self.root[address] = account

    def __delitem__(
        self, address: Address | FixedSizeBytesConvertible
    ) -> None:
        """Delete account associated with an address."""
        self._flags.assert_allow_account_address_set()
        self.__internal_delitem__(address)

    def __internal_delitem__(
        self,
        address: Address | FixedSizeBytesConvertible,
    ) -> None:
        """
        Delete account associated with an address.

        Called by the pre-alloc implementation to delete an account.
        """
        if not isinstance(address, Address):
            address = Address(address)
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
            self._flags.assert_allow_deploy_to_hardcoded_address()

        if Number(nonce) == 0:
            self._flags.assert_allow_zero_nonce_contracts()

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
            self._flags.assert_allow_eoa_with_code()

        if nonce is not None:
            self._flags.assert_allow_eoa_with_hardcoded_nonce()

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

        If the address is already present in the pre-alloc the amount will be
        added to its existing balance.

        Args:
            address: Address to fund
            amount: Amount to fund in Wei
            minimum_balance: If set to True, account will be checked to have a
                minimum balance of `amount` and only fund if the balance is
                insufficient

        """
        self._flags.assert_allow_fund_address()
        return self._fund_address(
            address=address,
            amount=amount,
            minimum_balance=minimum_balance,
        )

    def _fund_address(
        self,
        address: Address,
        amount: NumberConvertible,
        *,
        minimum_balance: bool,
    ) -> None:
        """
        Sub-class implementation of fund_address.
        """
        raise NotImplementedError(
            "_fund_address is not implemented in the base class"
        )

    def empty_account(self) -> Address:
        """
        Return a previously unused account guaranteed to be empty.

        This ensures the account has zero balance, zero nonce, no code, and no
        storage. The account is not a precompile or a system contract.
        """
        return self._empty_account()

    def _empty_account(self) -> Address:
        """
        Sub-class implementation of empty_account.
        """
        raise NotImplementedError(
            "_empty_account is not implemented in the base class"
        )
