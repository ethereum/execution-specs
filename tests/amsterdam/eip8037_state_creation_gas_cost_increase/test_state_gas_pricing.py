"""
Test the core EIP-8037 state gas pricing and charge mechanism.

`cost_per_state_byte` is a fixed parameter (CPSB = 1530) derived from
a 150M reference block gas limit and a 120 GiB/year target state
growth. The state gas cost of any operation is its byte footprint
multiplied by CPSB.

The `charge_state_gas()` function draws from the state gas reservoir
first, then spills into gas_left. If both pools are insufficient, the
transaction runs out of gas.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Bytecode,
    CodeGasMeasure,
    Environment,
    Fork,
    Header,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
    TransactionReceipt,
    compute_create_address,
)
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version

BLOCK_GAS_LIMITS = [
    pytest.param(1_000_000, id="1M"),
    pytest.param(30_000_000, id="30M"),
    pytest.param(36_000_000, id="36M"),
    pytest.param(60_000_000, id="60M"),
    pytest.param(100_000_000, id="100M"),
    pytest.param(120_000_000, id="120M"),
    pytest.param(200_000_000, id="200M"),
    pytest.param(300_000_000, id="300M"),
    pytest.param(500_000_000, id="500M"),
    pytest.param(1_000_000_000, id="1G"),
]


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize("block_gas_limit", BLOCK_GAS_LIMITS)
@pytest.mark.valid_from("EIP8037")
def test_pricing_at_various_gas_limits(
    state_test: StateTestFiller,
    pre: Alloc,
    block_gas_limit: int,
    fork: Fork,
) -> None:
    """
    Test SSTORE succeeds at various block gas limits.

    EIP-8037 prices state gas at a constant `cost_per_state_byte`,
    independent of block gas limit. At each block size, an SSTORE
    zero-to-nonzero should succeed when given sufficient total gas.
    """
    storage = Storage()
    code = Op.SSTORE(
        storage.store_next(1),
        1,
        # gas accounting
        original_value=0,
        new_value=1,
    )
    env = Environment(gas_limit=block_gas_limit)

    gas_limit = (
        fork.transaction_intrinsic_cost_calculator()()
        + fork.transaction_top_frame_gas_calculator()()
        + code.gas_cost(fork)
    )

    tx_gas = min(gas_limit, block_gas_limit)

    contract = pre.deploy_contract(
        code=code,
    )

    # The state charge does not scale with the block gas limit, so the
    # header reports the same `gas_used` at 1M and at 1G.
    state_gas = code.state_cost(fork)
    execution_gas = gas_limit - state_gas
    expected_gas_used = max(execution_gas, state_gas)
    assert expected_gas_used == state_gas, (
        "expected state gas to dominate execution gas"
    )

    tx = Transaction(
        to=contract,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.parametrize(
    "gas_delta",
    [pytest.param(0, id="exact_fit"), pytest.param(-1, id="one_short")],
)
@pytest.mark.valid_from("EIP8037")
def test_charge_draws_entirely_from_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_delta: int,
) -> None:
    """
    Test state gas is drawn entirely from the reservoir.

    The inner frame is handed exactly its SSTORE's execution cost, so
    it has no `gas_left` to spill from and the state charge must come
    entirely from the reservoir. An exact reservoir succeeds; one gas
    short halts the frame.
    """
    inner_code = Op.SSTORE(0, 1)
    inner = pre.deploy_contract(code=inner_code)
    inner_gas = inner_code.execution_cost(fork)

    succeeds = gas_delta == 0
    storage = Storage()

    slot = storage.store_next(int(succeeds), "inner_succeeded")
    contract = pre.deploy_contract(
        code=Op.SSTORE(
            slot,
            Op.CALL(gas=inner_gas, address=inner),
            # gas accounting
            original_value=1,
            current_value=1,
            new_value=int(succeeds),
            key_warm=False,
        ),
        storage={slot: 1},
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=inner_code.state_cost(fork) + gas_delta,
        sender=pre.fund_eoa(),
    )

    post = {
        contract: Account(storage=storage),
        inner: Account(storage={0: int(succeeds)}),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "reservoir_fraction",
    [
        pytest.param(0, id="all_spilled"),
        pytest.param(2, id="half_spilled"),
        pytest.param(1, id="none_spilled"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_charge_spills_to_gas_left(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    reservoir_fraction: int,
) -> None:
    """
    Test state gas spills from reservoir to gas_left.

    When the reservoir has some gas but not enough to cover the full
    state charge, the remainder is taken from gas_left. The SSTORE
    should still succeed.
    """
    measured_code = Op.SSTORE(
        1,
        1,
        # gas accounting
        original_value=0,
        current_value=0,
        new_value=1,
        key_warm=False,
    )
    state_gas = measured_code.state_cost(fork)
    execution_gas = measured_code.execution_cost(fork)

    reservoir = state_gas // reservoir_fraction if reservoir_fraction else 0
    spill = state_gas - reservoir

    # Slot 0 already holds a value, so writing the measurement into it
    # is a nonzero write that adds no state gas of its own.
    result_slot = 0
    contract = pre.deploy_contract(
        code=CodeGasMeasure(code=measured_code, sstore_key=result_slot),
        storage={result_slot: 1},
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=reservoir,
        sender=pre.fund_eoa(),
    )

    post = {
        contract: Account(
            storage={
                result_slot: execution_gas + spill,
                1: 1,
            }
        )
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "gas_delta",
    [pytest.param(0, id="exact_fit"), pytest.param(-1, id="one_short")],
)
@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.valid_from("EIP8037")
def test_charge_spill_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_delta: int,
) -> None:
    """
    Test the SSTORE-set state charge at its exact-fit spill boundary.

    With an empty reservoir (in-cap tx) the full state charge spills
    into gas_left. Sized to exactly the charge the SSTORE succeeds and
    the block bills it as state gas; one gas short, neither pool can
    cover the charge and the frame runs out of gas with the slot unset.
    """
    code = Op.SSTORE(
        0,
        1,
        # gas accounting
        original_value=0,
        new_value=1,
    )
    contract = pre.deploy_contract(code=code)

    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    execution = code.execution_cost(fork)
    state = code.state_cost(fork)
    gas_limit = intrinsic + execution + state + gas_delta

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    header = Header(
        gas_used=max(intrinsic + execution, state)
        if gas_delta == 0
        else gas_limit
    )
    state_test(
        pre=pre,
        post={contract: Account(storage={0: 1 if gas_delta == 0 else 0})},
        tx=tx,
        blockchain_test_header_verify=header,
    )


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@pytest.mark.parametrize(
    "fund_from_reservoir",
    [
        pytest.param(False, id="spilled_from_gas_left"),
        pytest.param(True, id="drawn_from_reservoir"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_refund_cap_includes_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    fund_from_reservoir: bool,
) -> None:
    """
    Test the 1/5 refund cap counts state gas whichever pool funds it.

    The cap applies to the combined execution plus state gas consumed,
    and the gas used before the refund is the same whether the state
    charge spills from `gas_left` or draws from the reservoir. Both
    variants therefore expect the identical refund: one the execution
    dimension alone would have capped short.
    """
    cleared_slots = 3
    set_slots = 3

    storage = Storage()
    code = Bytecode()
    for _ in range(cleared_slots):
        code += Op.SSTORE(
            storage.store_next(0, "cleared"),
            0,
            # gas accounting
            original_value=1,
            current_value=1,
            new_value=0,
            key_warm=False,
        )
    for _ in range(set_slots):
        code += Op.SSTORE(
            storage.store_next(1, "set"),
            1,
            # gas accounting
            original_value=0,
            current_value=0,
            new_value=1,
            key_warm=False,
        )
    contract = pre.deploy_contract(
        code=code,
        storage=dict.fromkeys(range(cleared_slots), 1),
    )

    state_gas = code.state_cost(fork)
    execution_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + code.execution_cost(fork)
    )
    before_refund = execution_gas + state_gas
    refund = min(before_refund // 5, code.refund(fork))
    # Counting the state charge lifts the cap above the refund,
    # While execution gas alone would cut it short.
    assert refund == code.refund(fork)
    assert execution_gas // fork.max_refund_quotient() < code.refund(fork)

    # Block accounting ignores refunds, so the header still reports the
    # dominant pre-refund dimension.
    expected_gas_used = max(execution_gas, state_gas)
    assert expected_gas_used == state_gas

    tx = Transaction(
        to=contract,
        state_gas_reservoir=state_gas if fund_from_reservoir else 0,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=before_refund - refund
        ),
    )

    post = {contract: Account(storage=storage)}
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@pytest.mark.valid_from("EIP8037")
def test_refund_with_reservoir_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test refund when state gas is drawn from reservoir.

    When state gas comes from the reservoir, the refund still applies.
    The refund_counter accumulates state + execution gas refunds, and
    the 1/5 cap uses tx_gas_used_before_refund which accounts for
    both dimensions. An SSTORE zero-to-nonzero-to-zero sequence
    should refund correctly.
    """
    kept = Op.SSTORE(0, 1, original_value=0, current_value=0, new_value=1)
    restored = Op.SSTORE(
        1, 1, original_value=0, current_value=0, new_value=1
    ) + Op.SSTORE(
        1, 0, key_warm=True, original_value=0, current_value=1, new_value=0
    )
    code = kept + restored
    contract = pre.deploy_contract(code=code)

    net_state_gas = code.state_cost(fork) - code.state_refund(fork)
    refund_counter = code.refund(fork) - code.state_refund(fork)
    gas_used_before_refund = (
        fork.transaction_intrinsic_cost_calculator()()
        + fork.transaction_top_frame_gas_calculator()(contract_creation=False)
        + code.execution_cost(fork)
        + net_state_gas
    )
    refund = min(
        gas_used_before_refund // fork.max_refund_quotient(), refund_counter
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=code.state_cost(fork),
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=gas_used_before_refund - refund
        ),
    )

    post = {contract: Account(storage={0: 1, 1: 0})}
    state_test(pre=pre, post=post, tx=tx)


