"""Test fixture post state (expect section) during state fixture generation."""

from typing import Any, Mapping, Type

import pytest

from ethereum_clis import ExecutionSpecsTransitionTool
from ethereum_test_base_types import Account, Address, TestAddress, TestPrivateKey
from ethereum_test_exceptions import TransactionException
from ethereum_test_fixtures import BlockchainFixture, FixtureFormat, StateFixture
from ethereum_test_forks import Fork, get_deployed_forks
from ethereum_test_types import Alloc, Environment, Storage, Transaction, TransactionReceipt

from ..helpers import (
    TransactionExceptionMismatchError,
    TransactionReceiptMismatchError,
    TransactionUnexpectedFailError,
    TransactionUnexpectedSuccessError,
)
from ..state import StateTest

ADDRESS_UNDER_TEST = Address(0x01)


@pytest.fixture
def tx() -> Transaction:
    """Fixture set from the test's indirectly parametrized `tx` parameter."""
    return Transaction(secret_key=TestPrivateKey)


@pytest.fixture
def pre(request) -> Alloc:
    """Fixture set from the test's indirectly parametrized `pre` parameter."""
    extra_accounts = {}
    if hasattr(request, "param"):
        extra_accounts = request.param
    return Alloc(extra_accounts | {TestAddress: Account(balance=(10**18))})


@pytest.fixture
def post(request) -> Alloc:  # noqa: D103
    """Fixture set from the test's indirectly parametrized `post` parameter."""
    extra_accounts = {}
    if hasattr(request, "param"):
        extra_accounts = request.param
    return Alloc(extra_accounts)


@pytest.fixture
def fork() -> Fork:  # noqa: D103
    return get_deployed_forks()[-1]


@pytest.fixture
def state_test(  # noqa: D103
    pre: Mapping[Any, Any], post: Mapping[Any, Any], tx: Transaction
) -> StateTest:
    return StateTest(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.fixture
def t8n() -> ExecutionSpecsTransitionTool:  # noqa: D103
    return ExecutionSpecsTransitionTool()


# Storage value mismatch tests
@pytest.mark.run_in_serial
@pytest.mark.parametrize(
    "pre,post,expected_exception",
    [
        (  # mismatch_1: 1:1 vs 1:2
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x01"}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x02"})},
            Storage.KeyValueMismatchError(address=ADDRESS_UNDER_TEST, key=1, want=2, got=1),
        ),
        (  # mismatch_2: 1:1 vs 2:1
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x01"}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={"0x02": "0x01"})},
            Storage.KeyValueMismatchError(address=ADDRESS_UNDER_TEST, key=1, want=0, got=1),
        ),
        (  # mismatch_2_a: 1:1 vs 0:0
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x01"}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={"0x00": "0x00"})},
            Storage.KeyValueMismatchError(address=ADDRESS_UNDER_TEST, key=1, want=0, got=1),
        ),
        (  # mismatch_2_b: 1:1 vs empty
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x01"}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={})},
            Storage.KeyValueMismatchError(address=ADDRESS_UNDER_TEST, key=1, want=0, got=1),
        ),
        (  # mismatch_3: 0:0 vs 1:2
            {ADDRESS_UNDER_TEST: Account(storage={"0x00": "0x00"}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x02"})},
            Storage.KeyValueMismatchError(address=ADDRESS_UNDER_TEST, key=1, want=2, got=0),
        ),
        (  # mismatch_3_a: empty vs 1:2
            {ADDRESS_UNDER_TEST: Account(storage={}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x02"})},
            Storage.KeyValueMismatchError(address=ADDRESS_UNDER_TEST, key=1, want=2, got=0),
        ),
        (  # mismatch_4: 0:3, 1:2 vs 1:2
            {ADDRESS_UNDER_TEST: Account(storage={"0x00": "0x03", "0x01": "0x02"}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x02"})},
            Storage.KeyValueMismatchError(address=ADDRESS_UNDER_TEST, key=0, want=0, got=3),
        ),
        (  # mismatch_5: 1:2, 2:3 vs 1:2
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x02", "0x02": "0x03"}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x02"})},
            Storage.KeyValueMismatchError(address=ADDRESS_UNDER_TEST, key=2, want=0, got=3),
        ),
        (  # mismatch_6: 1:2 vs 1:2, 2:3
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x02"}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x02", "0x02": "0x03"})},
            Storage.KeyValueMismatchError(address=ADDRESS_UNDER_TEST, key=2, want=3, got=0),
        ),
    ],
    indirect=["pre", "post"],
)
def test_post_storage_value_mismatch(expected_exception, state_test, t8n, fork):
    """Test post state `Account.storage` exceptions during state test fixture generation."""
    with pytest.raises(Storage.KeyValueMismatchError) as e_info:
        state_test.generate(request=None, t8n=t8n, fork=fork, fixture_format=StateFixture)
    assert e_info.value == expected_exception


