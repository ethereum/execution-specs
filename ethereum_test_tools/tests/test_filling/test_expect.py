"""
Test fixture post state (expect section) during state fixture generation.
"""
from typing import Any, Mapping

import pytest

from ethereum_test_forks import Fork, get_deployed_forks
from evm_transition_tool import FixtureFormats, GethTransitionTool

from ...common import Account, Address, Environment, Transaction
from ...common.types import Storage
from ...spec import StateTest

ADDRESS_UNDER_TEST = Address(0x01)


@pytest.fixture
def pre(request) -> Mapping[Any, Any]:
    """
    The pre state: Set from the test's indirectly parametrized `pre` parameter.
    """
    return request.param


@pytest.fixture
def post(request) -> Mapping[Any, Any]:  # noqa: D103
    """
    The post state: Set from the test's indirectly parametrized `post` parameter.
    """
    return request.param


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
        fixture_format=FixtureFormats.STATE_TEST,
    )


@pytest.fixture
def t8n() -> GethTransitionTool:  # noqa: D103
    return GethTransitionTool()


# Storage value mismatch tests
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
)
def test_post_storage_value_mismatch(pre, post, expected_exception, state_test, t8n, fork):
    """
    Test post state `Account.storage` exceptions during state test fixture generation.
    """
    with pytest.raises(Storage.KeyValueMismatch) as e_info:
        state_test.generate(t8n=t8n, fork=fork)
    assert e_info.value == expected_exception


# Nonce value mismatch tests
@pytest.mark.parametrize(
    "pre,post",
    [
        ({ADDRESS_UNDER_TEST: Account(nonce=1)}, {ADDRESS_UNDER_TEST: Account(nonce=2)}),
        ({ADDRESS_UNDER_TEST: Account(nonce=1)}, {ADDRESS_UNDER_TEST: Account(nonce=0)}),
        ({ADDRESS_UNDER_TEST: Account(nonce=1)}, {ADDRESS_UNDER_TEST: Account(nonce=None)}),
    ],
)
def test_post_nonce_value_mismatch(pre, post, state_test, t8n, fork):
    """
    Test post state `Account.nonce` verification and exceptions during state test
    fixture generation.
    """
    pre_nonce = pre[ADDRESS_UNDER_TEST].nonce
    post_nonce = post[ADDRESS_UNDER_TEST].nonce
    if post_nonce is None:  # no exception
        state_test.generate(t8n=t8n, fork=fork)
        return
    with pytest.raises(Account.NonceMismatch) as e_info:
        state_test.generate(t8n=t8n, fork=fork)
    assert e_info.value == Account.NonceMismatch(
        address=ADDRESS_UNDER_TEST, want=post_nonce, got=pre_nonce
    )


# Code value mismatch tests
@pytest.mark.parametrize(
    "pre,post",
    [
        ({ADDRESS_UNDER_TEST: Account(code="0x02")}, {ADDRESS_UNDER_TEST: Account(code="0x01")}),
        ({ADDRESS_UNDER_TEST: Account(code="0x02")}, {ADDRESS_UNDER_TEST: Account(code="0x")}),
        ({ADDRESS_UNDER_TEST: Account(code="0x02")}, {ADDRESS_UNDER_TEST: Account(code=None)}),
    ],
    indirect=["pre", "post"],
)
def test_post_code_value_mismatch(pre, post, state_test, t8n, fork):
    """
    Test post state `Account.code` verification and exceptions during state test
    fixture generation.
    """
    pre_code = pre[ADDRESS_UNDER_TEST].code
    post_code = post[ADDRESS_UNDER_TEST].code
    if post_code is None:  # no exception
        state_test.generate(t8n=t8n, fork=fork)
        return
    with pytest.raises(Account.CodeMismatch) as e_info:
        state_test.generate(t8n=t8n, fork=fork)
    assert e_info.value == Account.CodeMismatch(
        address=ADDRESS_UNDER_TEST, want=post_code, got=pre_code
    )


# Balance value mismatch tests
@pytest.mark.parametrize(
    "pre,post",
    [
        ({ADDRESS_UNDER_TEST: Account(balance=1)}, {ADDRESS_UNDER_TEST: Account(balance=2)}),
        ({ADDRESS_UNDER_TEST: Account(balance=1)}, {ADDRESS_UNDER_TEST: Account(balance=0)}),
        ({ADDRESS_UNDER_TEST: Account(balance=1)}, {ADDRESS_UNDER_TEST: Account(balance=None)}),
    ],
    indirect=["pre", "post"],
)
def test_post_balance_value_mismatch(pre, post, state_test, t8n, fork):
    """
    Test post state `Account.balance` verification and exceptions during state test
    fixture generation.
    """
    pre_balance = pre[ADDRESS_UNDER_TEST].balance
    post_balance = post[ADDRESS_UNDER_TEST].balance
    if post_balance is None:  # no exception
        state_test.generate(t8n=t8n, fork=fork)
        return
    with pytest.raises(Account.BalanceMismatch) as e_info:
        state_test.generate(t8n=t8n, fork=fork)
    assert e_info.value == Account.BalanceMismatch(
        address=ADDRESS_UNDER_TEST, want=post_balance, got=pre_balance
    )


# Account mismatch tests
@pytest.mark.parametrize(
    "pre,post,error_str",
    [
        (
            {ADDRESS_UNDER_TEST: Account(balance=1)},
            {ADDRESS_UNDER_TEST: Account()},
            None,
        ),
        (
            {ADDRESS_UNDER_TEST: Account(balance=1)},
            {ADDRESS_UNDER_TEST: Account(balance=1), Address(0x02): Account(balance=1)},
            "expected account not found",
        ),
        (
            {ADDRESS_UNDER_TEST: Account(balance=1)},
            {},
            None,
        ),
        (
            {ADDRESS_UNDER_TEST: Account(balance=1)},
            {ADDRESS_UNDER_TEST: Account.NONEXISTENT},
            "found unexpected account",
        ),
    ],
    indirect=["pre", "post"],
)
def test_post_account_mismatch(state_test, t8n, fork, error_str):
    """
    Test post state `Account` verification and exceptions during state test
    fixture generation.
    """
    if error_str is None:
        state_test.generate(t8n=t8n, fork=fork)
        return
    with pytest.raises(Exception) as e_info:
        state_test.generate(t8n=t8n, fork=fork)
    assert error_str in str(e_info.value)
