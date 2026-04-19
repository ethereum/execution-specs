"""
Test SSTORE state gas charging under EIP-8037.

Zero-to-nonzero storage writes charge `32 * cost_per_state_byte` of state
gas. Nonzero-to-nonzero writes charge no state gas. 0 to x to 0
restoration in the same tx refunds state gas directly to
`state_gas_reservoir` (inline at x to 0) and the regular write-cost
portion to `refund_counter`.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Environment,
    Fork,
    Header,
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
@pytest.mark.valid_from("EIP8037")
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


@pytest.mark.valid_from("EIP8037")
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


@pytest.mark.valid_from("EIP8037")
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


@pytest.mark.valid_from("EIP8037")
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
@pytest.mark.valid_from("EIP8037")
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


@pytest.mark.valid_from("EIP8037")
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


@pytest.mark.valid_from("EIP8037")
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
@pytest.mark.valid_from("EIP8037")
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


@pytest.mark.valid_from("EIP8037")
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
@pytest.mark.valid_from("EIP8037")
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
@pytest.mark.valid_from("EIP8037")
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


@pytest.mark.parametrize(
    "num_cycles",
    [
        pytest.param(1, id="single_cycle"),
        pytest.param(50, id="fifty_cycles"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_sstore_restoration_block_state_gas_zero(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    num_cycles: int,
) -> None:
    """
    Verify 0 to x to 0 cycles contribute zero to block state gas.

    Net state growth is zero. State gas goes directly to
    `state_gas_reservoir` rather than `refund_counter`, so block
    state gas is not inflated by the charges.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    code = Bytecode()
    for i in range(num_cycles):
        code += Op.SSTORE(i, 1) + Op.SSTORE.with_metadata(
            key_warm=True,
            original_value=0,
            current_value=1,
            new_value=0,
        )(i, 0)
    tx_regular = (
        intrinsic_gas + code.gas_cost(fork) - num_cycles * sstore_state_gas
    )

    contract = pre.deploy_contract(code=code)
    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + num_cycles * sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], header_verify=Header(gas_used=tx_regular))],
        post={contract: Account(storage=dict.fromkeys(range(num_cycles), 0))},
    )


