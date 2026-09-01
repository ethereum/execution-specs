"""
Test SSTORE state gas charging under EIP-8037.

Zero-to-nonzero storage writes charge
`STATE_BYTES_PER_STORAGE_SET * cost_per_state_byte` of state gas.
Nonzero-to-nonzero writes charge no state gas. 0 to x to 0 restoration
in the same tx refunds state gas directly to `state_gas_reservoir`
(inline at x to 0) and the execution write-cost portion to
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
    CodeGasMeasure,
    Conditional,
    Fork,
    Header,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionReceipt,
)
from execution_testing.checklists import EIPChecklist

from .spec import init_code_at_high_bytes, ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


def sender_gas_used(fork: Fork, pre_refund_gas: int, code: Bytecode) -> int:
    """
    Return the sender's bill for a transaction whose top frame ran `code`.
    """
    execution_refund = code.refund(fork) - code.state_refund(fork)
    return pre_refund_gas - min(
        pre_refund_gas // fork.max_refund_quotient(), execution_refund
    )


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
    STATE_BYTES_PER_STORAGE_SET * cost_per_state_byte of state gas
    in addition to execution gas.
    """
    storage = Storage()
    code = Op.SSTORE(storage.store_next(1), 1)
    state_gas = code.state_cost(fork)
    tx_execution = (
        fork.transaction_intrinsic_cost_calculator()()
        + code.execution_cost(fork)
    )
    assert state_gas > tx_execution, "state dimension must set the header"

    contract = pre.deploy_contract(code=code)

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=tx_execution + state_gas
        ),
    )

    state_test(
        pre=pre,
        post={contract: Account(storage=storage)},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=state_gas),
    )


@pytest.mark.valid_from("EIP8037")
def test_sstore_nonzero_to_nonzero(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SSTORE nonzero-to-nonzero charges no state gas.

    Updating a slot that already holds a nonzero value to a different
    nonzero value does not create new state, so no state gas is charged
    and the header reports the execution dimension alone.
    """
    storage = Storage()
    code = Op.SSTORE(
        storage.store_next(2),
        2,
        original_value=1,
        current_value=1,
        new_value=2,
    )
    assert code.state_cost(fork) == 0, "no state growth, no state gas"
    tx_execution = (
        fork.transaction_intrinsic_cost_calculator()()
        + code.execution_cost(fork)
    )

    contract = pre.deploy_contract(code=code, storage={0: 1})

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(cumulative_gas_used=tx_execution),
    )

    state_test(
        pre=pre,
        post={contract: Account(storage=storage)},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=tx_execution),
    )


@pytest.mark.valid_from("EIP8037")
def test_sstore_nonzero_to_zero(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SSTORE nonzero-to-zero charges no state gas.

    Clearing a storage slot (setting to zero) does not grow state and
    earns an execution gas refund (GAS_STORAGE_CLEAR_REFUND).
    """
    storage = Storage()
    code = Op.SSTORE(
        storage.store_next(0),
        0,
        original_value=1,
        current_value=1,
        new_value=0,
    )
    assert code.state_cost(fork) == 0, "clearing a slot grows no state"
    assert code.refund(fork) > 0, "clearing a slot must earn a refund"
    pre_refund_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + code.execution_cost(fork)
    )

    contract = pre.deploy_contract(code=code, storage={0: 1})

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=sender_gas_used(fork, pre_refund_gas, code)
        ),
    )

    state_test(
        pre=pre,
        post={contract: Account(storage=storage)},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=pre_refund_gas),
    )


