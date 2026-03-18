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
    TransactionException,
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


@pytest.mark.parametrize(
    "exceeds_cap",
    [
        pytest.param(False, id="at_cap"),
        pytest.param(True, id="exceeds_cap", marks=pytest.mark.exception_test),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_calldata_floor_exceeding_tx_gas_limit_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    exceeds_cap: bool,
) -> None:
    """
    Verify calldata floor > TX_MAX_GAS_LIMIT rejects the transaction.

    When the EIP-7623 calldata floor cost exceeds the EIP-7825 transaction
    gas limit cap, the transaction must be rejected at validation —
    even though the regular intrinsic gas may be within the cap.

    at_cap: calldata floor exactly equals the cap — transaction accepted.
    exceeds_cap: calldata floor exceeds the cap by 1 — transaction rejected.
    """
    gas_costs = fork.gas_costs()
    gas_limit_cap = fork.transaction_gas_limit_cap()

    # calldata_floor = tokens * GAS_TX_DATA_TOKEN_FLOOR + GAS_TX_BASE
    # For non-zero bytes: tokens = 4 per byte.
    # Solve: num_bytes * 4 * floor_token + GAS_TX_BASE = target
    floor_token = gas_costs.GAS_TX_DATA_TOKEN_FLOOR
    tx_base = gas_costs.GAS_TX_BASE
    tokens_per_nonzero = 4

    # For at_cap: find max bytes where floor <= cap (floor division).
    # For exceeds_cap: add 1 more byte so floor > cap.
    max_tokens = (gas_limit_cap - tx_base) // floor_token
    max_bytes = max_tokens // tokens_per_nonzero
    num_bytes = max_bytes + (1 if exceeds_cap else 0)

    actual_tokens = num_bytes * tokens_per_nonzero
    actual_floor = actual_tokens * floor_token + tx_base

    calldata = b"\x01" * num_bytes
    contract = pre.deploy_contract(Op.STOP)

    tx = Transaction(
        to=contract,
        data=calldata,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
        error=TransactionException.INTRINSIC_GAS_TOO_LOW
        if exceeds_cap
        else None,
    )

    post = {contract: Account(code=Op.STOP)} if not exceeds_cap else {}
    state_test(pre=pre, post=post, tx=tx)
