"""
Test state gas behavior when calling via 7702 delegation pointer vs direct.

Under EIP-8037, calling a contract that has a 7702 delegation pointer
should charge the same state gas as calling the target directly. The
delegation resolution is transparent to gas accounting.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    AuthorizationTuple,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


@pytest.mark.valid_from("EIP8037")
def test_sstore_via_delegation_pointer(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SSTORE state gas charged when called via delegation pointer.

    A contract performs an SSTORE. An EOA delegates to that contract
    via EIP-7702. Calling the EOA (delegation pointer) executes the
    contract code in the EOA's context. The SSTORE state gas should
    be charged from the reservoir just as it would for a direct call.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    auth_state_gas = fork.transaction_intrinsic_state_gas(
        authorization_count=1,
    )
    sstore_state_gas = fork.sstore_state_gas()

    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    # EOA with pre-existing delegation to the contract
    delegator = pre.fund_eoa(delegation=contract)

    sender = pre.fund_eoa()
    tx = Transaction(
        to=delegator,
        gas_limit=(gas_limit_cap + auth_state_gas + sstore_state_gas),
        authorization_list=[
            AuthorizationTuple(
                address=contract,
                nonce=0,
                signer=delegator,
            ),
        ],
        sender=sender,
    )

    # SSTORE writes to the delegator's storage context
    post = {delegator: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_sstore_direct_call_same_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SSTORE state gas charged when calling the contract directly.

    Baseline comparison: calling the contract directly (not via a
    delegation pointer) charges SSTORE state gas identically.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    sender = pre.fund_eoa()
    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=sender,
    )

    post = {contract: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_delegation_pointer_new_account_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test delegation pointer CALL to empty account charges new-account gas.

    A contract CALLs with value to a non-existent address. When executed
    via a delegation pointer, the new-account state gas
    is charged identically to a direct call.
    """
    gas_costs = fork.gas_costs()
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    auth_state_gas = fork.transaction_intrinsic_state_gas(
        authorization_count=1,
    )
    new_account_state_gas = gas_costs.GAS_NEW_ACCOUNT

    target = 0xDEAD

    parent_storage = Storage()
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                parent_storage.store_next(1),
                Op.CALL(gas=100_000, address=target, value=1),
            )
        ),
        balance=1,
    )

    # EOA delegates to the contract
    delegator = pre.fund_eoa(delegation=contract, amount=1)

    sender = pre.fund_eoa()
    tx = Transaction(
        to=delegator,
        gas_limit=(gas_limit_cap + auth_state_gas + new_account_state_gas),
        authorization_list=[
            AuthorizationTuple(
                address=contract,
                nonce=0,
                signer=delegator,
            ),
        ],
        sender=sender,
    )

    # CALL success stored in delegator's storage context
    post = {delegator: Account(storage=parent_storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)
