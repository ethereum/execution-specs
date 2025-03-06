"""Pre-alloc specifically conditioned for test filling."""

import inspect
from enum import IntEnum
from functools import cache
from itertools import count
from typing import Iterator, Literal

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
from ethereum_test_types.eof.v1 import Container
from ethereum_test_vm import Bytecode, EVMCodeType, Opcodes

CONTRACT_START_ADDRESS_DEFAULT = 0x1000
CONTRACT_ADDRESS_INCREMENTS_DEFAULT = 0x100


def pytest_addoption(parser: pytest.Parser):
    """Add command-line options to pytest."""
    pre_alloc_group = parser.getgroup(
        "pre_alloc", "Arguments defining pre-allocation behavior during test filling."
    )

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
    pre_alloc_group.addoption(
        "--evm-code-type",
        action="store",
        dest="evm_code_type",
        default=None,
        type=EVMCodeType,
        choices=list(EVMCodeType),
        help="Type of EVM code to deploy in each test by default.",
    )


class AllocMode(IntEnum):
    """Allocation mode for the state."""

    PERMISSIVE = 0
    STRICT = 1


DELEGATION_DESIGNATION = b"\xef\x01\x00"


class Alloc(BaseAlloc):
    """Allocation of accounts in the state, pre and post test execution."""

    _alloc_mode: AllocMode = PrivateAttr()
    _contract_address_iterator: Iterator[Address] = PrivateAttr()
    _eoa_iterator: Iterator[EOA] = PrivateAttr()
    _evm_code_type: EVMCodeType | None = PrivateAttr(None)

    def __init__(
        self,
        *args,
        alloc_mode: AllocMode,
        contract_address_iterator: Iterator[Address],
        eoa_iterator: Iterator[EOA],
        evm_code_type: EVMCodeType | None = None,
        **kwargs,
    ):
        """Initialize allocation with the given properties."""
        super().__init__(*args, **kwargs)
        self._alloc_mode = alloc_mode
        self._contract_address_iterator = contract_address_iterator
        self._eoa_iterator = eoa_iterator
        self._evm_code_type = evm_code_type

    def __setitem__(self, address: Address | FixedSizeBytesConvertible, account: Account | None):
        """Set account associated with an address."""
        if self._alloc_mode == AllocMode.STRICT:
            raise ValueError("Cannot set items in strict mode")
        super().__setitem__(address, account)

    def code_pre_processor(
        self, code: BytesConvertible, *, evm_code_type: EVMCodeType | None
    ) -> BytesConvertible:
        """Pre-processes the code before setting it."""
        if evm_code_type is None:
            evm_code_type = self._evm_code_type
        if evm_code_type == EVMCodeType.EOF_V1:
            if not isinstance(code, Container):
                if isinstance(code, Bytecode) and not code.terminating:
                    return Container.Code(code + Opcodes.STOP)
                return Container.Code(code)
        return code

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
        """
        Deploy a contract to the allocation.

        Warning: `address` parameter is a temporary solution to allow tests to hard-code the
        contract address. Do NOT use in new tests as it will be removed in the future!
        """
        if storage is None:
            storage = {}
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
                code=self.code_pre_processor(code, evm_code_type=evm_code_type),
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

    def fund_eoa(
        self,
        amount: NumberConvertible | None = None,
        label: str | None = None,
        storage: Storage | None = None,
        delegation: Address | Literal["Self"] | None = None,
        nonce: NumberConvertible | None = None,
    ) -> EOA:
        """
        Add a previously unused EOA to the pre-alloc with the balance specified by `amount`.

        If amount is 0, nothing will be added to the pre-alloc but a new and unique EOA will be
        returned.
        """
        eoa = next(self._eoa_iterator)
        if amount is None:
            amount = self._eoa_fund_amount_default
        if (
            Number(amount) > 0
            or storage is not None
            or delegation is not None
            or (nonce is not None and Number(nonce) > 0)
        ):
            if storage is None and delegation is None:
                nonce = Number(0 if nonce is None else nonce)
                account = Account(
                    nonce=nonce,
                    balance=amount,
                )
                if nonce > 0:
                    eoa.nonce = nonce
            else:
                # Type-4 transaction is sent to the EOA to set the storage, so the nonce must be 1
                if not isinstance(delegation, Address) and delegation == "Self":
                    delegation = eoa
                # If delegation is None but storage is not, realistically the nonce should be 2
                # because the account must have delegated to set the storage and then again to
                # reset the delegation (but can be overridden by the test for a non-realistic
                # scenario)
                real_nonce = 2 if delegation is None else 1
                nonce = Number(real_nonce if nonce is None else nonce)
                account = Account(
                    nonce=nonce,
                    balance=amount,
                    storage=storage if storage is not None else {},
                    code=DELEGATION_DESIGNATION + bytes(delegation)  # type: ignore
                    if delegation is not None
                    else b"",
                )
                eoa.nonce = nonce

            super().__setitem__(eoa, account)
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
    """Return allocation mode for the tests."""
    if request.config.getoption("strict_alloc"):
        return AllocMode.STRICT
    return AllocMode.PERMISSIVE


@pytest.fixture(scope="session")
def contract_start_address(request: pytest.FixtureRequest) -> int:
    """Return starting address for contract deployment."""
    return int(request.config.getoption("test_contract_start_address"), 0)


@pytest.fixture(scope="session")
def contract_address_increments(request: pytest.FixtureRequest) -> int:
    """Return address increment for contract deployment."""
    return int(request.config.getoption("test_contract_address_increments"), 0)


@pytest.fixture(scope="function")
def contract_address_iterator(
    contract_start_address: int,
    contract_address_increments: int,
) -> Iterator[Address]:
    """Return iterator over contract addresses."""
    return iter(
        Address(contract_start_address + (i * contract_address_increments)) for i in count()
    )


@cache
def eoa_by_index(i: int) -> EOA:
    """Return EOA by index."""
    return EOA(key=TestPrivateKey + i if i != 1 else TestPrivateKey2, nonce=0)


@pytest.fixture(scope="function")
def eoa_iterator() -> Iterator[EOA]:
    """Return iterator over EOAs copies."""
    return iter(eoa_by_index(i).copy() for i in count())


@pytest.fixture(autouse=True)
def evm_code_type(request: pytest.FixtureRequest) -> EVMCodeType:
    """Return default EVM code type for all tests (LEGACY)."""
    parameter_evm_code_type = request.config.getoption("evm_code_type")
    if parameter_evm_code_type is not None:
        assert type(parameter_evm_code_type) is EVMCodeType, "Invalid EVM code type"
        return parameter_evm_code_type
    return EVMCodeType.LEGACY


@pytest.fixture(scope="function")
def pre(
    alloc_mode: AllocMode,
    contract_address_iterator: Iterator[Address],
    eoa_iterator: Iterator[EOA],
    evm_code_type: EVMCodeType,
) -> Alloc:
    """Return default pre allocation for all tests (Empty alloc)."""
    return Alloc(
        alloc_mode=alloc_mode,
        contract_address_iterator=contract_address_iterator,
        eoa_iterator=eoa_iterator,
        evm_code_type=evm_code_type,
    )