def _access_list_over_execution_cap(
    fork: Fork, cap: int, *, margin_num: int = 1, margin_den: int = 1
) -> list[AccessList]:
    """
    Build an access list whose intrinsic *execution* gas exceeds ``cap`` by
    roughly the factor ``margin_num / margin_den``.

    Each access-list address adds a fixed amount to the execution intrinsic
    (the EIP-2930 address cost plus the EIP-7981 floor-token surcharge) and
    a much smaller amount to the calldata floor, so the list raises the
    execution operand of ``max(intrinsic_execution, calldata_floor)`` over the
    cap while the floor stays below it. No state gas is incurred.
    """
    intrinsic = fork.transaction_intrinsic_cost_calculator()
    base_execution = intrinsic(return_cost_deducted_prior_execution=True)
    per_address_execution = (
        intrinsic(
            access_list=[AccessList(address=Address(0x100), storage_keys=[])],
            return_cost_deducted_prior_execution=True,
        )
        - base_execution
    )
    assert per_address_execution > 0
    num_entries = (cap * margin_num) // (
        per_address_execution * margin_den
    ) + 1
    return [
        AccessList(address=Address(0x10000 + i), storage_keys=[])
        for i in range(num_entries)
    ]


@pytest.mark.inclusion_test
@pytest.mark.exception_test
@pytest.mark.valid_from("EIP8037")
def test_intrinsic_execution_gas_exceeds_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Reject a transaction whose intrinsic *execution* gas exceeds the cap.

    EIP-8037 enforces ``max(intrinsic_execution, calldata_floor) <=
    TX_MAX_GAS_LIMIT`` after the separate sufficiency check
    ``max(intrinsic_total, calldata_floor) <= tx.gas``. A large access list
    raises the execution intrinsic over the cap while adding no state gas and
    keeping the calldata floor below the cap. ``gas_limit`` is set above the
    total intrinsic so the sufficiency check passes and the cap is the only
    reason the transaction is rejected; a client that compares the intrinsic
    against ``tx.gas`` but never against the cap would wrongly accept it.
    """
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None
    floor_cost = fork.transaction_data_floor_cost_calculator()
    intrinsic = fork.transaction_intrinsic_cost_calculator()

    access_list = _access_list_over_execution_cap(fork, cap)
    execution = intrinsic(
        access_list=access_list,
        return_cost_deducted_prior_execution=True,
    )
    floor = floor_cost(data=b"", access_list=access_list)
    tx_gas = execution + 1_000_000

    assert max(execution, floor) > cap, "cap check must fire"
    assert execution <= tx_gas, "sufficiency check must not fire"
    assert floor <= tx_gas

    tx = Transaction(
        ty=1,
        to=pre.deploy_contract(code=Op.STOP),
        gas_limit=tx_gas,
        access_list=access_list,
        sender=pre.fund_eoa(),
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )
    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.inclusion_test
@pytest.mark.exception_test
@pytest.mark.valid_from("EIP8037")
def test_intrinsic_execution_gas_exceeds_cap_with_floor_below_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Reject when intrinsic *execution* gas exceeds the cap while the calldata
    floor stays below it, isolating the execution operand of
    ``max(intrinsic_execution, calldata_floor)``.

    A large access list with no calldata pushes the execution intrinsic over
    the cap while the floor stays well below it, and ``gas_limit`` covers
    the total intrinsic so the sufficiency check passes. The explicit
    ``floor < cap`` assertion guarantees the rejection comes from the
    execution operand, so a client that compares only the calldata floor
    against the cap would wrongly accept the transaction.
    """
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None
    floor_cost = fork.transaction_data_floor_cost_calculator()
    intrinsic = fork.transaction_intrinsic_cost_calculator()

    access_list = _access_list_over_execution_cap(
        fork, cap, margin_num=5, margin_den=4
    )
    execution = intrinsic(
        access_list=access_list,
        return_cost_deducted_prior_execution=True,
    )
    floor = floor_cost(data=b"", access_list=access_list)
    tx_gas = execution + 1_000_000

    assert execution > cap, "execution operand must exceed the cap"
    assert floor < cap, "calldata floor must stay below the cap"
    assert execution <= tx_gas, "sufficiency check must not fire"

    tx = Transaction(
        ty=1,
        to=pre.deploy_contract(code=Op.STOP),
        gas_limit=tx_gas,
        access_list=access_list,
        sender=pre.fund_eoa(),
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )
    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_intrinsic_within_cap_gas_limit_above_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Accept a transaction whose ``gas_limit`` exceeds the cap when both
    intrinsic operands stay below it.

    EIP-8037 relaxes the EIP-7825 cap on ``tx.gas`` itself; only
    ``max(intrinsic_execution, calldata_floor)`` is capped. This positive
    control sets ``gas_limit`` above the cap with a small access list so
    both operands are far below it, and the transaction must execute. It is
    the accepting counterpart to the cap-rejection tests above.
    """
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None
    floor_cost = fork.transaction_data_floor_cost_calculator()
    intrinsic = fork.transaction_intrinsic_cost_calculator()

    access_list = [
        AccessList(address=Address(0x10000 + i), storage_keys=[])
        for i in range(16)
    ]
    execution = intrinsic(
        access_list=access_list,
        return_cost_deducted_prior_execution=True,
    )
    floor = floor_cost(data=b"", access_list=access_list)
    assert execution <= cap
    assert floor <= cap

    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    tx = Transaction(
        ty=1,
        to=contract,
        gas_limit=cap + 3_000_000,
        access_list=access_list,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={contract: Account(storage=storage)}, tx=tx)


@pytest.mark.inclusion_test
@pytest.mark.parametrize(
    "above_floor",
    [
        pytest.param(
            False,
            id="below_floor",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(True, id="at_floor"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_calldata_floor_enforced_with_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    above_floor: bool,
) -> None:
    """
    Test EIP-7623 calldata floor is enforced when EIP-8037 is active.

    Send 100 non-zero calldata bytes to a call transaction so the
    execution intrinsic cost is below the calldata floor. A gas_limit
    at the floor succeeds; one below the floor is rejected.
    """
    calldata = b"\x01" * 100
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    floor_cost = fork.transaction_data_floor_cost_calculator()

    execution_gas = intrinsic_cost(
        calldata=calldata,
        return_cost_deducted_prior_execution=True,
    )
    floor_gas = floor_cost(data=calldata)
    assert floor_gas > execution_gas, "floor must exceed execution for test"

    if above_floor:
        gas_limit = floor_gas
        error = None
    else:
        # Between execution and floor: satisfies execution but not floor
        gas_limit = (execution_gas + floor_gas) // 2
        error = TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST

    tx = Transaction(
        to=pre.fund_eoa(0),
        data=calldata,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
        error=error,
    )

    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.parametrize("block_gas_limit", BLOCK_GAS_LIMITS)
@pytest.mark.valid_from("EIP8037")
def test_create_state_gas_scales_with_cpsb(
    state_test: StateTestFiller,
    pre: Alloc,
    block_gas_limit: int,
    fork: Fork,
) -> None:
    """
    Test CREATE new-account state gas scales with block gas limit.

    State gas for a CREATE is 120 * cpsb (new account) plus
    code_size * cpsb (code deposit).
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment(gas_limit=block_gas_limit)
    create_state_gas = fork.create_state_gas(code_size=1)

    storage = Storage()
    contract_code = Op.SSTORE(
        storage.store_next(1, "create_success"),
        Op.GT(Op.CREATE(0, 0, 1), 0),
    )
    contract = pre.deploy_contract(code=contract_code)

    state_gas = contract_code.state_cost(fork)
    execution_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + contract_code.execution_cost(fork)
    )
    expected_gas_used = max(execution_gas, state_gas)
    assert expected_gas_used == state_gas, (
        "expected state gas to dominate execution gas"
    )

    tx_gas = min(gas_limit_cap + create_state_gas, block_gas_limit)
    tx = Transaction(
        to=contract,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.parametrize("block_gas_limit", BLOCK_GAS_LIMITS)
@pytest.mark.valid_from("EIP8037")
def test_code_deposit_state_gas_scales_with_cpsb(
    state_test: StateTestFiller,
    pre: Alloc,
    block_gas_limit: int,
    fork: Fork,
) -> None:
    """
    Test the code-deposit state gas holds across block gas limits.

    Code deposit is the only charge billed per byte rather than per
    account or slot, so it is the most sensitive to the state-byte
    price. A creation transaction deposits a fixed body and the header
    must report the state dimension at every block gas limit.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment(gas_limit=block_gas_limit)

    code_size = 512
    init_code = Op.RETURN(
        0,
        code_size,
        # gas accounting
        code_deposit_size=code_size,
        new_memory_size=code_size,
    )
    deposit_state_gas = init_code.state_cost(fork)
    assert deposit_state_gas > 0, "the deposit must carry a state charge"

    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        calldata=bytes(init_code),
        contract_creation=True,
        return_cost_deducted_prior_execution=True,
    )
    state_gas = (
        fork.transaction_top_frame_state_gas(contract_creation=True)
        + deposit_state_gas
    )
    execution_gas = intrinsic_execution + init_code.execution_cost(fork)
    expected_gas_used = max(execution_gas, state_gas)
    assert expected_gas_used == state_gas, (
        "expected state gas to dominate execution gas"
    )

    sender = pre.fund_eoa()
    created = compute_create_address(address=sender, nonce=0)
    tx = Transaction(
        to=None,
        data=init_code,
        gas_limit=min(execution_gas + state_gas, block_gas_limit),
        sender=sender,
    )

    state_test(
        env=env,
        pre=pre,
        post={created: Account(code=b"\x00" * code_size)},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.parametrize("block_gas_limit", BLOCK_GAS_LIMITS)
@pytest.mark.valid_from("EIP8037")
def test_call_new_account_state_gas_scales_with_cpsb(
    state_test: StateTestFiller,
    pre: Alloc,
    block_gas_limit: int,
    fork: Fork,
) -> None:
    """
    Test CALL value transfer to empty account scales with block gas limit.

    Sending value to a non-existent account charges 120 * cpsb
    of state gas for account creation.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment(gas_limit=block_gas_limit)
    empty = pre.fund_eoa(0)
    call = Op.CALL(
        gas=100_000,
        address=empty,
        value=1,
        value_transfer=True,
        account_new=True,
    )
    storage = Storage()
    contract_code = Op.SSTORE(storage.store_next(1, "call_success"), call)
    contract = pre.deploy_contract(code=contract_code, balance=1)

    state_gas = contract_code.state_cost(fork)
    execution_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + contract_code.execution_cost(fork)
        # The empty target returns the value-call stipend unused.
        - fork.call_value_stipend()
    )
    expected_gas_used = max(execution_gas, state_gas)
    assert expected_gas_used == state_gas, (
        "expected state gas to dominate execution gas"
    )

    tx_gas = min(gas_limit_cap + call.state_cost(fork), block_gas_limit)
    tx = Transaction(
        to=contract,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.parametrize("block_gas_limit", BLOCK_GAS_LIMITS)
@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_new_beneficiary_scales_with_cpsb(
    state_test: StateTestFiller,
    pre: Alloc,
    block_gas_limit: int,
    fork: Fork,
) -> None:
    """
    Test SELFDESTRUCT to new beneficiary scales with block gas limit.

    Destructing to a non-existent address with balance charges
    120 * cpsb of state gas for the new beneficiary account.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment(gas_limit=block_gas_limit)
    new_account_state_gas = Op.SELFDESTRUCT(account_new=True).state_cost(fork)

    beneficiary = pre.fund_eoa(0)
    storage = Storage()
    caller_code = Op.SSTORE(
        storage.store_next(1, "selfdestruct_ran"), 1
    ) + Op.SELFDESTRUCT(beneficiary, account_new=True)
    caller = pre.deploy_contract(code=caller_code, balance=1)

    state_gas = caller_code.state_cost(fork)
    execution_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + caller_code.execution_cost(fork)
    )
    expected_gas_used = max(execution_gas, state_gas)
    assert expected_gas_used == state_gas, (
        "expected state gas to dominate execution gas"
    )

    tx_gas = min(gas_limit_cap + new_account_state_gas, block_gas_limit)
    tx = Transaction(
        to=caller,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
    )

    post = {caller: Account(storage=storage)}
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.parametrize("block_gas_limit", BLOCK_GAS_LIMITS)
@pytest.mark.valid_from("EIP8037")
def test_sstore_refund_scales_with_cpsb(
    state_test: StateTestFiller,
    pre: Alloc,
    block_gas_limit: int,
    fork: Fork,
) -> None:
    """
    Test SSTORE restoration refund scales with block gas limit.

    Zero-to-nonzero-to-zero in the same tx refunds the state gas
    (64 * cpsb) via refund_counter.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment(gas_limit=block_gas_limit)
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    code = Op.SSTORE(
        0,
        1,
        # gas accounting
        original_value=0,
        current_value=0,
        new_value=1,
        key_warm=False,
    ) + Op.SSTORE(
        0,
        0,
        # gas accounting
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )
    contract = pre.deploy_contract(code=code)

    # Restoring the slot hands the whole state charge straight back to
    # its own dimension, so none of it is billed; only the execution
    # refund passes through the one fifth cap.
    net_state_gas = code.state_cost(fork) - code.state_refund(fork)
    assert net_state_gas == 0

    refund_counter = code.refund(fork) - code.state_refund(fork)

    gas_used_before_refund = (
        fork.transaction_intrinsic_cost_calculator()()
        + fork.transaction_top_frame_gas_calculator()(contract_creation=False)
        + code.execution_cost(fork)
        + net_state_gas
    )

    refund = min(
        gas_used_before_refund // fork.max_refund_quotient(), refund_counter
    )

    tx_gas = min(gas_limit_cap + sstore_state_gas, block_gas_limit)
    tx = Transaction(
        to=contract,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=gas_used_before_refund - refund
        ),
    )

    post = {contract: Account(storage={0: 0})}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("block_gas_limit", BLOCK_GAS_LIMITS)