@pytest.mark.valid_from("EIP8037")
def test_sstore_zero_to_zero(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SSTORE zero-to-zero charges no state gas.

    Writing zero to an already-zero slot creates no new state. Only
    the warm access execution gas cost is charged.
    """
    storage = Storage()
    code = Op.SSTORE(storage.store_next(0), 0, new_value=0)
    assert code.state_cost(fork) == 0, "a no-op write grows no state"
    tx_execution = (
        fork.transaction_intrinsic_cost_calculator()()
        + code.execution_cost(fork)
    )

    contract = pre.deploy_contract(code=code)

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(cumulative_gas_used=tx_execution),
    )

    state_test(
        pre=pre,
        post={contract: Account(storage=storage)},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=tx_execution),
    )


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
    # (1→2, no state growth, no refund) — same execution shape.
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
    # Budget execution headroom for the call chain plus that spill, then
    # sit mid-window: short of also spill-funding `create_state_gas`,
    # so only a refund-credited reservoir can cover the CREATE.
    execution_headroom = 200_000
    gas_limit = (
        execution_headroom + 2 * sstore_state_gas + create_state_gas // 2
    )

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
    fork: Fork,
) -> None:
    """
    Test SSTORE zero-to-nonzero-to-zero restoration refunds state gas.

    When a slot is written from zero to nonzero and then restored to
    zero in the same transaction, the state gas charge
    (STATE_BYTES_PER_STORAGE_SET * cost_per_state_byte) is refunded
    via refund_counter along with the execution gas write cost.
    """
    code = Op.SSTORE(0, 1) + Op.SSTORE(
        0,
        0,
        # gas accounting
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )
    assert code.state_refund(fork) == code.state_cost(fork), (
        "the restoration must refund the whole state charge"
    )
    pre_refund_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + code.execution_cost(fork)
    )

    contract = pre.deploy_contract(code=code)

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=sender_gas_used(fork, pre_refund_gas, code)
        ),
    )

    state_test(
        pre=pre,
        post={contract: Account(storage={0: 0})},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=pre_refund_gas),
    )


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
    so only execution gas refunds apply.
    """
    code = Op.SSTORE(
        0,
        2,
        # gas accounting
        original_value=1,
        current_value=1,
        new_value=2,
    ) + Op.SSTORE(
        0,
        1,
        # gas accounting
        key_warm=True,
        original_value=1,
        current_value=2,
        new_value=1,
    )
    assert code.state_cost(fork) == 0, "a nonzero slot grows no state"
    assert code.state_refund(fork) == 0, "no state charge, no state refund"
    assert code.refund(fork) > 0, "the execution write cost is refunded"
    pre_refund_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + code.execution_cost(fork)
    )

    contract = pre.deploy_contract(code=code, storage={0: 1})

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=sender_gas_used(fork, pre_refund_gas, code)
        ),
    )

    state_test(
        pre=pre,
        post={contract: Account(storage={0: 1})},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=pre_refund_gas),
    )


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
    nonzero value, the clear refund is reversed via refund_counter, so
    the sender pays the full pre-refund gas.
    """
    code = Op.SSTORE(
        0,
        0,
        # gas accounting
        original_value=1,
        current_value=1,
        new_value=0,
    ) + Op.SSTORE(
        0,
        2,
        # gas accounting
        key_warm=True,
        original_value=1,
        current_value=0,
        new_value=2,
    )
    assert code.refund(fork) == 0, "the clear refund must be fully reversed"
    assert code.state_cost(fork) == 0, "a nonzero slot grows no state"
    tx_execution = (
        fork.transaction_intrinsic_cost_calculator()()
        + code.execution_cost(fork)
    )

    contract = pre.deploy_contract(code=code, storage={0: 1})

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(cumulative_gas_used=tx_execution),
    )

    state_test(
        pre=pre,
        post={contract: Account(storage={0: 2})},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=tx_execution),
    )


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
    fork: Fork,
    num_slots: int,
) -> None:
    """
    Test multiple zero-to-nonzero SSTOREs each charge state gas.

    Each slot written from zero to nonzero independently charges
    STATE_BYTES_PER_STORAGE_SET * cost_per_state_byte of state gas, so
    the state dimension scales with the slot count.
    """
    storage = Storage()
    code = Bytecode()
    for _ in range(num_slots):
        code += Op.SSTORE(storage.store_next(1), 1)

    state_gas = code.state_cost(fork)
    assert state_gas == num_slots * Op.SSTORE(new_value=1).state_cost(fork), (
        "every slot must be charged independently"
    )
    tx_execution = (
        fork.transaction_intrinsic_cost_calculator()()
        + code.execution_cost(fork)
    )
    assert state_gas > tx_execution, "state dimension must set the header"

    contract = pre.deploy_contract(code=code)

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=tx_execution + state_gas
        ),
    )

    state_test(
        pre=pre,
        post={contract: Account(storage=storage)},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=state_gas),
    )


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
    measured = Op.SSTORE(1, 1)
    measured_execution = measured.execution_cost(fork)
    sstore_state_gas = measured.state_cost(fork)

    # The recording SSTORE is itself a zero-to-nonzero set; its state
    # gas spills into gas_left because the measured set drained the
    # reservoir first.
    code = CodeGasMeasure(code=measured, sstore_key=0)
    state_gas = code.state_cost(fork)
    tx_execution = (
        fork.transaction_intrinsic_cost_calculator()()
        + code.execution_cost(fork)
    )
    assert state_gas > tx_execution, "state dimension must set the header"

    contract = pre.deploy_contract(code=code)

    tx = Transaction(
        to=contract,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=tx_execution + state_gas
        ),
    )

    state_test(
        pre=pre,
        post={contract: Account(storage={0: measured_execution, 1: 1})},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=state_gas),
    )


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
    Verify the SSTORE gas check uses gas_left only, not the reservoir.

    A child frame has gas_left at or just below the stipend threshold
    (GAS_CALL_STIPEND + 1) while the reservoir holds ample state gas.
    The check must fail when gas_left is too low, regardless of the
    reservoir balance.

    Post-8038 the cold access cost (COLD_STORAGE_ACCESS = 3000) exceeds
    the stipend (2300), so for this cold slot the access cost is the
    binding gate and the stipend sentry is subsumed. The reservoir is
    excluded either way, which is what this test pins down.

    With below_stipend: SSTORE fails (gas_left too low, reservoir ignored).
    With at_stipend: SSTORE has full execution gas and proceeds.
    """
    stipend = fork.call_value_stipend() + 1
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    # Child: Op.SSTORE(0, 1) = 2 pushes + SSTORE opcode.
    child_code = Op.SSTORE(0, 1)
    child = pre.deploy_contract(child_code)

    # Full execution gas for the child (pushes + SSTORE execution cost).
    # State gas comes from the reservoir so it doesn't affect gas_left.
    child_full_execution = child_code.execution_cost(fork)

    # below_stipend: give 1 less than stipend after pushes, fails check.
    # at_stipend: give full execution gas, passes check and completes.
    if gas_above_stipend < 0:
        push_gas = 2 * Op.PUSH1(0).execution_cost(fork)
        child_gas = push_gas + stipend - 1
    else:
        child_gas = child_full_execution

    # Caller forwards limited execution gas via CALL. State gas comes
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
        code += Op.SSTORE(i, 1) + Op.SSTORE(
            i,
            0,
            # gas accounting
            key_warm=True,
            original_value=0,
            current_value=1,
            new_value=0,
        )
    tx_execution = intrinsic_gas + code.execution_cost(fork)

    assert code.state_refund(fork) == num_cycles * sstore_state_gas, (
        "every cycle must refund its state charge"
    )

    contract = pre.deploy_contract(code=code)
    tx = Transaction(
        to=contract,
        state_gas_reservoir=num_cycles * sstore_state_gas,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=sender_gas_used(fork, tx_execution, code)
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], header_verify=Header(gas_used=tx_execution))],
        post={contract: Account(storage=dict.fromkeys(range(num_cycles), 0))},
    )


