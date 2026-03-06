"""
Test EIP-7623 calldata floor interaction with EIP-8037 state gas.

The calldata floor applies to the regular gas dimension only. It
does not affect state gas. Block gas accounting uses
max(tx_regular_gas, calldata_floor) for regular gas and tracks
state gas separately.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


@EIPChecklist.GasRefundsChanges.Test.CrossFunctional.CalldataCost()
@pytest.mark.valid_from("Amsterdam")
def test_calldata_floor_with_sstore(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test calldata floor does not affect state gas charging.

    A transaction with large calldata triggers the calldata floor for
    regular gas, but state gas for SSTORE is charged independently.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    # Large calldata to trigger the calldata floor
    calldata = b"\x01" * 256

    tx = Transaction(
        to=contract,
        data=calldata,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_calldata_floor_independent_of_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test calldata floor applies only to regular gas dimension.

    The calldata floor inflates regular gas used for block accounting
    but does not affect the state gas dimension. A transaction with
    high calldata and no state operations should succeed even when
    the floor exceeds actual execution gas.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    contract = pre.deploy_contract(code=Op.STOP)

    # Large calldata so the floor exceeds actual execution gas
    calldata = b"\xff" * 512

    tx = Transaction(
        to=contract,
        data=calldata,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_calldata_floor_higher_than_execution_with_state_ops(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test state gas is tracked separately when calldata floor dominates.

    Even when calldata floor > actual regular gas used, state gas for
    SSTORE is charged normally from the reservoir or gas_left.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    # Large calldata so floor dominates regular gas
    calldata = b"\x01" * 1024

    tx = Transaction(
        to=contract,
        data=calldata,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)
