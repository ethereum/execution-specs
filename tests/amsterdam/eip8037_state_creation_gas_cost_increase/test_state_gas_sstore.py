"""
Test SSTORE state gas charging under EIP-8037.

Zero-to-nonzero storage writes charge `32 * cost_per_state_byte` of state
gas. Nonzero-to-nonzero writes charge no state gas. Restoration
(zero to nonzero back to zero in the same tx) refunds both state
gas and regular gas via the unified `refund_counter`.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
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


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.valid_from("Amsterdam")
def test_sstore_zero_to_nonzero(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SSTORE zero-to-nonzero charges state gas.

    Writing a nonzero value to a previously-zero slot charges
    32 * cost_per_state_byte of state gas in addition to regular gas.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_sstore_nonzero_to_nonzero(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SSTORE nonzero-to-nonzero charges no state gas.

    Updating a slot that already holds a nonzero value to a different
    nonzero value does not create new state, so no state gas is charged.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(2), 2),
        storage={0: 1},
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_sstore_nonzero_to_zero(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SSTORE nonzero-to-zero charges no state gas.

    Clearing a storage slot (setting to zero) does not grow state and
    earns a regular gas refund (GAS_STORAGE_CLEAR_REFUND).
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(0), 0),
        storage={0: 1},
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_sstore_zero_to_zero(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SSTORE zero-to-zero charges no state gas.

    Writing zero to an already-zero slot creates no new state. Only
    the warm access regular gas cost is charged.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(0), 0),
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@pytest.mark.valid_from("Amsterdam")
def test_sstore_restoration_refund(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SSTORE zero-to-nonzero-to-zero restoration refunds state gas.

    When a slot is written from zero to nonzero and then restored to
    zero in the same transaction, the state gas charge
    (32 * cost_per_state_byte) is refunded via refund_counter along
    with the regular gas write cost.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    contract = pre.deploy_contract(
        code=(Op.SSTORE(0, 1) + Op.SSTORE(0, 0)),
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    # Slot 0 restored to zero — state gas refunded
    post = {contract: Account(storage={0: 0})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_sstore_restoration_nonzero_no_state_refund(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test nonzero-to-nonzero-to-original restoration has no state gas refund.

    When a slot holds a nonzero original value, changing it and
    restoring it never involves state gas (no state growth occurred),
    so only regular gas refunds apply.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    contract = pre.deploy_contract(
        code=(Op.SSTORE(0, 2) + Op.SSTORE(0, 1)),
        storage={0: 1},
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage={0: 1})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_sstore_clear_refund_reversal(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test clearing a nonzero slot then un-clearing reverses the refund.

    When a slot with a nonzero original value is cleared (set to zero),
    the clear refund is granted. If the slot is then set back to a
    nonzero value, the clear refund is reversed via refund_counter.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    contract = pre.deploy_contract(
        code=(Op.SSTORE(0, 0) + Op.SSTORE(0, 2)),
        storage={0: 1},
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage={0: 2})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "num_slots",
    [
        pytest.param(1, id="single_slot"),
        pytest.param(5, id="five_slots"),
        pytest.param(10, id="ten_slots"),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_sstore_multiple_slots(
    state_test: StateTestFiller,
    pre: Alloc,
    num_slots: int,
    fork: Fork,
) -> None:
    """
    Test multiple zero-to-nonzero SSTOREs each charge state gas.

    Each slot written from zero to nonzero independently charges
    32 * cost_per_state_byte of state gas.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    storage = Storage()
    code = Bytecode()
    for _ in range(num_slots):
        code += Op.SSTORE(storage.store_next(1), 1)
    contract = pre.deploy_contract(code=code)

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_sstore_state_gas_drawn_from_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SSTORE state gas drawn from reservoir before gas_left.

    Provide enough gas above TX_MAX_GAS_LIMIT to fully cover the
    SSTORE state gas from the reservoir, leaving gas_left untouched
    by the state gas charge.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.with_all_typed_transactions
@pytest.mark.valid_from("Amsterdam")
def test_sstore_state_gas_all_tx_types(
    state_test: StateTestFiller,
    pre: Alloc,
    typed_transaction: Transaction,
    fork: Fork,
) -> None:
    """
    Test SSTORE state gas works across all transaction types.

    Different tx types (legacy, access list, EIP-1559, blob, SetCode)
    have different intrinsic costs, which affects the gas split between
    gas_left and state_gas_reservoir. Verify SSTORE succeeds with
    each type.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    tx = typed_transaction.copy(
        to=contract,
        gas_limit=gas_limit_cap,
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "gas_above_stipend",
    [
        pytest.param(-1, id="below_stipend"),
        pytest.param(0, id="at_stipend"),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_sstore_stipend_check_excludes_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_above_stipend: int,
) -> None:
    """
    Verify SSTORE stipend check uses gas_left only, not the reservoir.

    A child frame has gas_left at or just below the stipend threshold
    (GAS_CALL_STIPEND + 1) while the reservoir holds ample state gas.
    The stipend check must fail when gas_left < stipend, regardless
    of the reservoir balance.

    With below_stipend: SSTORE fails (gas_left < 2301, reservoir ignored).
    With at_stipend: SSTORE passes the stipend check and proceeds.
    """
    gas_costs = fork.gas_costs()
    stipend = gas_costs.GAS_CALL_STIPEND + 1
    sstore_state_gas = fork.sstore_state_gas()

    # Child: Op.SSTORE(0, 1) = 2 pushes + SSTORE opcode.
    child_code = Op.SSTORE(0, 1)
    child = pre.deploy_contract(child_code)

    # Full regular gas for the child (pushes + SSTORE regular cost).
    # State gas comes from the reservoir so it doesn't affect gas_left.
    child_full_regular = child_code.gas_cost(fork) - sstore_state_gas

    # below_stipend: give 1 less than stipend after pushes, fails check.
    # at_stipend: give full regular gas, passes check and completes.
    if gas_above_stipend < 0:
        push_gas = 2 * gas_costs.GAS_VERY_LOW
        child_gas = push_gas + stipend - 1
    else:
        child_gas = child_full_regular

    # Caller forwards limited regular gas via CALL. State gas comes
    # from the reservoir (gas_limit above the cap).
    caller_storage = Storage()
    sstore_succeeds = gas_above_stipend >= 0
    caller = pre.deploy_contract(
        Op.SSTORE(
            caller_storage.store_next(
                1 if sstore_succeeds else 0,
                "sstore_succeeds"
                if sstore_succeeds
                else "sstore_fails_stipend",
            ),
            Op.CALL(gas=child_gas, address=child),
        )
    )

    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        gas_limit=gas_limit_cap + sstore_state_gas,
    )

    post = {caller: Account(storage=caller_storage)}
    state_test(pre=pre, tx=tx, post=post)