@pytest.mark.parametrize(
    "num_cycles",
    [
        pytest.param(1, id="one_cycle"),
        pytest.param(10, id="ten_cycles"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_sstore_restoration_mixed_with_genuine_sstore(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    num_cycles: int,
) -> None:
    """
    Verify restoration cycles plus a genuine 0 to x SSTORE.

    `num_cycles` of 0 to x to 0 refund; one genuine 0 to x on slot 99
    persists, contributing exactly one `sstore_state_gas` to block
    state gas.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    code = Bytecode()
    for i in range(num_cycles):
        code += Op.SSTORE(i, 1) + Op.SSTORE.with_metadata(
            key_warm=True,
            original_value=0,
            current_value=1,
            new_value=0,
        )(i, 0)
    code += Op.SSTORE(99, 1)

    num_0_to_1 = num_cycles + 1
    tx_regular = (
        intrinsic_gas + code.gas_cost(fork) - num_0_to_1 * sstore_state_gas
    )
    expected = max(tx_regular, sstore_state_gas)

    contract = pre.deploy_contract(code=code)
    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + num_0_to_1 * sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post_storage = dict.fromkeys(range(num_cycles), 0)
    post_storage[99] = 1
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], header_verify=Header(gas_used=expected))],
        post={contract: Account(storage=post_storage)},
    )


@pytest.mark.valid_from("EIP8037")
def test_sstore_restoration_intermediate_values(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify restoration refund triggers for 0 to x to y to 0.

    The refund condition is `original_value == new_value == 0`,
    independent of intermediate values. One state gas charge at the
    first 0 to x; no charge for nonzero-to-nonzero; refund to reservoir
    at y to 0.  Net block state gas is zero.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    code = (
        Op.SSTORE(0, 1)
        + Op.SSTORE.with_metadata(
            key_warm=True,
            original_value=0,
            current_value=1,
            new_value=2,
        )(0, 2)
        + Op.SSTORE.with_metadata(
            key_warm=True,
            original_value=0,
            current_value=2,
            new_value=0,
        )(0, 0)
    )
    tx_regular = intrinsic_gas + code.gas_cost(fork) - sstore_state_gas

    contract = pre.deploy_contract(code=code)
    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], header_verify=Header(gas_used=tx_regular))],
        post={contract: Account(storage={0: 0})},
    )


@pytest.mark.valid_from("EIP8037")
def test_sstore_restoration_then_reset(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify accounting across 0 to 1 to 0 to 1 (restore then re-set).

    The refund applied at 1 to 0 returns state gas to the reservoir;
    the subsequent 0 to 1 re-charges state gas.  Net: one charge
    remains, one state gas worth counted in block state gas.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    code = (
        Op.SSTORE(0, 1)
        + Op.SSTORE.with_metadata(
            key_warm=True,
            original_value=0,
            current_value=1,
            new_value=0,
        )(0, 0)
        + Op.SSTORE.with_metadata(
            key_warm=True,
            original_value=0,
            current_value=0,
            new_value=1,
        )(0, 1)
    )
    tx_regular = intrinsic_gas + code.gas_cost(fork) - 2 * sstore_state_gas
    expected = max(tx_regular, sstore_state_gas)

    contract = pre.deploy_contract(code=code)
    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], header_verify=Header(gas_used=expected))],
        post={contract: Account(storage={0: 1})},
    )


@pytest.mark.valid_from("EIP8037")
def test_sstore_restoration_reservoir_replenished_inline(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify the reservoir is replenished inline at x to 0.

    Reservoir sized for exactly one slot. After the 0 to 1 to 0 pair
    on slot 0, the reservoir refill allows a second 0 to 1 on slot 1
    to draw from it.  Block state gas reflects only slot 1.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    code = (
        Op.SSTORE(0, 1)
        + Op.SSTORE.with_metadata(
            key_warm=True,
            original_value=0,
            current_value=1,
            new_value=0,
        )(0, 0)
        + Op.SSTORE(1, 1)
    )
    tx_regular = intrinsic_gas + code.gas_cost(fork) - 2 * sstore_state_gas
    expected = max(tx_regular, sstore_state_gas)

    contract = pre.deploy_contract(code=code)
    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], header_verify=Header(gas_used=expected))],
        post={contract: Account(storage={0: 0, 1: 1})},
    )


@pytest.mark.with_all_call_opcodes(
    selector=lambda call_opcode: call_opcode != Op.STATICCALL
)
@pytest.mark.valid_from("EIP8037")
def test_sstore_restoration_cross_frame(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
) -> None:
    """
    Verify restoration refund across frames for CALL / CALLCODE / DELEGATECALL.

    Callee performs the full 0 to x to 0 cycle within its call. For
    CALL the slot lives in callee's storage; for CALLCODE/DELEGATECALL
    it lives in caller's.  The reservoir is tx-level, so the refund
    applies regardless of storage ownership.  Net block state gas is
    zero.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    child_code = (
        Op.SSTORE(0, 1)
        + Op.SSTORE.with_metadata(
            key_warm=True,
            original_value=0,
            current_value=1,
            new_value=0,
        )(0, 0)
        + Op.STOP
    )
    # Callee's regular gas excludes the state gas (refunded at x to 0).
    child_regular = child_code.gas_cost(fork) - sstore_state_gas
    child = pre.deploy_contract(code=child_code)

    parent_code = Op.POP(call_opcode(gas=child_regular, address=child))
    parent = pre.deploy_contract(code=parent_code)

    tx_regular = intrinsic_gas + parent_code.gas_cost(fork) + child_regular

    tx = Transaction(
        to=parent,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    # CALL targets callee's storage; CALLCODE/DELEGATECALL target caller's.
    slot_owner = child if call_opcode == Op.CALL else parent
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], header_verify=Header(gas_used=tx_regular))],
        post={slot_owner: Account(storage={0: 0})},
    )


@pytest.mark.with_all_call_opcodes(
    selector=lambda call_opcode: call_opcode != Op.STATICCALL
)
@pytest.mark.valid_from("EIP8037")
def test_sstore_restoration_sub_frame_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
) -> None:
    """
    Verify 0 to x to 0 reservoir refund unwinds on sub-frame REVERT.

    The sub-call performs 0 to x to 0 then REVERTs.  If the reservoir
    refund is not rolled back with the reverted frame, the reservoir
    stays inflated by `sstore_state_gas`.  A single-SSTORE probe sized
    to OOG by 1 would then succeed; the test asserts it OOGs.
    """
    gas_costs = fork.gas_costs()
    # Probe SSTORE(0, 1): 2 pushes + cold storage write + state gas - 1,
    # so it OOGs by 1 when the reservoir is 0 and succeeds otherwise.
    probe_gas = (
        2 * gas_costs.GAS_VERY_LOW
        + gas_costs.GAS_COLD_STORAGE_WRITE
        + fork.sstore_state_gas()
        - 1
    )

    child_code = Op.SSTORE(0, 1) + Op.SSTORE(0, 0) + Op.REVERT(0, 0)
    child = pre.deploy_contract(code=child_code)
    probe = pre.deploy_contract(code=Op.SSTORE(0, 1))

    # Forward all remaining gas so the child completes both SSTOREs
    # and REVERT without a hard-coded budget.
    caller_storage = Storage()
    caller_code = Op.POP(call_opcode(gas=Op.GAS, address=child)) + Op.SSTORE(
        caller_storage.store_next(0, "probe_must_fail"),
        Op.CALL(gas=probe_gas, address=probe),
    )
    caller = pre.deploy_contract(code=caller_code)

    # gas_limit at the cap means reservoir starts at 0 pre-call.
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    post = {caller: Account(storage=caller_storage)}
    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.valid_from("EIP8037")
def test_sstore_restoration_ancestor_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify the SSTORE 0 to x to 0 refund unwinds when an ancestor frame
    (not the applying frame itself) reverts.

    Inner frame applies the refund and returns successfully; its
    refund propagates to middle via `incorporate_child_on_success`.
    Middle then REVERTs; its refund must be dropped by the caller's
    `incorporate_child_on_error`, rather than propagating up.  This
    exercises the recursive scope that single-frame revert tests do
    not: a bug in the success propagation of `state_gas_refund` would
    leak the refund into the caller's reservoir.
    """
    gas_costs = fork.gas_costs()
    # Probe SSTORE(0, 1): 2 pushes + cold storage write + state gas - 1,
    # so it OOGs by 1 when the reservoir is 0 and succeeds otherwise.
    probe_gas = (
        2 * gas_costs.GAS_VERY_LOW
        + gas_costs.GAS_COLD_STORAGE_WRITE
        + fork.sstore_state_gas()
        - 1
    )

    inner = pre.deploy_contract(
        code=Op.SSTORE(0, 1) + Op.SSTORE(0, 0) + Op.STOP,
    )
    middle = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=Op.GAS, address=inner)) + Op.REVERT(0, 0),
    )
    probe = pre.deploy_contract(code=Op.SSTORE(0, 1))

    caller_storage = Storage()
    caller = pre.deploy_contract(
        code=(
            Op.POP(Op.CALL(gas=Op.GAS, address=middle))
            + Op.SSTORE(
                caller_storage.store_next(0, "probe_must_fail"),
                Op.CALL(gas=probe_gas, address=probe),
            )
        ),
    )

    # gas_limit at the cap means the caller's reservoir starts at 0.
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    post = {caller: Account(storage=caller_storage)}
    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.with_all_create_opcodes
@pytest.mark.valid_from("EIP8037")
def test_sstore_restoration_create_init_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Verify reservoir refunds unwind when CREATE init code REVERTs
    inside a sub-frame that also REVERTs.

    Wrapping the CREATE in an outer reverting frame isolates the
    rollback concern from the legitimate CREATE silent-failure refund
    (`create_account_state_gas` credited to the frame executing the
    CREATE opcode).  When the outer frame reverts, every refund that
    occurred inside it must unwind, leaving the caller's reservoir at
    its pre-call value.  A single-SSTORE probe sized to OOG by 1
    detects any leaked refund.
    """
    gas_costs = fork.gas_costs()
    # Probe SSTORE(0, 1): 2 pushes + cold storage write + state gas - 1,
    # so it OOGs by 1 when the reservoir is 0 and succeeds otherwise.
    probe_gas = (
        2 * gas_costs.GAS_VERY_LOW
        + gas_costs.GAS_COLD_STORAGE_WRITE
        + fork.sstore_state_gas()
        - 1
    )

    init_code = Op.SSTORE(0, 1) + Op.SSTORE(0, 0) + Op.REVERT(0, 0)
    probe = pre.deploy_contract(code=Op.SSTORE(0, 1))

    if create_opcode == Op.CREATE:
        create_call = Op.CREATE(0, 0, len(init_code))
    else:
        create_call = Op.CREATE2(0, 0, len(init_code), 0)

    # Inner contract performs the CREATE then REVERTs, so any refunds
    # (SSTORE restoration or CREATE silent-failure) applied during its
    # execution must unwind with the frame.
    inner = pre.deploy_contract(
        code=(
            Op.MSTORE(
                0,
                int.from_bytes(bytes(init_code), "big")
                << (256 - 8 * len(init_code)),
            )
            + Op.POP(create_call)
            + Op.REVERT(0, 0)
        ),
    )

    caller_storage = Storage()
    caller = pre.deploy_contract(
        code=(
            Op.POP(Op.CALL(gas=Op.GAS, address=inner))
            + Op.SSTORE(
                caller_storage.store_next(0, "probe_must_fail"),
                Op.CALL(gas=probe_gas, address=probe),
            )
        ),
    )

    # gas_limit at the cap means the caller's reservoir starts at 0.
    tx = Transaction(
        to=caller,
        gas_limit=fork.transaction_gas_limit_cap(),
        sender=pre.fund_eoa(),
    )

    post = {caller: Account(storage=caller_storage)}
    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.with_all_create_opcodes