# Nonce value mismatch tests
@pytest.mark.run_in_serial
@pytest.mark.parametrize(
    "pre,post",
    [
        ({ADDRESS_UNDER_TEST: Account(nonce=1)}, {ADDRESS_UNDER_TEST: Account(nonce=2)}),
        ({ADDRESS_UNDER_TEST: Account(nonce=1)}, {ADDRESS_UNDER_TEST: Account(nonce=0)}),
        ({ADDRESS_UNDER_TEST: Account(nonce=1)}, {ADDRESS_UNDER_TEST: Account()}),
    ],
    indirect=["pre", "post"],
)
def test_post_nonce_value_mismatch(pre: Alloc, post: Alloc, state_test, t8n, fork):
    """
    Test post state `Account.nonce` verification and exceptions during state test
    fixture generation.
    """
    pre_account = pre[ADDRESS_UNDER_TEST]
    post_account = post[ADDRESS_UNDER_TEST]
    assert pre_account is not None
    assert post_account is not None
    pre_nonce = pre_account.nonce
    post_nonce = post_account.nonce
    if "nonce" not in post_account.model_fields_set:  # no exception
        state_test.generate(request=None, t8n=t8n, fork=fork, fixture_format=StateFixture)
        return
    with pytest.raises(Account.NonceMismatchError) as e_info:
        state_test.generate(request=None, t8n=t8n, fork=fork, fixture_format=StateFixture)
    assert e_info.value == Account.NonceMismatchError(
        address=ADDRESS_UNDER_TEST, want=post_nonce, got=pre_nonce
    )


# Code value mismatch tests
@pytest.mark.run_in_serial
@pytest.mark.parametrize(
    "pre,post",
    [
        ({ADDRESS_UNDER_TEST: Account(code="0x02")}, {ADDRESS_UNDER_TEST: Account(code="0x01")}),
        ({ADDRESS_UNDER_TEST: Account(code="0x02")}, {ADDRESS_UNDER_TEST: Account(code="0x")}),
        ({ADDRESS_UNDER_TEST: Account(code="0x02")}, {ADDRESS_UNDER_TEST: Account()}),
    ],
    indirect=["pre", "post"],
)
def test_post_code_value_mismatch(pre: Alloc, post: Alloc, state_test, t8n, fork):
    """
    Test post state `Account.code` verification and exceptions during state test
    fixture generation.
    """
    pre_account = pre[ADDRESS_UNDER_TEST]
    post_account = post[ADDRESS_UNDER_TEST]
    assert pre_account is not None
    assert post_account is not None
    pre_code = pre_account.code
    post_code = post_account.code
    if "code" not in post_account.model_fields_set:  # no exception
        state_test.generate(request=None, t8n=t8n, fork=fork, fixture_format=StateFixture)
        return
    with pytest.raises(Account.CodeMismatchError) as e_info:
        state_test.generate(request=None, t8n=t8n, fork=fork, fixture_format=StateFixture)
    assert e_info.value == Account.CodeMismatchError(
        address=ADDRESS_UNDER_TEST, want=post_code, got=pre_code
    )


# Balance value mismatch tests
@pytest.mark.run_in_serial
@pytest.mark.parametrize(
    "pre,post",
    [
        ({ADDRESS_UNDER_TEST: Account(balance=1)}, {ADDRESS_UNDER_TEST: Account(balance=2)}),
        ({ADDRESS_UNDER_TEST: Account(balance=1)}, {ADDRESS_UNDER_TEST: Account(balance=0)}),
        ({ADDRESS_UNDER_TEST: Account(balance=1)}, {ADDRESS_UNDER_TEST: Account()}),
    ],
    indirect=["pre", "post"],
)
def test_post_balance_value_mismatch(pre: Alloc, post: Alloc, state_test, t8n, fork):
    """
    Test post state `Account.balance` verification and exceptions during state test
    fixture generation.
    """
    pre_account = pre[ADDRESS_UNDER_TEST]
    post_account = post[ADDRESS_UNDER_TEST]
    assert pre_account is not None
    assert post_account is not None
    pre_balance = pre_account.balance
    post_balance = post_account.balance
    if "balance" not in post_account.model_fields_set:  # no exception
        state_test.generate(request=None, t8n=t8n, fork=fork, fixture_format=StateFixture)
        return
    with pytest.raises(Account.BalanceMismatchError) as e_info:
        state_test.generate(request=None, t8n=t8n, fork=fork, fixture_format=StateFixture)
    assert e_info.value == Account.BalanceMismatchError(
        address=ADDRESS_UNDER_TEST, want=post_balance, got=pre_balance
    )