@pytest.mark.valid_from("EIP8037")
def test_auth_state_gas_scales_with_cpsb(
    state_test: StateTestFiller,
    pre: Alloc,
    block_gas_limit: int,
    fork: Fork,
) -> None:
    """
    Test SetCode authorization top-frame state gas scales with cpsb.

    Under EIP-2780 an authorization's state-dependent cost is charged at
    the top frame, not the intrinsic. An existing authority gaining a
    fresh delegation pays ``AUTH_BASE`` (= STATE_BYTES_PER_AUTH_BASE *
    cost_per_state_byte) of state gas there. The tx gas is sized so the
    charge draws from the reservoir when block_gas_limit is large and
    spills into gas_left when it is small; the delegated call must succeed
    in every regime.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment(gas_limit=block_gas_limit)

    # A cheap STOP delegate: the delegated call only needs to resolve and
    # succeed to prove the delegation applied; the state gas under test is
    # the top-frame AUTH_BASE, not the delegate's own work.
    delegate = pre.deploy_contract(code=Op.STOP)
    signer = pre.fund_eoa()

    authorization_list = [
        AuthorizationTuple(
            address=delegate,
            nonce=0,
            signer=signer,
            creates_account=False,
            writes_delegation=True,
        ),
    ]
    # Top-frame state gas for the existing authority's fresh delegation
    # (AUTH_BASE = STATE_BYTES_PER_AUTH_BASE * cpsb).
    auth_state_gas = fork.transaction_top_frame_state_gas(
        authorizations=authorization_list,
    )

    storage = Storage()
    target_code = Op.SSTORE(
        storage.store_next(1, "delegated_call_success"),
        Op.CALL(gas=100_000, address=signer, delegated_address=True),
    )

    target = pre.deploy_contract(code=target_code)

    state_gas = auth_state_gas + target_code.state_cost(fork)
    execution_gas = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=authorization_list
    ) + target_code.execution_cost(fork)

    expected_gas_used = max(execution_gas, state_gas)
    assert expected_gas_used == state_gas, (
        "expected state gas to dominate execution gas"
    )

    tx_gas = min(gas_limit_cap + auth_state_gas, block_gas_limit)
    tx = Transaction(
        ty=4,
        to=target,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
        authorization_list=authorization_list,
    )

    post = {target: Account(storage=storage)}
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )
