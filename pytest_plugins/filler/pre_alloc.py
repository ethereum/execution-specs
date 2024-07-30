"""
Pre-alloc specifically conditioned for test filling.
"""

import inspect
from enum import IntEnum
from functools import cache
from itertools import count
from typing import Iterator

import pytest
from pydantic import PrivateAttr

from ethereum_test_base_types import (
    Account,
    Address,
    Number,
    Storage,
    StorageRootType,
    TestPrivateKey,
    TestPrivateKey2,
    ZeroPaddedHexNumber,
)
from ethereum_test_base_types.conversions import (
    BytesConvertible,
    FixedSizeBytesConvertible,
    NumberConvertible,
)
from ethereum_test_types import EOA
from ethereum_test_types import Alloc as BaseAlloc

CONTRACT_START_ADDRESS_DEFAULT = 0x1000
CONTRACT_ADDRESS_INCREMENTS_DEFAULT = 0x100


def pytest_addoption(parser: pytest.Parser):
    """
    Adds command-line options to pytest.
    """
    pre_alloc_group = parser.getgroup("pre_alloc", "Arguments defining pre-allocation behavior.")

    pre_alloc_group.addoption(
        "--strict-alloc",
        action="store_true",
        dest="strict_alloc",
        default=False,
        help=("[DEBUG ONLY] Disallows deploying a contract in a predefined address."),
    )
    pre_alloc_group.addoption(
        "--ca-start",
        "--contract-address-start",
        action="store",
        dest="test_contract_start_address",
        default=f"{CONTRACT_START_ADDRESS_DEFAULT}",
        type=str,
        help="The starting address from which tests will deploy contracts.",
    )
    pre_alloc_group.addoption(
        "--ca-incr",
        "--contract-address-increment",
        action="store",
        dest="test_contract_address_increments",
        default=f"{CONTRACT_ADDRESS_INCREMENTS_DEFAULT}",
        type=str,
        help="The address increment value to each deployed contract by a test.",
    )


class AllocMode(IntEnum):
    """
    Allocation mode for the state.
    """

    PERMISSIVE = 0
    STRICT = 1


class Alloc(BaseAlloc):
    """
    Allocation of accounts in the state, pre and post test execution.
    """

    _alloc_mode: AllocMode = PrivateAttr(...)
    _contract_address_iterator: Iterator[Address] = PrivateAttr(...)
    _eoa_iterator: Iterator[EOA] = PrivateAttr(...)

    def __init__(
        self,
        *args,
        alloc_mode: AllocMode,
        contract_address_iterator: Iterator[Address],
        eoa_iterator: Iterator[EOA],
        **kwargs,
    ):
        """
        Initializes the allocation with the given properties.
        """
        super().__init__(*args, **kwargs)
        self._alloc_mode = alloc_mode
        self._contract_address_iterator = contract_address_iterator
        self._eoa_iterator = eoa_iterator

    def __setitem__(self, address: Address | FixedSizeBytesConvertible, account: Account | None):
        """
        Sets the account associated with an address.
        """
        if self._alloc_mode == AllocMode.STRICT:
            raise ValueError("Cannot set items in strict mode")
        super().__setitem__(address, account)

    def deploy_contract(
        self,
        code: BytesConvertible,
        *,
        storage: Storage | StorageRootType = {},
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

        super().__setitem__(
            contract_address,
            Account(
                nonce=nonce,
                balance=balance,
                code=code,
                storage=storage,
            ),
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

        If amount is 0, nothing will be added to the pre-alloc but a new and unique EOA will be
        returned.
        """
        eoa = next(self._eoa_iterator)
        if Number(amount) > 0:
            super().__setitem__(
                eoa,
                Account(
                    nonce=0,
                    balance=amount,
                ),
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
        super().__setitem__(address, Account(balance=amount))


@pytest.fixture(scope="session")
def alloc_mode(request: pytest.FixtureRequest) -> AllocMode:
    """
    Returns the allocation mode for the tests.
    """
    if request.config.getoption("strict_alloc"):
        return AllocMode.STRICT
    return AllocMode.PERMISSIVE


@pytest.fixture(scope="session")
def contract_start_address(request: pytest.FixtureRequest) -> int:
    """
    Returns the starting address for contract deployment.
    """
    return int(request.config.getoption("test_contract_start_address"), 0)


@pytest.fixture(scope="session")
def contract_address_increments(request: pytest.FixtureRequest) -> int:
    """
    Returns the address increment for contract deployment.
    """
    return int(request.config.getoption("test_contract_address_increments"), 0)


@pytest.fixture(scope="function")
def contract_address_iterator(
    contract_start_address: int,
    contract_address_increments: int,
) -> Iterator[Address]:
    """
    Returns an iterator over contract addresses.
    """
    return iter(
        Address(contract_start_address + (i * contract_address_increments)) for i in count()
    )


@cache
def eoa_by_index(i: int) -> EOA:
    """
    Returns an EOA by index.
    """
    return EOA(key=TestPrivateKey + i if i != 1 else TestPrivateKey2, nonce=0)


@pytest.fixture(scope="function")
def eoa_iterator() -> Iterator[EOA]:
    """
    Returns an iterator over EOAs copies.
    """
    return iter(eoa_by_index(i).copy() for i in count())


@pytest.fixture(scope="function")
def pre(
    alloc_mode: AllocMode,
    contract_address_iterator: Iterator[Address],
    eoa_iterator: Iterator[EOA],
) -> Alloc:
    """
    Returns the default pre allocation for all tests (Empty alloc).
    """
    return Alloc(
        alloc_mode=alloc_mode,
        contract_address_iterator=contract_address_iterator,
        eoa_iterator=eoa_iterator,
    )
