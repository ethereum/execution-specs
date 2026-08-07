"""
No-silent-fallback exact-balance tests for
[EIP-8038: State Access Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-8038).

Each test funds the sender with *exactly* ``gas_limit * gas_price`` and
sets ``gas_limit`` one gas below the spec-correct Amsterdam intrinsic for
a single repriced dimension. A spec-correct client therefore rejects the
transaction with ``INTRINSIC_GAS_TOO_LOW``; a client that silently fell
back to the pre-Amsterdam value for that one constant would have computed
a strictly smaller intrinsic (``new - per_unit_delta``) and could have
executed the transaction. Because the sender holds no surplus wei, there
is no room for such a fallback to hide.

The pre-Amsterdam (old) per-component value is read from the parent
fork's schedule (``fork.parent()``); the spec-correct intrinsic is read
from the active fork's intrinsic calculator. Nothing is hardcoded; the
gap is asserted to be positive so the construction is only emitted when
the dimension genuinely got more expensive.
"""

from typing import Callable, Tuple

import pytest
from execution_testing import (
    AccessList,
    Alloc,
    AuthorizationTuple,
    Fork,
    GasCosts,
    StateTestFiller,
    Transaction,
    TransactionException,
)
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8038

REFERENCE_SPEC_GIT_PATH = ref_spec_8038.git_path
REFERENCE_SPEC_VERSION = ref_spec_8038.version

pytestmark = pytest.mark.valid_from("Amsterdam")

GAS_PRICE = 10


def gas_costs_before_increase(
    fork: Fork, costs: Callable[[GasCosts], Tuple[int, ...]]
) -> GasCosts:
    """
    Return the gas cost schedule of the closest ancestor fork whose
    constants selected by ``costs`` differ from ``fork``'s.

    Raises if no ancestor differs. When ``costs`` selects several
    constants, the walk stops at the first fork where any of them
    changed.
    """
    current = costs(fork.gas_costs())
    ancestor = fork.parent_or_fail()
    while costs(ancestor.gas_costs()) == current:
        ancestor = ancestor.parent_or_fail()
    return ancestor.gas_costs()


@pytest.mark.inclusion_test
@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "num_addresses,num_keys",
    [
        pytest.param(1, 0, id="one_address"),
        pytest.param(2, 0, id="two_addresses"),
        pytest.param(1, 1, id="one_address_one_key"),
    ],
)
def test_access_list_no_fallback(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    num_addresses: int,
    num_keys: int,
) -> None:
    """
    Reject an access-list transaction whose ``gas_limit`` is one gas
    below the Amsterdam intrinsic.

    EIP-8038 raises ``TX_ACCESS_LIST_ADDRESS`` and
    ``TX_ACCESS_LIST_STORAGE_KEY``. A client reusing the
    old per-address/per-key constants would compute an intrinsic smaller
    by ``num_addresses * addr_delta + num_keys * key_delta``; with the
    sender funded to the wei, that fallback must not slip through.
    """
    new_costs = fork.gas_costs()
    old_costs = gas_costs_before_increase(
        fork,
        lambda c: (c.TX_ACCESS_LIST_ADDRESS, c.TX_ACCESS_LIST_STORAGE_KEY),
    )
    addr_delta = (
        new_costs.TX_ACCESS_LIST_ADDRESS - old_costs.TX_ACCESS_LIST_ADDRESS
    )
    key_delta = (
        new_costs.TX_ACCESS_LIST_STORAGE_KEY
        - old_costs.TX_ACCESS_LIST_STORAGE_KEY
    )
    fallback_delta = num_addresses * addr_delta + num_keys * key_delta
    assert fallback_delta > 0

    # All storage keys live on the first listed address; the remaining
    # addresses carry no keys.
    storage_keys = list(range(num_keys))
    access_list = [
        AccessList(
            address=pre.fund_eoa(amount=0),
            storage_keys=storage_keys if index == 0 else [],
        )
        for index in range(num_addresses)
    ]

    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list,
        return_cost_deducted_prior_execution=True,
    )
    # One gas below the spec-correct intrinsic: a fallback client using
    # the old constants needs only `intrinsic - fallback_delta`.
    gas_limit = intrinsic - 1
    assert intrinsic - fallback_delta <= gas_limit < intrinsic

    sender = pre.fund_eoa(amount=gas_limit * GAS_PRICE)
    tx = Transaction(
        sender=sender,
        to=pre.fund_eoa(amount=0),
        access_list=access_list,
        gas_limit=gas_limit,
        gas_price=GAS_PRICE,
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )

    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.inclusion_test
