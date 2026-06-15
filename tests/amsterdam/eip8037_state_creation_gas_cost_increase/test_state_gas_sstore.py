"""
Test SSTORE state gas charging under EIP-8037.

Zero-to-nonzero storage writes charge
`STATE_BYTES_PER_STORAGE_SET * cost_per_state_byte` of state gas.
Nonzero-to-nonzero writes charge no state gas. 0 to x to 0 restoration
in the same tx refunds state gas directly to `state_gas_reservoir`
(inline at x to 0) and the regular write-cost portion to
`refund_counter`.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
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
) -> None:
    """
    Test SSTORE zero-to-nonzero charges state gas.

    Writing a nonzero value to a previously-zero slot charges
    STATE_BYTES_PER_STORAGE_SET * cost_per_state_byte of state gas
    in addition to regular gas.
    """
    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_sstore_nonzero_to_nonzero(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test SSTORE nonzero-to-nonzero charges no state gas.

    Updating a slot that already holds a nonzero value to a different
    nonzero value does not create new state, so no state gas is charged.
    """
    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(2), 2),
        storage={0: 1},
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_sstore_nonzero_to_zero(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test SSTORE nonzero-to-zero charges no state gas.

    Clearing a storage slot (setting to zero) does not grow state and
    earns a regular gas refund (GAS_STORAGE_CLEAR_REFUND).
    """
    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(0), 0),
        storage={0: 1},
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_sstore_zero_to_zero(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test SSTORE zero-to-zero charges no state gas.

    Writing zero to an already-zero slot creates no new state. Only
    the warm access regular gas cost is charged.
    """
    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(0), 0),
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "refund_sufficient",
    [
        pytest.param(True, id="refund_funds_create"),
        pytest.param(False, id="no_refund_create_oogs"),
    ],
)
@pytest.mark.parametrize(
    "delegatecall_depth",
    [
        pytest.param(1, id="depth_1"),
        pytest.param(3, id="depth_3"),
        pytest.param(10, id="depth_10"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_sstore_restoration_refund_credits_local_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    delegatecall_depth: int,
    refund_sufficient: bool,
) -> None:
    """
    Verify a same transaction SSTORE restoration refund credits the
    clearing frame's own reservoir immediately so later state gas in
    that frame is funded. Parametrized to pin the refund as necessary
    and sufficient.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    create_state_gas = fork.create_state_gas()
    # Premise: the two restoration refunds must be able to cover the
    # CREATE's new-account state gas for the funded path to exist.
    # Drift-proof relationship (vs. hardcoding the constants).
    assert 2 * sstore_state_gas >= create_state_gas

    # Sentinel written only if the CREATE returned (frame did not OOG).
    sentinel_slot = 2
    # refund: clear (1→0, restoration refund). no refund: modify
    # (1→2, no state growth, no refund) — same regular shape.
    cleared_value = 0 if refund_sufficient else 2
    clearing = pre.deploy_contract(
        code=(
            Op.SSTORE(0, cleared_value)
            + Op.SSTORE(1, cleared_value)
            + Op.POP(Op.CREATE(0, 0, 0))
            + Op.SSTORE(sentinel_slot, 1)
            + Op.STOP
        )
    )
    inner: Address = clearing
    for _ in range(delegatecall_depth):
        inner = pre.deploy_contract(
            code=(Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=inner)) + Op.STOP)
        )
    parent = pre.deploy_contract(
        code=(
            Op.SSTORE(0, 1)
            + Op.SSTORE(1, 1)
            + Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=inner))
            + Op.STOP
        )
    )

    # The two parent `0→1` sets spill their state gas into `gas_left`
    # (tx is far below the per-tx cap, so no state-gas reservoir).
    # Budget regular headroom for the call chain plus that spill, then
    # sit mid-window: short of also spill-funding `create_state_gas`,
    # so only a refund-credited reservoir can cover the CREATE.
    regular_headroom = 200_000
    gas_limit = regular_headroom + 2 * sstore_state_gas + create_state_gas // 2

    if refund_sufficient:
        post = {parent: Account(storage={0: 0, 1: 0, sentinel_slot: 1})}
    else:
        # CREATE OOGs in the clearing frame; its writes (the 1→2
        # modifications and the sentinel) revert, leaving the parent's
        # original sets intact.
        post = {parent: Account(storage={0: 1, 1: 1})}

    tx = Transaction(
        to=parent,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@pytest.mark.valid_from("EIP8037")
def test_sstore_restoration_refund(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test SSTORE zero-to-nonzero-to-zero restoration refunds state gas.

    When a slot is written from zero to nonzero and then restored to
    zero in the same transaction, the state gas charge
    (STATE_BYTES_PER_STORAGE_SET * cost_per_state_byte) is refunded
    via refund_counter along with the regular gas write cost.
    """
    contract = pre.deploy_contract(
        code=(Op.SSTORE(0, 1) + Op.SSTORE(0, 0)),
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    # Slot 0 restored to zero — state gas refunded
    post = {contract: Account(storage={0: 0})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_sstore_restoration_nonzero_no_state_refund(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test nonzero-to-nonzero-to-original restoration has no state gas refund.

    When a slot holds a nonzero original value, changing it and
    restoring it never involves state gas (no state growth occurred),
    so only regular gas refunds apply.
    """
    contract = pre.deploy_contract(
        code=(Op.SSTORE(0, 2) + Op.SSTORE(0, 1)),
        storage={0: 1},
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage={0: 1})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_sstore_clear_refund_reversal(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test clearing a nonzero slot then un-clearing reverses the refund.

    When a slot with a nonzero original value is cleared (set to zero),
    the clear refund is granted. If the slot is then set back to a
    nonzero value, the clear refund is reversed via refund_counter.
    """
    contract = pre.deploy_contract(
        code=(Op.SSTORE(0, 0) + Op.SSTORE(0, 2)),
        storage={0: 1},
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
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
) -> None:
    """
    Test multiple zero-to-nonzero SSTOREs each charge state gas.

    Each slot written from zero to nonzero independently charges
    STATE_BYTES_PER_STORAGE_SET * cost_per_state_byte of state gas.
    """
    storage = Storage()
    code = Bytecode()
    for _ in range(num_slots):
        code += Op.SSTORE(storage.store_next(1), 1)
    contract = pre.deploy_contract(code=code)

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.with_all_typed_transactions
@pytest.mark.valid_from("EIP8037")
def test_sstore_state_gas_all_tx_types(
    state_test: StateTestFiller,
    pre: Alloc,
    typed_transaction: Transaction,
) -> None:
    """
    Test SSTORE state gas works across all transaction types.

    With the gas limit pinned to the cap (zero reservoir), each tx
    type's SSTORE state gas spills into gas_left despite differing
    intrinsic costs.
    """
    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    tx = typed_transaction.copy(to=contract, state_gas_reservoir=0)

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
    stipend = gas_costs.CALL_STIPEND + 1
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    # Child: Op.SSTORE(0, 1) = 2 pushes + SSTORE opcode.
    child_code = Op.SSTORE(0, 1)
    child = pre.deploy_contract(child_code)

    # Full regular gas for the child (pushes + SSTORE regular cost).
    # State gas comes from the reservoir so it doesn't affect gas_left.
    child_full_regular = child_code.gas_cost(fork) - sstore_state_gas

    # below_stipend: give 1 less than stipend after pushes, fails check.
    # at_stipend: give full regular gas, passes check and completes.
    if gas_above_stipend < 0:
        push_gas = 2 * gas_costs.VERY_LOW
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

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        state_gas_reservoir=sstore_state_gas,
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
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
        state_gas_reservoir=num_cycles * sstore_state_gas,
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
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
        state_gas_reservoir=num_0_to_1 * sstore_state_gas,
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
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
        state_gas_reservoir=sstore_state_gas,
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
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
        state_gas_reservoir=sstore_state_gas,
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
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
        state_gas_reservoir=sstore_state_gas,
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
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
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    # CALL targets callee's storage; CALLCODE/DELEGATECALL target caller's.
    slot_owner = child if call_opcode == Op.CALL else parent
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], header_verify=Header(gas_used=tx_regular))],
        post={slot_owner: Account(storage={0: 0})},
    )


@pytest.mark.parametrize(
    "num_hops",
    [
        pytest.param(1, id="single_hop"),
        pytest.param(2, id="two_hops"),
        pytest.param(3, id="three_hops"),
        pytest.param(10, id="ten_hops"),
    ],
)
@pytest.mark.with_all_call_opcodes(
    selector=lambda call_opcode: call_opcode in (Op.DELEGATECALL, Op.CALLCODE)
)
@pytest.mark.valid_from("EIP8037")
def test_sstore_restoration_charge_in_ancestor(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
    num_hops: int,
) -> None:
    """
    Verify 0 to x to 0 refund when the 0 to x charge is in the parent
    and x to 0 runs `num_hops` DELEGATECALL/CALLCODE frames below,
    each sharing storage with the parent.

    Every intermediate frame has zero local `state_gas_used`, so the
    refund must propagate up the chain to the ancestor that charged
    the 0 to x.  A probe SSTORE sized to OOG by 1 detects any loss.
    """
    gas_costs = fork.gas_costs()
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    probe_gas = (
        2 * gas_costs.VERY_LOW
        + gas_costs.COLD_STORAGE_WRITE
        + sstore_state_gas
        - 1
    )

    # Innermost frame does x to 0; each hop above delegates down.
    delegate_target = pre.deploy_contract(
        code=(
            Op.SSTORE.with_metadata(
                key_warm=True,
                original_value=0,
                current_value=1,
                new_value=0,
            )(0, 0)
            + Op.STOP
        )
    )
    for _ in range(num_hops - 1):
        delegate_target = pre.deploy_contract(
            code=Op.POP(call_opcode(gas=Op.GAS, address=delegate_target))
            + Op.STOP,
        )

    probe = pre.deploy_contract(code=Op.SSTORE(0, 1))

    parent_storage = Storage()
    parent_code = (
        Op.SSTORE(parent_storage.store_next(0, "cycle_restored"), 1)
        + Op.POP(call_opcode(gas=Op.GAS, address=delegate_target))
        + Op.SSTORE(
            parent_storage.store_next(1, "probe_must_succeed"),
            Op.CALL(gas=probe_gas, address=probe),
        )
    )
    parent = pre.deploy_contract(code=parent_code)

    # Reservoir starts at exactly sstore_state_gas; the parent's 0 to 1
    # drains it to zero before entering the delegation chain.
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=parent,
        state_gas_reservoir=sstore_state_gas,
    )

    post = {parent: Account(storage=parent_storage)}
    state_test(pre=pre, tx=tx, post=post)


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
    Verify 0 to x to 0 reservoir refund returns to the caller on
    sub-frame REVERT.

    The sub-call performs 0 to x to 0 then REVERTs.  Since both the
    set-charge and its refund roll back together, the
    `state_gas_used + state_gas_left` sum reflects the unconsumed
    reservoir and is returned to the caller via
    `incorporate_child_on_error`.  A single-SSTORE probe sized to OOG
    by 1 succeeds, confirming the caller's reservoir was replenished.
    """
    gas_costs = fork.gas_costs()
    # Probe SSTORE(0, 1): 2 pushes + cold storage write + state gas - 1,
    # so it OOGs by 1 when the reservoir is 0 and succeeds otherwise.
    probe_gas = (
        2 * gas_costs.VERY_LOW
        + gas_costs.COLD_STORAGE_WRITE
        + Op.SSTORE(new_value=1).state_cost(fork)
        - 1
    )

    child_code = Op.SSTORE(0, 1) + Op.SSTORE(0, 0) + Op.REVERT(0, 0)
    child = pre.deploy_contract(code=child_code)
    probe = pre.deploy_contract(code=Op.SSTORE(0, 1))

    # Forward all remaining gas so the child completes both SSTOREs
    # and REVERT without a hard-coded budget.
    caller_storage = Storage()
    caller_code = Op.POP(call_opcode(gas=Op.GAS, address=child)) + Op.SSTORE(
        caller_storage.store_next(1, "probe_must_succeed"),
        Op.CALL(gas=probe_gas, address=probe),
    )
    caller = pre.deploy_contract(code=caller_code)

    # gas_limit at the cap means reservoir starts at 0 pre-call.
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        state_gas_reservoir=0,
    )

    post = {caller: Account(storage=caller_storage)}
    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.with_all_call_opcodes(
    selector=lambda call_opcode: call_opcode != Op.STATICCALL
)
@pytest.mark.valid_from("EIP8037")
def test_sstore_restoration_ancestor_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
) -> None:
    """
    Verify the SSTORE 0 to x to 0 refund returns to the caller when an
    ancestor frame (not the applying frame itself) reverts.

    Inner frame applies the refund and returns successfully; its
    `state_gas_left` (inflated by the refund) propagates to middle
    via `incorporate_child_on_success`.  Middle then REVERTs; the
    refunded reservoir flows back to the caller via
    `incorporate_child_on_error`, so the caller's reservoir is
    replenished by `sstore_state_gas`.
    """
    gas_costs = fork.gas_costs()
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    # Probe SSTORE(0, 1): 2 pushes + cold storage write + state gas - 1,
    # so it OOGs by 1 when the reservoir is 0 and succeeds otherwise.
    probe_gas = (
        2 * gas_costs.VERY_LOW
        + gas_costs.COLD_STORAGE_WRITE
        + Op.SSTORE(new_value=1).state_cost(fork)
        - 1
    )

    set_op = Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=0,
        current_value=0,
        new_value=1,
    )(0, 1)
    clear_op = Op.SSTORE.with_metadata(
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )(0, 0)
    inner_code = set_op + clear_op + Op.STOP
    inner = pre.deploy_contract(code=inner_code)

    middle_code = Op.POP(Op.CALL(gas=Op.GAS, address=inner)) + Op.REVERT(0, 0)
    middle = pre.deploy_contract(code=middle_code)

    probe_code = Op.SSTORE(0, 1)
    probe = pre.deploy_contract(code=probe_code)

    caller_storage = Storage()
    caller_code = Op.POP(call_opcode(gas=Op.GAS, address=middle)) + Op.SSTORE(
        caller_storage.store_next(1, "probe_must_succeed"),
        Op.CALL(gas=probe_gas, address=probe),
    )
    caller = pre.deploy_contract(code=caller_code)

    # Block state gas commits: probe's SSTORE-set and caller's outer
    # SSTORE-set; inner's set+clear cancel before middle reverts and
    # don't propagate.  Header gas_used is max(regular, state).
    expected_regular = (
        intrinsic_cost
        + caller_code.regular_cost(fork)
        + middle_code.regular_cost(fork)
        + inner_code.regular_cost(fork)
        + probe_code.regular_cost(fork)
    )
    expected_state = 2 * Op.SSTORE(new_value=1).state_cost(fork)
    expected_gas_used = max(expected_regular, expected_state)

    # gas_limit at the cap means the caller's reservoir starts at 0.
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        state_gas_reservoir=0,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={caller: Account(storage=caller_storage)},
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.with_all_call_opcodes(
    selector=lambda call_opcode: call_opcode in (Op.DELEGATECALL, Op.CALLCODE)
)
@pytest.mark.valid_from("EIP8037")
def test_sstore_restoration_charge_in_ancestor_intermediate_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
) -> None:
    """
    Verify a deferred refund applied in an intermediate frame still
    flows back to the caller when that frame REVERTs.

    Caller's SSTORE charges; the matching clear in inner is deferred
    through the chain and lands on middle's own SSTORE-set during
    `incorporate_child_on_success`.  Middle REVERTs; the applied
    amount must reach the caller via `incorporate_child_on_error`.
    A probe SSTORE sized to OOG by 1 detects loss.
    """
    gas_costs = fork.gas_costs()
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    # Probe SSTORE(0, 1): 2 pushes + cold storage write + state gas - 1,
    # so it OOGs by 1 when the reservoir is 0 and succeeds otherwise.
    probe_gas = (
        2 * gas_costs.VERY_LOW
        + gas_costs.COLD_STORAGE_WRITE
        + sstore_state_gas
        - 1
    )

    inner_code = (
        Op.SSTORE.with_metadata(
            key_warm=True,
            original_value=0,
            current_value=1,
            new_value=0,
        )(0, 0)
        + Op.STOP
    )
    inner = pre.deploy_contract(code=inner_code)

    # Middle's own SSTORE on slot 1 supplies the `state_gas_used`
    # that inner's deferred credit lands on, then middle REVERTs.
    middle_code = (
        Op.SSTORE(1, 1)
        + Op.POP(call_opcode(gas=Op.GAS, address=inner))
        + Op.REVERT(0, 0)
    )
    middle = pre.deploy_contract(code=middle_code)

    probe_code = Op.SSTORE(0, 1)
    probe = pre.deploy_contract(code=probe_code)

    caller_storage = Storage()
    caller_code = (
        Op.SSTORE(caller_storage.store_next(1, "caller_set_persists"), 1)
        + Op.POP(call_opcode(gas=Op.GAS, address=middle))
        + Op.SSTORE(
            caller_storage.store_next(1, "probe_must_succeed"),
            Op.CALL(gas=probe_gas, address=probe),
        )
    )
    caller = pre.deploy_contract(code=caller_code)

    # Block state gas commits: caller's slot-0 set + probe's
    # SSTORE-set + caller's outer SSTORE-set on slot 1.  Middle's
    # own slot-1 set is washed by inner's deferred credit before
    # middle reverts, so it does not propagate.  Header gas_used
    # is max(regular, state).
    expected_regular = (
        intrinsic_cost
        + caller_code.regular_cost(fork)
        + middle_code.regular_cost(fork)
        + inner_code.regular_cost(fork)
        + probe_code.regular_cost(fork)
    )
    expected_state = 3 * sstore_state_gas
    expected_gas_used = max(expected_regular, expected_state)

    # Reservoir = 2 * sstore_state_gas covers caller's and middle's
    # sets; the deferred credit refills middle by sstore_state_gas,
    # which flows to the caller on revert.
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        state_gas_reservoir=2 * sstore_state_gas,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={caller: Account(storage=caller_storage)},
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.with_all_create_opcodes
@pytest.mark.valid_from("EIP8037")
def test_sstore_restoration_create_init_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Verify reservoir refunds return to the caller when CREATE init
    code REVERTs inside a sub-frame that also REVERTs.

    Wrapping the CREATE in an outer reverting frame isolates the
    rollback concern from the legitimate CREATE silent-failure refund
    (`create_account_state_gas` credited to the frame executing the
    CREATE opcode).  When the outer frame reverts, the refunded
    reservoir flows back to the caller via
    `incorporate_child_on_error`, replenishing the caller's
    reservoir by at least `sstore_state_gas`.  A single-SSTORE probe
    sized to OOG by 1 succeeds, confirming the propagation.
    """
    gas_costs = fork.gas_costs()
    # Probe SSTORE(0, 1): 2 pushes + cold storage write + state gas - 1,
    # so it OOGs by 1 when the reservoir is 0 and succeeds otherwise.
    probe_gas = (
        2 * gas_costs.VERY_LOW
        + gas_costs.COLD_STORAGE_WRITE
        + Op.SSTORE(new_value=1).state_cost(fork)
        - 1
    )

    init_code = Op.SSTORE(0, 1) + Op.SSTORE(0, 0) + Op.REVERT(0, 0)
    probe = pre.deploy_contract(code=Op.SSTORE(0, 1))

    if create_opcode == Op.CREATE:
        create_call = Op.CREATE(0, 0, len(init_code))
    else:
        create_call = Op.CREATE2(0, 0, len(init_code), 0)

    # Inner contract performs the CREATE then REVERTs.
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
                caller_storage.store_next(1, "probe_must_succeed"),
                Op.CALL(gas=probe_gas, address=probe),
            )
        ),
    )

    # gas_limit at the cap means the caller's reservoir starts at 0.
    tx = Transaction(
        to=caller,
        state_gas_reservoir=0,
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
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
        state_gas_reservoir=create_state_gas + sstore_state_gas,
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
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
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], header_verify=Header(gas_used=tx_regular))],
        post={contract: Account(storage={0: 0})},
    )