# Account mismatch tests
@pytest.mark.run_in_serial
@pytest.mark.parametrize(
    "pre,post,exception_type",
    [
        (
            {ADDRESS_UNDER_TEST: Account(balance=1)},
            {ADDRESS_UNDER_TEST: Account()},
            None,
        ),
        (
            {ADDRESS_UNDER_TEST: Account(balance=1)},
            {ADDRESS_UNDER_TEST: Account(balance=1), Address(0x02): Account(balance=1)},
            Alloc.MissingAccountError,
        ),
        (
            {ADDRESS_UNDER_TEST: Account(balance=1)},
            {},
            None,
        ),
        (
            {ADDRESS_UNDER_TEST: Account(balance=1)},
            {ADDRESS_UNDER_TEST: Account.NONEXISTENT},
            Alloc.UnexpectedAccountError,
        ),
    ],
    indirect=["pre", "post"],
)
def test_post_account_mismatch(state_test, t8n, fork, exception_type: Type[Exception] | None):
    """
    Test post state `Account` verification and exceptions during state test
    fixture generation.
    """
    if exception_type is None:
        state_test.generate(request=None, t8n=t8n, fork=fork, fixture_format=StateFixture)
        return
    with pytest.raises(exception_type) as _:
        state_test.generate(request=None, t8n=t8n, fork=fork, fixture_format=StateFixture)


# Transaction result mismatch tests
@pytest.mark.run_in_serial
@pytest.mark.parametrize(
    "tx,exception_type",
    [
        pytest.param(
            Transaction(
                secret_key=TestPrivateKey,
                expected_receipt=TransactionReceipt(gas_used=21_000),
            ),
            TransactionExceptionMismatchError,
            id="TransactionExceptionMismatchError",
            marks=pytest.mark.xfail(
                reason="Exceptions need to be better described in the t8n tool."
            ),
        ),
        pytest.param(
            Transaction(
                secret_key=TestPrivateKey,
                error=TransactionException.INTRINSIC_GAS_TOO_LOW,
                expected_receipt=TransactionReceipt(gas_used=21_000),
            ),
            TransactionUnexpectedSuccessError,
            id="TransactionUnexpectedSuccessError",
        ),
        pytest.param(
            Transaction(
                secret_key=TestPrivateKey,
                gas_limit=20_999,
                expected_receipt=TransactionReceipt(gas_used=21_000),
            ),
            TransactionUnexpectedFailError,
            id="TransactionUnexpectedFailError",
        ),
        pytest.param(
            Transaction(
                secret_key=TestPrivateKey,
                expected_receipt=TransactionReceipt(gas_used=21_001),
            ),
            TransactionReceiptMismatchError,
            id="TransactionReceiptMismatchError",
        ),
        pytest.param(
            Transaction(
                secret_key=TestPrivateKey,
                gas_limit=20_999,
                expected_receipt=TransactionReceipt(gas_used=21_001),
            ),
            TransactionUnexpectedFailError,
            id="TransactionUnexpectedFailError+TransactionReceiptMismatchError",
        ),
        pytest.param(
            Transaction(
                secret_key=TestPrivateKey,
                error=TransactionException.INTRINSIC_GAS_TOO_LOW,
                expected_receipt=TransactionReceipt(gas_used=21_001),
            ),
            TransactionUnexpectedSuccessError,
            id="TransactionUnexpectedSuccessError+TransactionReceiptMismatchError",
        ),
    ],
)
@pytest.mark.parametrize(
    "fixture_format",
    [
        StateFixture,
        BlockchainFixture,
    ],
)
def test_transaction_expectation(
    state_test,
    t8n,
    fork,
    exception_type: Type[Exception] | None,
    fixture_format: FixtureFormat,
):
    """
    Test a transaction that has an unexpected error, expected error, or expected a specific
    value in its receipt.
    """
    if exception_type is None:
        state_test.generate(request=None, t8n=t8n, fork=fork, fixture_format=fixture_format)
    else:
        with pytest.raises(exception_type) as _:
            state_test.generate(request=None, t8n=t8n, fork=fork, fixture_format=fixture_format)