@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "num_auths",
    [
        pytest.param(1, id="one_auth"),
        pytest.param(2, id="two_auths"),
    ],
)
def test_authorization_no_fallback(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    num_auths: int,
) -> None:
    """
    Reject a ``7702`` set-code transaction whose ``gas_limit`` is one
    gas below the Amsterdam intrinsic.

    EIP-8038 raises the per-authorization intrinsic
    (``AUTH_PER_EMPTY_ACCOUNT``). A client reusing the old per-auth
    constant would compute an intrinsic smaller by
    ``num_auths * auth_delta``; the exact-balance sender leaves no slack
    for that fallback.
    """
    new_costs = fork.gas_costs()
    old_costs = gas_costs_before_increase(
        fork, lambda c: (c.AUTH_PER_EMPTY_ACCOUNT,)
    )
    auth_delta = (
        new_costs.AUTH_PER_EMPTY_ACCOUNT - old_costs.AUTH_PER_EMPTY_ACCOUNT
    )
    fallback_delta = num_auths * auth_delta
    assert fallback_delta > 0

    target = pre.deploy_contract(code=b"")
    authorization_list = [
        AuthorizationTuple(
            address=target,
            nonce=0,
            signer=pre.fund_eoa(),
        )
        for _ in range(num_auths)
    ]

    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=authorization_list,
        return_cost_deducted_prior_execution=True,
    )
    gas_limit = intrinsic - 1
    assert intrinsic - fallback_delta <= gas_limit < intrinsic

    # Set-code (type-4) txs require EIP-1559 fee fields. With
    # max_fee == max_priority and value 0, the upfront debit the
    # protocol reserves is exactly gas_limit * GAS_PRICE.
    sender = pre.fund_eoa(amount=gas_limit * GAS_PRICE)
    tx = Transaction(
        sender=sender,
        to=pre.fund_eoa(amount=0),
        authorization_list=authorization_list,
        gas_limit=gas_limit,
        max_fee_per_gas=GAS_PRICE,
        max_priority_fee_per_gas=GAS_PRICE,
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )

    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.inclusion_test
@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.exception_test
def test_cold_account_access_no_fallback(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Reject a plain call transaction whose ``gas_limit`` is one gas below
    the Amsterdam intrinsic.

    Under EIP-2780 every non-create, non-self transaction pays one
    ``COLD_ACCOUNT_ACCESS`` in its intrinsic for touching the recipient;
    EIP-8038 raises that constant. A client reusing the
    old ``COLD_ACCOUNT_ACCESS`` would compute an intrinsic smaller by the
    per-access delta, and with the sender funded to the wei that fallback
    must not execute.
    """
    new_costs = fork.gas_costs()
    old_costs = gas_costs_before_increase(
        fork, lambda c: (c.COLD_ACCOUNT_ACCESS,)
    )
    fallback_delta = (
        new_costs.COLD_ACCOUNT_ACCESS - old_costs.COLD_ACCOUNT_ACCESS
    )
    assert fallback_delta > 0

    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True,
    )
    gas_limit = intrinsic - 1
    assert intrinsic - fallback_delta <= gas_limit < intrinsic

    sender = pre.fund_eoa(amount=gas_limit * GAS_PRICE)
    tx = Transaction(
        sender=sender,
        to=pre.deploy_contract(code=b""),
        gas_limit=gas_limit,
        gas_price=GAS_PRICE,
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )

    state_test(pre=pre, post={}, tx=tx)
