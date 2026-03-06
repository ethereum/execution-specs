"""Pre-alloc specifically conditioned for test filling."""

import hashlib
import inspect
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
    NumberConvertible,
)
from execution_testing.fixtures import LabeledFixtureFormat
from execution_testing.forks import Fork, TransitionFork
from execution_testing.specs import BaseTest
from execution_testing.test_types import (
    DETERMINISTIC_FACTORY_ADDRESS,
    DETERMINISTIC_FACTORY_BYTECODE,
    EOA,
    Environment,
    compute_deterministic_create2_address,
    contract_address_from_hash,
    eoa_from_hash,
)
from execution_testing.tools import Initcode

from ..shared.pre_alloc import Alloc as SharedAlloc
from ..shared.pre_alloc import AllocFlags


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options to pytest."""
    pre_alloc_group = parser.getgroup(
        "pre_alloc",
        "Arguments defining pre-allocation behavior during test filling.",
    )

    # No options for now
    del pre_alloc_group


DELEGATION_DESIGNATION = b"\xef\x01\x00"
EMPTY_ACCOUNT_HASH = Account().hash()


class Alloc(SharedAlloc):
    """Allocation of accounts in the state, pre and post test execution."""

    _eoa_fund_amount_default: int = PrivateAttr(10**21)
    _account_salt: Dict[Hash, int] = PrivateAttr(default_factory=dict)

    def __init__(
        self, *args: Any, fork: Fork, flags: AllocFlags, **kwargs: Any
    ) -> None:
        """Initialize the pre-alloc."""
        super().__init__(*args, fork=fork, flags=flags, **kwargs)

    def get_next_account_salt(self, account_hash: Hash) -> int:
        """Retrieve the next salt for this account."""
        salt = self._account_salt.get(account_hash, 0)
        self._account_salt[account_hash] = salt + 1
        return salt

    def code_pre_processor(self, code: BytesConvertible) -> BytesConvertible:
        """Pre-processes the code before setting it."""
        return code

    def modified_accounts_salt(self) -> int:
        """
        Return a salt if this pre-allocation was affected by setting addresses
        to hard-coded accounts or has pre-funded addresses.

        Any modification the test does to a hard-coded address must affect
        this salt.
        """
        if (
            not self._set_addresses
            and not self._pre_funded_addresses
            and not self._hardcoded_addresses_deployed_to
            and not self._deleted_addresses
        ):
            return 0

        # Build a hashable buffer from the modified accounts.
        buffer = b""
        altered_accounts = (
            self._set_addresses
            | self._pre_funded_addresses
            | self._hardcoded_addresses_deployed_to
        )
        if altered_accounts:
            buffer += b"\0"
            for altered_account in sorted(altered_accounts):
                buffer += altered_account
                account = self[altered_account]
                assert account is not None
                buffer += account.hash()
        if self._deleted_addresses:
            buffer += b"\1"
            for deleted_address in sorted(self._deleted_addresses):
                buffer += deleted_address

        return int.from_bytes(
            hashlib.sha256(buffer).digest()[:8], byteorder="big"
        )

    def compute_pre_alloc_group_hash(
        self,
        *,
        fork: Fork | TransitionFork,
        genesis_environment: Environment,
        group_salt: str | None,
    ) -> str:
        """Hash (fork, env) in order to group tests by genesis config."""
        fork_digest = hashlib.sha256(fork.name().encode("utf-8")).digest()
        fork_hash = int.from_bytes(fork_digest[:8], byteorder="big")
        combined_hash = (
            fork_hash
            ^ hash(genesis_environment)
            ^ self.modified_accounts_salt()
        )

        # Check if this pre-allocation has a group salt
        if group_salt:
            # Add custom salt to hash
            salt_hash = hashlib.sha256(group_salt.encode("utf-8")).digest()
            salt_int = int.from_bytes(salt_hash[:8], byteorder="big")
            combined_hash = combined_hash ^ salt_int

        return f"0x{combined_hash:016x}"

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
        Filler implementation of contract deployment to a deterministic
        location.
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
        # Everything is deployed at genesis, hence `transitions_from`
        fork = self._fork.transitions_from()
        contract_address = compute_deterministic_create2_address(
            salt=salt, initcode=initcode, fork=fork
        )
        if contract_address in self:
            raise ValueError(
                f"contract address already in pre-alloc: {contract_address}"
            )
        max_code_size = fork.max_code_size()
        if len(deploy_code) > max_code_size:
            raise ValueError(
                f"code too large: {len(deploy_code)} > {max_code_size}"
            )

        fork_deterministic_factory_address = (
            fork.deterministic_factory_predeploy_address()
        )
        if (
            fork_deterministic_factory_address is None
            and DETERMINISTIC_FACTORY_ADDRESS not in self
        ):
            self.__internal_setitem__(
                DETERMINISTIC_FACTORY_ADDRESS,
                Account(
                    nonce=1,
                    code=DETERMINISTIC_FACTORY_BYTECODE,
                    storage={},
                ),
            )

        self.__internal_setitem__(
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
        Filler implementation of contract deployment.
        """
        del stub

        if storage is None:
            storage = {}
        code = self.code_pre_processor(code)
        code_bytes = (
            bytes(code) if not isinstance(code, (bytes, str)) else code
        )
        max_code_size = self._fork.transitions_from().max_code_size()
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
            contract_address = contract_address_from_hash(account_hash, salt)

        self.__internal_setitem__(contract_address, account)
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
        Filler implementation of EOA funding.

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
            if storage is None and delegation is None and code is None:
                nonce = Number(0 if nonce is None else nonce)
                account = Account(
                    nonce=nonce,
                    balance=amount,
                )
            else:
                # Type-4 transaction is sent to the EOA to set the storage, so
                # the nonce must be 1
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
                else:
                    code = b""
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
        eoa = eoa_from_hash(account_hash, salt)

        if account.nonce > 0:
            eoa.nonce = account.nonce

        if not isinstance(delegation, Address) and delegation == "Self":
            account = account.copy(code=DELEGATION_DESIGNATION + eoa)
        if account:
            self.__internal_setitem__(eoa, account)
        return eoa

    def _fund_address(
        self,
        address: Address,
        amount: int,
        *,
        minimum_balance: bool,
    ) -> None:
        """
        Filler implementation of address funding.
        """
        del minimum_balance
        self.__internal_setitem__(address, Account(balance=amount))

    def _nonexistent_account(self) -> Address:
        """
        Filler implementation of nonexistent_account.
        """
        salt = self.get_next_account_salt(EMPTY_ACCOUNT_HASH)
        return Address(eoa_from_hash(EMPTY_ACCOUNT_HASH, salt))


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
    # Strip xdist group suffix (e.g., @t8n-cache-abc12345) so entropy is
    # deterministic regardless of whether xdist is active.
    if "@" in node_id:
        node_id = node_id.rsplit("@", 1)[0]
    if fork is None:
        # FIXME: Static tests don't have a fork, so we need to get it from the
        # node.
        assert hasattr(request.node, "fork")
        fork = request.node.fork
    for fixture_format_name in ALL_FIXTURE_FORMAT_NAMES:
        if fixture_format_name in node_id:
            parts = node_id.split("::")
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
    alloc_flags: AllocFlags,
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
        flags=alloc_flags,
        fork=actual_fork,
    )
