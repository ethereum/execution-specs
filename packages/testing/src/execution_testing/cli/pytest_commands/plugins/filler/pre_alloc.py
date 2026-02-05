"""Pre-alloc specifically conditioned for test filling."""

import inspect
from enum import IntEnum
from functools import cache
from hashlib import sha256
from typing import Any, Dict, List, Literal

import pytest
from pydantic import PrivateAttr

from execution_testing.base_types import (
    Account,
    Address,
    Bytes,
    Hash,
    Number,
    Storage,
    StorageRootType,
    TestPrivateKey,
    TestPrivateKey2,
)
from execution_testing.base_types.conversions import (
    BytesConvertible,
    FixedSizeBytesConvertible,
    NumberConvertible,
)
from execution_testing.fixtures import LabeledFixtureFormat
from execution_testing.forks import Fork
from execution_testing.specs import BaseTest
from execution_testing.test_types import (
    DETERMINISTIC_FACTORY_ADDRESS,
    DETERMINISTIC_FACTORY_BYTECODE,
    EOA,
    compute_deterministic_create2_address,
)
from execution_testing.test_types import Alloc as BaseAlloc
from execution_testing.tools import Initcode

CONTRACT_START_ADDRESS_DEFAULT = 0x1000000000000000000000000000000000001000
CONTRACT_ADDRESS_INCREMENTS_DEFAULT = 0x100


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options to pytest."""
    pre_alloc_group = parser.getgroup(
        "pre_alloc",
        "Arguments defining pre-allocation behavior during test filling.",
    )

    pre_alloc_group.addoption(
        "--strict-alloc",
        action="store_true",
        dest="strict_alloc",
        default=False,
        help=(
            "[DEBUG ONLY] Disallows deploying a contract in a predefined "
            "address."
        ),
    )
    pre_alloc_group.addoption(
        "--ca-start",
        "--contract-address-start",
        action="store",
        dest="test_contract_start_address",
        default=f"{CONTRACT_START_ADDRESS_DEFAULT}",
        type=str,
        help="Starting address from which tests will deploy contracts.",
    )
    pre_alloc_group.addoption(
        "--ca-incr",
        "--contract-address-increment",
        action="store",
        dest="test_contract_address_increments",
        default=f"{CONTRACT_ADDRESS_INCREMENTS_DEFAULT}",
        type=str,
        help="Address increment value for each deployed contract by a test.",
    )


class AllocMode(IntEnum):
    """Allocation mode for the state."""

    PERMISSIVE = 0
    STRICT = 1


DELEGATION_DESIGNATION = b"\xef\x01\x00"
EMPTY_ACCOUNT_HASH = Account().hash()


def contract_address_from_account(account_hash: Hash, salt: int) -> Address:
    """
    Calculate a deterministic address for a contract given the properties of
    the account.

    Useful to not duplicate accounts in the pre-allocation when grouping
    many tests.
    """
    return Address(
        Bytes(account_hash + salt.to_bytes(64, "big")).sha256()[12:]
    )


def eoa_from_account(account_hash: Hash, salt: int) -> EOA:
    """
    Calculate a deterministic EOA for a contract given the properties of
    the account.

    Useful to not duplicate accounts in the pre-allocation when grouping
    many tests.
    """
    return EOA(key=Bytes(account_hash + salt.to_bytes(64, "big")).sha256())


class Alloc(BaseAlloc):
    """Allocation of accounts in the state, pre and post test execution."""

    _eoa_fund_amount_default: int = PrivateAttr(10**21)
    _alloc_mode: AllocMode = PrivateAttr()
    _account_salt: Dict[Hash, int] = PrivateAttr()
    _fork: Fork = PrivateAttr()

    def __init__(
        self,
        *args: Any,
        alloc_mode: AllocMode,
        fork: Fork,
        **kwargs: Any,
    ) -> None:
        """Initialize allocation with the given properties."""
        super().__init__(*args, **kwargs)
        self._alloc_mode = alloc_mode
        self._account_salt = {}
        self._fork = fork

    def __setitem__(
        self,
        address: Address | FixedSizeBytesConvertible,
        account: Account | None,
    ) -> None:
        """Set account associated with an address."""
        if self._alloc_mode == AllocMode.STRICT:
            raise ValueError("Cannot set items in strict mode")
        super().__setitem__(address, account)

    def get_next_account_salt(self, account_hash: Hash) -> int:
        """Retrieve the next salt for this account."""
        salt = self._account_salt.get(account_hash, 0)
        self._account_salt[account_hash] = salt + 1
        return salt

    def code_pre_processor(self, code: BytesConvertible) -> BytesConvertible:
        """Pre-processes the code before setting it."""
        return code

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
        """
        if not isinstance(deploy_code, Bytes):
            deploy_code = Bytes(deploy_code)
        if initcode is None:
            initcode = Initcode(deploy_code=deploy_code)
        elif not isinstance(initcode, Bytes):
            initcode = Bytes(initcode)
        if storage is None:
            storage = {}
        salt = Hash(salt)
        contract_address = compute_deterministic_create2_address(
            salt=salt, initcode=initcode, fork=self._fork
        )
        if contract_address in self:
            raise ValueError(
                f"contract address already in pre-alloc: {contract_address}"
            )
        max_code_size = self._fork.max_code_size()
        if len(deploy_code) > max_code_size:
            raise ValueError(
                f"code too large: {len(deploy_code)} > {max_code_size}"
            )

        fork_deterministic_factory_address = (
            self._fork.deterministic_factory_predeploy_address()
        )
        if (
            fork_deterministic_factory_address is None
            and DETERMINISTIC_FACTORY_ADDRESS not in self
        ):
            super().__setitem__(
                DETERMINISTIC_FACTORY_ADDRESS,
                Account(
                    nonce=1,
                    code=DETERMINISTIC_FACTORY_BYTECODE,
                    storage={},
                ),
            )

        super().__setitem__(
            contract_address,
            Account(
                nonce=1,
                code=deploy_code,
                storage=storage,
            ),
        )
        if label is None:
            # Try to deduce the label from the code
            frame = inspect.currentframe()
            if frame is not None:
                caller_frame = frame.f_back
                if caller_frame is not None:
                    code_context = inspect.getframeinfo(
                        caller_frame
                    ).code_context
                    if code_context is not None:
                        line = code_context[0].strip()
                        if "=" in line:
                            label = line.split("=")[0].strip()

        contract_address.label = label
        return contract_address

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
        del stub

        if storage is None:
            storage = {}
        if address is not None:
            assert self._alloc_mode == AllocMode.PERMISSIVE, (
                "address parameter is not supported"
            )

        if self._alloc_mode == AllocMode.STRICT:
            assert Number(nonce) >= 1, (
                "impossible to deploy contract with nonce lower than one"
            )

        code = self.code_pre_processor(code)
        code_bytes = (
            bytes(code) if not isinstance(code, (bytes, str)) else code
        )
        max_code_size = self._fork.max_code_size()
        assert len(code_bytes) <= max_code_size, (
            f"code too large: {len(code_bytes)} > {max_code_size}"
        )

        account = Account(
            nonce=nonce,
            balance=balance,
            code=code,
            storage=storage,
        )

        if address is not None:
            assert address not in self, (
                f"address {address} already in allocation"
            )
            contract_address = address
        else:
            account_hash = account.hash()
            salt = self.get_next_account_salt(account_hash)
            contract_address = contract_address_from_account(
                account_hash, salt
            )

        super().__setitem__(contract_address, account)
        if label is None:
            # Try to deduce the label from the code
            frame = inspect.currentframe()
            if frame is not None:
                caller_frame = frame.f_back
                if caller_frame is not None:
                    code_context = inspect.getframeinfo(
                        caller_frame
                    ).code_context
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
        del label

        if amount is None:
            amount = self._eoa_fund_amount_default
        if (
            Number(amount) > 0
            or storage is not None
            or code is not None
            or delegation is not None
            or (nonce is not None and Number(nonce) > 0)
        ):
            if code is not None and delegation is not None:
                raise Exception(
                    "code and delegation cannot be set at the same time"
                )
            if storage is None and delegation is None:
                nonce = Number(0 if nonce is None else nonce)
                account = Account(
                    nonce=nonce,
                    balance=amount,
                )
            else:
                # Type-4 transaction is sent to the EOA to set the storage, so
                # the nonce must be 1
                code = b""
                if delegation is not None:
                    if (
                        not isinstance(delegation, Address)
                        and delegation == "Self"
                    ):
                        # This is a placeholder value, since we don't know
                        # the address until the end of the function.
                        code = DELEGATION_DESIGNATION + b"Self"
                    else:
                        code = DELEGATION_DESIGNATION + delegation
                elif code is not None:
                    code = Bytes(code)
                # If delegation is None but storage is not, realistically the
                # nonce should be 2 because the account must have delegated to
                # set the storage and then again to reset the delegation (but
                # can be overridden by the test for a non-realistic scenario)
                real_nonce = 2 if delegation is None else 1
                nonce = Number(real_nonce if nonce is None else nonce)
                account = Account(
                    nonce=nonce,
                    balance=amount,
                    storage=storage if storage is not None else {},
                    code=code,
                )

        else:
            account = Account()

        account_hash = account.hash()
        salt = self.get_next_account_salt(account_hash)
        eoa = eoa_from_account(account_hash, salt)

        if account.nonce > 0:
            eoa.nonce = account.nonce

        if not isinstance(delegation, Address) and delegation == "Self":
            account = account.copy(code=DELEGATION_DESIGNATION + eoa)
        if account:
            super().__setitem__(eoa, account)
        return eoa

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
        """
        del minimum_balance
        if address in self:
            raise Exception(
                "Cannot fund an account already in state. "
                "Use the appropriate `amount`, `balance` arguments "
                "when creating the account."
            )
        super().__setitem__(address, Account(balance=amount))

    def empty_account(self) -> Address:
        """
        Add a previously unused account guaranteed to be empty to the
        pre-alloc.

        This ensures the account has:
        - Zero balance
        - Zero nonce
        - No code
        - No storage

        This is different from precompiles or system contracts. The function
        does not send any transactions, ensuring that the account remains
        "empty."

        Returns:
            Address: The address of the created empty account.

        """
        salt = self.get_next_account_salt(EMPTY_ACCOUNT_HASH)
        return Address(eoa_from_account(EMPTY_ACCOUNT_HASH, salt))


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


def sha256_from_string(s: str) -> int:
    """Return SHA-256 hash of a string."""
    return int.from_bytes(sha256(s.encode("utf-8")).digest(), "big")


ALL_FIXTURE_FORMAT_NAMES: List[str] = []

for spec in BaseTest.spec_types.values():
    for labeled_fixture_format in spec.supported_fixture_formats:
        name = (
            labeled_fixture_format.label
            if isinstance(labeled_fixture_format, LabeledFixtureFormat)
            else labeled_fixture_format.format_name.lower()
        )
        if name not in ALL_FIXTURE_FORMAT_NAMES:
            ALL_FIXTURE_FORMAT_NAMES.append(name)

# Sort by length, from longest to shortest, since some fixture format names
# contain others so we are always sure to catch the longest one first.
ALL_FIXTURE_FORMAT_NAMES.sort(key=len, reverse=True)


@pytest.fixture(scope="function")
def node_id_for_entropy(
    request: pytest.FixtureRequest, fork: Fork | None
) -> str:
    """
    Return the node id with the fixture format name and fork name stripped.

    Used in cases where we are filling for pre-alloc groups, and we take the
    name of the test as source of entropy to get a deterministic address when
    generating the pre-alloc grouping.

    Removing the fixture format and the fork name from the node id before
    hashing results in the contracts and senders addresses being the same
    across fixture types and forks for the same test.
    """
    node_id: str = request.node.nodeid
    if fork is None:
        # FIXME: Static tests don't have a fork, so we need to get it from the
        # node.
        assert hasattr(request.node, "fork")
        fork = request.node.fork
    for fixture_format_name in ALL_FIXTURE_FORMAT_NAMES:
        if fixture_format_name in node_id:
            parts = request.node.nodeid.split("::")
            test_file_path = parts[0]
            test_name = "::".join(parts[1:])
            stripped_test_name = test_name.replace(
                fixture_format_name, ""
            ).replace(fork.name(), "")
            return f"{test_file_path}::{stripped_test_name}"
    raise Exception(f"Fixture format name not found in test {node_id}")


@cache
def eoa_by_index(i: int) -> EOA:
    """Return EOA by index."""
    return EOA(key=TestPrivateKey + i if i != 1 else TestPrivateKey2, nonce=0)


@pytest.fixture(scope="function")
def pre(
    alloc_mode: AllocMode,
    fork: Fork | None,
    request: pytest.FixtureRequest,
) -> Alloc:
    """Return default pre allocation for all tests (Empty alloc)."""
    # FIXME: Static tests don't have a fork so we need to get it from the node.
    actual_fork = fork
    if actual_fork is None:
        assert hasattr(request.node, "fork")
        actual_fork = request.node.fork

    return Alloc(
        alloc_mode=alloc_mode,
        fork=actual_fork,
    )