@pytest.mark.parametrize(
    "num_cycles,state_dominates",
    [
        pytest.param(1, True, id="one_cycle"),
        pytest.param(10, False, id="ten_cycles"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_sstore_restoration_mixed_with_genuine_sstore(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    num_cycles: int,
    state_dominates: bool,
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
    tx_execution = intrinsic_gas + code.execution_cost(fork)
    assert (sstore_state_gas > tx_execution) == state_dominates
    expected = max(tx_execution, sstore_state_gas)

    contract = pre.deploy_contract(code=code)
    tx = Transaction(
        to=contract,
        state_gas_reservoir=num_0_to_1 * sstore_state_gas,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=sender_gas_used(
                fork, tx_execution + sstore_state_gas, code
            )
        ),
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
    tx_execution = intrinsic_gas + code.execution_cost(fork)

    contract = pre.deploy_contract(code=code)
    tx = Transaction(
        to=contract,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], header_verify=Header(gas_used=tx_execution))],
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
    tx_execution = intrinsic_gas + code.execution_cost(fork)
    assert sstore_state_gas > tx_execution, (
        "the surviving state charge must set the header"
    )
    expected = max(tx_execution, sstore_state_gas)

    contract = pre.deploy_contract(code=code)
    tx = Transaction(
        to=contract,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=sender_gas_used(
                fork, tx_execution + sstore_state_gas, code
            )
        ),
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
    tx_execution = intrinsic_gas + code.execution_cost(fork)
    assert sstore_state_gas > tx_execution, "state gas must dominates"
    expected = max(tx_execution, sstore_state_gas)

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
    # Callee's execution gas excludes the state gas (refunded at x to 0).
    child_execution = child_code.execution_cost(fork)
    child = pre.deploy_contract(code=child_code)

    parent_code = Op.POP(call_opcode(gas=child_execution, address=child))
    parent = pre.deploy_contract(code=parent_code)

    tx_execution = (
        intrinsic_gas + parent_code.execution_cost(fork) + child_execution
    )

    tx = Transaction(
        to=parent,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    # CALL targets callee's storage; CALLCODE/DELEGATECALL target caller's.
    slot_owner = child if call_opcode == Op.CALL else parent
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], header_verify=Header(gas_used=tx_execution))],
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
    code = Op.SSTORE(0, 1, new_value=1)
    sstore_state_gas = code.state_cost(fork)
    probe_gas = code.gas_cost(fork) - 1

    # Innermost frame does x to 0; each hop above delegates down.
    delegate_target = pre.deploy_contract(
        code=(
            Op.SSTORE(
                0,
                0,
                # gas accounting
                key_warm=True,
                original_value=0,
                current_value=1,
                new_value=0,
            )
        )
    )
    for _ in range(num_hops - 1):
        delegate_target = pre.deploy_contract(
            code=Op.POP(call_opcode(gas=Op.GAS, address=delegate_target))
        )

    probe = pre.deploy_contract(code=code)

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
    Verify a sub-frame REVERT does not inflate the caller's reservoir
    under source-based (LIFO) refills.

    The sub-call does 0 to x to 0 then REVERTs. The set spilled its
    state gas from `gas_left`, so the refill at x to 0 returns it to
    `gas_left`, not the reservoir. On REVERT the state gas refills to
    the parent's `gas_left`, so the reservoir stays at 0. A probe sized
    to OOG by 1 then fails, since its fixed forwarded gas cannot reach
    the `gas_left` refund.
    """
    # Probe SSTORE(0, 1): 2 pushes + cold write + state gas - 1. OOGs by
    # 1 when the reservoir is 0, as forwarded gas misses gas_left.
    probe_gas = Op.SSTORE(0, 1).gas_cost(fork) - 1

    child_code = Op.SSTORE(0, 1) + Op.SSTORE(0, 0) + Op.REVERT(0, 0)
    child = pre.deploy_contract(code=child_code)
    probe = pre.deploy_contract(code=Op.SSTORE(0, 1))

    # Forward all gas so the child does both SSTOREs and REVERT.
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
    Verify an ancestor REVERT does not inflate the caller's reservoir
    under source-based (LIFO) refills.

    Inner's set spills its state gas from `gas_left`. The refill at
    x to 0 returns it to `gas_left`, and inner's
    `state_gas_spilled` propagates to middle on success. Middle
    then REVERTs, refilling the spilled state gas to the caller's
    `gas_left`, not the reservoir. The reservoir stays at 0, so a probe
    sized to OOG by 1 fails, since its fixed forwarded gas cannot reach
    the `gas_left` refund.
    """
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    # Probe SSTORE(0, 1): 2 pushes + cold write + state gas - 1. OOGs by
    # 1 when the reservoir is 0, as forwarded gas misses gas_left.
    probe_gas = Op.SSTORE(0, 1).gas_cost(fork) - 1

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
    # The probe OOGs and returns 0, so the caller's outer SSTORE is a
    # cold no-op (0 to 0) on a fresh slot, charging only
    # COLD_STORAGE_ACCESS rather than the cold set `execution_cost`
    # assumes by default.
    caller_code = Op.POP(
        call_opcode(gas=Op.GAS, address=middle)
    ) + Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=0,
        current_value=0,
        new_value=0,
    )(
        caller_storage.store_next(0, "probe_must_fail"),
        Op.CALL(gas=probe_gas, address=probe),
    )
    caller = pre.deploy_contract(code=caller_code)

    # No SSTORE-set persists (inner's set+clear cancel, middle reverts,
    # the probe OOGs and reverts, and the caller's outer SSTORE is a
    # no-op), so block state gas is zero and header gas_used (the max of
    # execution and state) is just the execution total. The probe burns its
    # full forwarded budget on the OOG; its CALL's cold-access surcharge
    # is already counted in the caller's execution cost.
    expected_gas_used = (
        intrinsic_cost
        + caller_code.execution_cost(fork)
        + middle_code.execution_cost(fork)
        + inner_code.execution_cost(fork)
        + probe_gas
    )

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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    # Probe SSTORE(0, 1): 2 pushes + cold storage write + state gas - 1,
    # so it OOGs by 1 when the reservoir is 0 and succeeds otherwise.
    probe_gas = Op.SSTORE(0, 1).gas_cost(fork) - 1

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
    # is max(execution, state).
    expected_execution = (
        intrinsic_cost
        + caller_code.execution_cost(fork)
        + middle_code.execution_cost(fork)
        + inner_code.execution_cost(fork)
        + probe_code.execution_cost(fork)
    )
    expected_state = 3 * sstore_state_gas
    expected_gas_used = max(expected_execution, expected_state)

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


