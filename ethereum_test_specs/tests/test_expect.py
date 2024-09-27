"""
Test fixture post state (expect section) during state fixture generation.
"""

from typing import Any, Mapping, Type

import pytest

from ethereum_test_base_types import Account, Address
from ethereum_test_fixtures import FixtureFormats
from ethereum_test_forks import Fork, get_deployed_forks
from ethereum_test_types import Alloc, Environment, Storage, Transaction
from evm_transition_tool import ExecutionSpecsTransitionTool

from ..state import StateTest

ADDRESS_UNDER_TEST = Address(0x01)


@pytest.fixture
def pre(request) -> Alloc:
    """
    The pre state: Set from the test's indirectly parametrized `pre` parameter.
    """
    return Alloc(request.param)


@pytest.fixture
def post(request) -> Alloc:  # noqa: D103
    """
    The post state: Set from the test's indirectly parametrized `post` parameter.
    """
    return Alloc(request.param)


@pytest.fixture
def fork() -> Fork:  # noqa: D103
    return get_deployed_forks()[-1]


@pytest.fixture
def state_test(  # noqa: D103
    fork: Fork, pre: Mapping[Any, Any], post: Mapping[Any, Any]
) -> StateTest:
    return StateTest(
        env=Environment(),
        pre=pre,
        post=post,
        tx=Transaction(),
        tag="post_value_mismatch",
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
            Storage.KeyValueMismatch(address=ADDRESS_UNDER_TEST, key=1, want=2, got=1),
        ),
        (  # mismatch_2: 1:1 vs 2:1
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x01"}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={"0x02": "0x01"})},
            Storage.KeyValueMismatch(address=ADDRESS_UNDER_TEST, key=1, want=0, got=1),
        ),
        (  # mismatch_2_a: 1:1 vs 0:0
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x01"}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={"0x00": "0x00"})},
            Storage.KeyValueMismatch(address=ADDRESS_UNDER_TEST, key=1, want=0, got=1),
        ),
        (  # mismatch_2_b: 1:1 vs empty
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x01"}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={})},
            Storage.KeyValueMismatch(address=ADDRESS_UNDER_TEST, key=1, want=0, got=1),
        ),
        (  # mismatch_3: 0:0 vs 1:2
            {ADDRESS_UNDER_TEST: Account(storage={"0x00": "0x00"}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x02"})},
            Storage.KeyValueMismatch(address=ADDRESS_UNDER_TEST, key=1, want=2, got=0),
        ),
        (  # mismatch_3_a: empty vs 1:2
            {ADDRESS_UNDER_TEST: Account(storage={}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x02"})},
            Storage.KeyValueMismatch(address=ADDRESS_UNDER_TEST, key=1, want=2, got=0),
        ),
        (  # mismatch_4: 0:3, 1:2 vs 1:2
            {ADDRESS_UNDER_TEST: Account(storage={"0x00": "0x03", "0x01": "0x02"}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x02"})},
            Storage.KeyValueMismatch(address=ADDRESS_UNDER_TEST, key=0, want=0, got=3),
        ),
        (  # mismatch_5: 1:2, 2:3 vs 1:2
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x02", "0x02": "0x03"}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x02"})},
            Storage.KeyValueMismatch(address=ADDRESS_UNDER_TEST, key=2, want=0, got=3),
        ),
        (  # mismatch_6: 1:2 vs 1:2, 2:3
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x02"}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x02", "0x02": "0x03"})},
            Storage.KeyValueMismatch(address=ADDRESS_UNDER_TEST, key=2, want=3, got=0),
        ),
    ],
    indirect=["pre", "post"],
)
def test_post_storage_value_mismatch(
    pre: Alloc, post: Alloc, expected_exception, state_test, t8n, fork
):
    """
    Test post state `Account.storage` exceptions during state test fixture generation.
    """
    with pytest.raises(Storage.KeyValueMismatch) as e_info:
        state_test.generate(
            request=None, t8n=t8n, fork=fork, fixture_format=FixtureFormats.STATE_TEST
        )
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
        state_test.generate(
            request=None, t8n=t8n, fork=fork, fixture_format=FixtureFormats.STATE_TEST
        )
        return
    with pytest.raises(Account.NonceMismatch) as e_info:
        state_test.generate(
            request=None, t8n=t8n, fork=fork, fixture_format=FixtureFormats.STATE_TEST
        )
    assert e_info.value == Account.NonceMismatch(
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
        state_test.generate(
            request=None, t8n=t8n, fork=fork, fixture_format=FixtureFormats.STATE_TEST
        )
        return
    with pytest.raises(Account.CodeMismatch) as e_info:
        state_test.generate(
            request=None, t8n=t8n, fork=fork, fixture_format=FixtureFormats.STATE_TEST
        )
    assert e_info.value == Account.CodeMismatch(
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
        state_test.generate(
            request=None, t8n=t8n, fork=fork, fixture_format=FixtureFormats.STATE_TEST
        )
        return
    with pytest.raises(Account.BalanceMismatch) as e_info:
        state_test.generate(
            request=None, t8n=t8n, fork=fork, fixture_format=FixtureFormats.STATE_TEST
        )
    assert e_info.value == Account.BalanceMismatch(
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
            Alloc.MissingAccount,
        ),
        (
            {ADDRESS_UNDER_TEST: Account(balance=1)},
            {},
            None,
        ),
        (
            {ADDRESS_UNDER_TEST: Account(balance=1)},
            {ADDRESS_UNDER_TEST: Account.NONEXISTENT},
            Alloc.UnexpectedAccount,
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
        state_test.generate(
            request=None, t8n=t8n, fork=fork, fixture_format=FixtureFormats.STATE_TEST
        )
        return
    with pytest.raises(exception_type) as _:
        state_test.generate(
            request=None, t8n=t8n, fork=fork, fixture_format=FixtureFormats.STATE_TEST
        )