@pytest.mark.valid_from("EIP8037")
def test_sstore_restoration_create_init_success(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Verify 0 to x to 0 reservoir refund applies across CREATE init.

    Init code writes and clears slot 0, then returns empty runtime.
    The CREATE succeeds (returns a nonzero address), confirming the
    restoration path works inside init and the refund doesn't disturb
    deployment.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()
    create_state_gas = fork.create_state_gas(code_size=0)

    init_code = (
        Op.SSTORE(0, 1)
        + Op.SSTORE.with_metadata(
            key_warm=True,
            original_value=0,
            current_value=1,
            new_value=0,
        )(0, 0)
        + Op.RETURN(0, 0)
    )

    if create_opcode == Op.CREATE:
        create_call = Op.CREATE(0, 0, len(init_code))
    else:
        create_call = Op.CREATE2(0, 0, len(init_code), 0)

    caller_storage = Storage()
    caller = pre.deploy_contract(
        code=(
            Op.MSTORE(
                0,
                int.from_bytes(bytes(init_code), "big")
                << (256 - 8 * len(init_code)),
            )
            + Op.SSTORE(
                caller_storage.store_next(True, "create_succeeded"),
                Op.GT(create_call, 0),
            )
        ),
    )

    tx = Transaction(
        to=caller,
        gas_limit=gas_limit_cap + create_state_gas + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {caller: Account(storage=caller_storage)}
    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.valid_from("EIP8037")
def test_sstore_restoration_reservoir_spillover(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify restoration refund when state gas spilled into gas_left.

    With tx.gas at the cap, reservoir is zero.  SSTORE 0 to 1 state
    gas comes from gas_left.  At x to 0 the refund goes to
    `state_gas_reservoir` (not back to gas_left), moving gas between
    buckets.  Block state gas is zero.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    code = Op.SSTORE(0, 1) + Op.SSTORE.with_metadata(
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )(0, 0)
    tx_regular = intrinsic_gas + code.gas_cost(fork) - sstore_state_gas

    contract = pre.deploy_contract(code=code)
    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], header_verify=Header(gas_used=tx_regular))],
        post={contract: Account(storage={0: 0})},
    )