@pytest.mark.parametrize(
    "ending",
    [
        pytest.param("success", id="all_frames_succeed"),
        pytest.param("top_revert", id="top_level_reverts"),
        pytest.param("middle_revert", id="middle_reverts_after_clear"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_cross_frame_refund_advance(
    state_test: StateTestFiller,
    pre: Alloc,
    ending: str,
) -> None:
    """
    Verify a restoration refund credited in a re-entered frame (an
    advance against the entry frame's spilled sets) discharges through
    the middle frame's merge on success, is void when the top level
    reverts, and is revoked when the middle frame reverts after the
    clear — leaving both slots set and the sender paying their full
    state gas.

    The tx gas limit sits below the EIP-7825 cap, so the reservoir is
    empty and the entry frame's sets spill from `gas_left`.
    """
    middle_ending = Op.REVERT(0, 0) if ending == "middle_revert" else Op.STOP
    middle = pre.deploy_contract(
        code=(
            Op.POP(Op.CALL(gas=Op.GAS, address=Op.CALLER, args_size=1))
            + middle_ending
        ),
    )

    entry_ending = Op.REVERT(0, 0) if ending == "top_revert" else Op.STOP
    entry = pre.deploy_contract(
        code=Conditional(
            condition=Op.CALLDATASIZE,
            # Re-entered: clear both slots; each refund is credited
            # here as an advance.
            if_true=Op.SSTORE(0, 0) + Op.SSTORE(1, 0) + Op.STOP,
            if_false=(
                Op.SSTORE(0, 1)
                + Op.SSTORE(1, 1)
                + Op.SSTORE(2, Op.CALL(gas=Op.GAS, address=middle))
                + entry_ending
            ),
        ),
    )

    tx = Transaction(
        to=entry,
        gas_limit=1_000_000,
        sender=pre.fund_eoa(),
    )

    if ending == "success":
        storage = {0: 0, 1: 0, 2: 1}
    elif ending == "top_revert":
        storage = {}
    else:
        storage = {0: 1, 1: 1, 2: 0}

    post = {entry: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


def revoked_advance_call_tree(pre: Alloc) -> Address:
    """
    Deploy a call tree whose entry sets two slots (both spilled), and
    whose middle frame — holding one spilled set of its own — value
    calls back into the entry, which imports a reverted child call and
    then clears both slots. The two-clear advance is only partially
    dischargeable against the middle frame's usage; the entry then
    exceptionally halts, revoking the rest.

    Returns the entry contract's address.
    """
    reverting = pre.deploy_contract(code=Op.SSTORE(0, 1) + Op.REVERT(0, 0))
    middle = pre.deploy_contract(
        code=(
            Op.SSTORE(0, 1)
            + Op.POP(Op.CALL(gas=Op.GAS, address=Op.CALLER, value=1))
            + Op.STOP
        ),
        balance=1,
    )
    return pre.deploy_contract(
        code=Conditional(
            condition=Op.CALLVALUE,
            if_true=(
                Op.POP(Op.CALL(gas=Op.GAS, address=reverting))
                + Op.SSTORE(0, 0)
                + Op.SSTORE(1, 0)
                + Op.STOP
            ),
            if_false=(
                Op.SSTORE(0, 1)
                + Op.SSTORE(1, 1)
                + Op.POP(Op.CALL(gas=Op.GAS, address=middle))
                + Op.INVALID
            ),
        ),
    )


@pytest.mark.valid_from("EIP8037")
def test_partially_discharged_advance_revoked_by_halt(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify an advance only partially dischargeable in the middle frame
    (two clears against one middle set) is fully revoked when the entry
    frame exceptionally halts, so the sender pays the entry's whole
    forwarded budget and the caller's accounting is undisturbed. The
    receipt pins the billing: the halted entry consumes its whole
    forwarded budget as execution gas and the caller's slot-1 set is
    the only surviving state charge.
    """
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    entry_budget = 600_000
    entry = revoked_advance_call_tree(pre)

    storage = Storage()
    # The entry call OOGs and returns 0, so the caller's first SSTORE
    # is a cold no-op (0 to 0) on a fresh slot rather than the cold set
    # `execution_cost` assumes by default.
    caller_code = Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=0,
        current_value=0,
        new_value=0,
    )(
        storage.store_next(0, "entry_halted"),
        Op.CALL(gas=entry_budget, address=entry),
    ) + Op.SSTORE(storage.store_next(1, "caller_completed"), 1)
    caller = pre.deploy_contract(code=caller_code)

    expected_cumulative = (
        intrinsic_cost
        + caller_code.execution_cost(fork)
        + entry_budget
        + sstore_state_gas
    )

    tx = Transaction(
        to=caller,
        gas_limit=1_000_000,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative,
        ),
    )

    post = {
        caller: Account(storage=storage),
        entry: Account(storage={0: 0, 1: 0}),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.with_all_create_opcodes
@pytest.mark.valid_from("EIP8037")
def test_sstore_restoration_create_init_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Verify a reverting CREATE sub-frame does not inflate the caller's
    reservoir under source-based (LIFO) refills.

    The init code spills its state gas from `gas_left`, does 0 to x to 0
    and REVERTs. The CREATE is wrapped in an outer frame that also
    REVERTs. Each refill returns the spilled state gas to `gas_left`,
    and the reverts refill it to the caller's `gas_left`, not the
    reservoir. The reservoir stays at 0, so a probe sized to OOG by 1
    fails, since its fixed forwarded gas cannot reach the `gas_left`
    refund.
    """
    # Probe SSTORE(0, 1): 2 pushes + cold write + state gas - 1. OOGs by
    # 1 when the reservoir is 0, as forwarded gas misses gas_left.
    probe_gas = Op.SSTORE(0, 1).gas_cost(fork) - 1

    init_code = Op.SSTORE(0, 1) + Op.SSTORE(0, 0) + Op.REVERT(0, 0)
    probe = pre.deploy_contract(code=Op.SSTORE(0, 1))

    mstore_value, init_code_size = init_code_at_high_bytes(init_code)
    if create_opcode == Op.CREATE:
        create_call = Op.CREATE(0, 0, init_code_size)
    else:
        create_call = Op.CREATE2(0, 0, init_code_size, 0)

    # Inner contract performs the CREATE then REVERTs.
    inner = pre.deploy_contract(
        code=Op.MSTORE(0, mstore_value)
        + Op.POP(create_call)
        + Op.REVERT(0, 0),
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

    mstore_value, init_code_size = init_code_at_high_bytes(init_code)
    if create_opcode == Op.CREATE:
        create_call = Op.CREATE(0, 0, init_code_size)
    else:
        create_call = Op.CREATE2(0, 0, init_code_size, 0)

    probe_code = Op.SSTORE(0, 1)
    probe = pre.deploy_contract(code=probe_code)
    probe_gas = probe_code.execution_cost(fork)

    caller_storage = Storage()
    create_slot = caller_storage.store_next(True, "create_succeeded")
    probe_slot = caller_storage.store_next(1, "probe_succeeds")
    caller = pre.deploy_contract(
        code=Op.MSTORE(0, mstore_value)
        + Op.SSTORE(
            create_slot,
            Op.GT(create_call, 0),
            # gas accounting
            original_value=1,
            current_value=1,
            new_value=1,
            key_warm=False,
        )
        + Op.SSTORE(
            probe_slot,
            Op.CALL(gas=probe_gas, address=probe),
            # gas accounting
            original_value=1,
            current_value=1,
            new_value=1,
            key_warm=False,
        ),
        storage={create_slot: 1, probe_slot: 1},
    )

    # Sized for the CREATE's account creation plus the probe's SSTORE:
    # the init frame's set and clear net to zero.
    tx = Transaction(
        to=caller,
        state_gas_reservoir=create_state_gas + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {
        caller: Account(storage=caller_storage),
        probe: Account(storage={0: 1}),
    }
    state_test(pre=pre, tx=tx, post=post)
