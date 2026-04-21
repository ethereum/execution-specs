"""
Test state gas consumption ordering under EIP-8037.

When an opcode charges both regular gas and state gas, regular gas MUST
be charged first. If regular gas OOGs, state gas is not consumed. This
prevents the parent's reservoir from being inflated on frame failure.

Each test gives a child frame exactly 1 gas less than needed, then uses
a probe contract to detect whether the parent's reservoir was inflated
by incorrectly consumed state gas.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Initcode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


def _single_sstore_probe_gas(fork: Fork) -> int:
    """
    Return the gas for a single-SSTORE probe that OOGs by 1 when the
    reservoir is 0 but succeeds when the reservoir holds any state gas.

    The probe bytecode is Op.SSTORE(0, 1): two pushes + SSTORE.
    """
    gas_costs = fork.gas_costs()
    sstore_regular = gas_costs.COLD_STORAGE_WRITE
    sstore_state = fork.sstore_state_gas()
    push_gas = 2 * gas_costs.VERY_LOW
    return push_gas + sstore_regular + sstore_state - 1


@pytest.mark.valid_from("EIP8037")
def test_sstore_oog_reservoir_inflation_detection(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Detect SSTORE state gas ordering via reservoir inflation.

    A factory does CREATE + SSTORE where SSTORE OOGs (1 gas short).
    After factory failure, the parent's reservoir should contain only
    CREATE's state gas. A probe contract tests this by doing 4 SSTOREs
    that need more total state gas than the correct reservoir but less
    than the inflated one.

    With correct ordering (regular gas first): probe OOGs on 4th SSTORE.
    With wrong ordering (state gas first): reservoir is inflated,
    probe succeeds.
    """
    gas_costs = fork.gas_costs()
    initcode = Initcode(deploy_code=Op.STOP)
    initcode_len = len(initcode)

    factory_code = Op.CALLDATACOPY(
        0,
        0,
        Op.CALLDATASIZE,
        data_size=initcode_len,
        new_memory_size=initcode_len,
    ) + Op.SSTORE(
        0,
        Op.CREATE(
            value=0,
            offset=0,
            size=Op.CALLDATASIZE,
            init_code_size=initcode_len,
        ),
    )
    factory = pre.deploy_contract(factory_code)

    factory_gas = (
        factory_code.gas_cost(fork)
        + initcode.execution_gas(fork)
        + initcode.deployment_gas(fork)
    )

    # Probe: 4 SSTOREs to cold slots. Total state gas exceeds the
    # correct reservoir (CREATE state gas only) but fits within the
    # inflated reservoir (CREATE + SSTORE state gas).
    probe = pre.deploy_contract(
        Op.SSTORE(0, 1) + Op.SSTORE(1, 1) + Op.SSTORE(2, 1) + Op.SSTORE(3, 1)
    )

    # Compute probe gas: enough for 4 SSTOREs' regular gas + pushes,
    # but after 4th regular charge, gas_left < the state gas spill.
    sstore_regular = gas_costs.COLD_STORAGE_WRITE
    sstore_state = fork.sstore_state_gas()
    push_per_sstore = 2 * gas_costs.VERY_LOW
    create_state_gas = fork.create_state_gas(
        code_size=len(initcode.deploy_code)
    )
    spill = 4 * sstore_state - create_state_gas
    probe_gas = 4 * (push_per_sstore + sstore_regular) + spill // 2

    caller_storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.POP(
            Op.CALL(
                gas=factory_gas - 1,
                address=factory,
                value=0,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
                ret_offset=0,
                ret_size=0,
            )
        )
        + Op.SSTORE(
            caller_storage.store_next(0, "probe_must_fail"),
            Op.CALL(gas=probe_gas, address=probe),
        )
    )

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=caller,
        data=bytes(initcode),
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    post = {
        caller: Account(storage=caller_storage),
    }

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.valid_from("EIP8037")
def test_call_oog_reservoir_inflation_detection(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Detect CALL state gas ordering via reservoir inflation.

    A child does CALL(value=1) to a dead address with gas tuned so
    the regular gas charge OOGs by 1. If state gas (new account) is
    incorrectly charged first, the parent's reservoir is inflated.

    A single-SSTORE probe detects the inflation: with correct reservoir
    (0) it OOGs; with inflated reservoir it succeeds.
    """
    gas_costs = fork.gas_costs()
    new_account_state_gas = gas_costs.NEW_ACCOUNT

    dead_address = 0xDEAD
    child_code = Op.CALL(
        gas=0,
        address=dead_address,
        value=1,
        args_offset=0,
        args_size=0,
        ret_offset=0,
        ret_size=0,
    )
    pushes_gas = 7 * gas_costs.VERY_LOW
    call_regular_gas = gas_costs.COLD_ACCOUNT_ACCESS + gas_costs.CALL_VALUE
    child_gas = pushes_gas + call_regular_gas + new_account_state_gas - 1
    child = pre.deploy_contract(child_code)

    probe = pre.deploy_contract(Op.SSTORE(0, 1))
    probe_gas = _single_sstore_probe_gas(fork)

    caller_storage = Storage()
    caller = pre.deploy_contract(
        Op.POP(Op.CALL(gas=child_gas, address=child))
        + Op.SSTORE(
            caller_storage.store_next(0, "probe_must_fail"),
            Op.CALL(gas=probe_gas, address=probe),
        )
    )

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=caller,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    post = {caller: Account(storage=caller_storage)}
    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_oog_reservoir_inflation_detection(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Detect SELFDESTRUCT state gas ordering via reservoir inflation.

    A child with non-zero balance does SELFDESTRUCT(dead_beneficiary)
    with gas tuned so the regular gas charge OOGs by 1. If state gas
    is incorrectly charged first, the parent's reservoir is inflated.

    Single-SSTORE probe detects the inflation.
    """
    gas_costs = fork.gas_costs()
    new_account_state_gas = gas_costs.NEW_ACCOUNT

    dead_beneficiary = 0xBEEF
    child_code = Op.SELFDESTRUCT(dead_beneficiary)
    pushes_gas = gas_costs.VERY_LOW
    selfdestruct_regular_gas = (
        gas_costs.OPCODE_SELFDESTRUCT_BASE + gas_costs.COLD_ACCOUNT_ACCESS
    )
    child_gas = (
        pushes_gas + selfdestruct_regular_gas + new_account_state_gas - 1
    )
    child = pre.deploy_contract(child_code, balance=1)

    probe = pre.deploy_contract(Op.SSTORE(0, 1))
    probe_gas = _single_sstore_probe_gas(fork)

    caller_storage = Storage()
    caller = pre.deploy_contract(
        Op.POP(Op.CALL(gas=child_gas, address=child))
        + Op.SSTORE(
            caller_storage.store_next(0, "probe_must_fail"),
            Op.CALL(gas=probe_gas, address=probe),
        )
    )

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=caller,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    post = {caller: Account(storage=caller_storage)}
    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("EIP8037")
def test_create_oog_reservoir_inflation_detection(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Detect CREATE/CREATE2 state gas ordering via reservoir inflation.

    A child does CREATE (or CREATE2) with size=0 and gas tuned so the
    regular gas charge OOGs by 1. CREATE/CREATE2 already have the
    correct ordering (regular before state), so this is a regression
    test ensuring it stays that way.

    Single-SSTORE probe detects potential inflation.
    """
    gas_costs = fork.gas_costs()
    new_account_state_gas = gas_costs.NEW_ACCOUNT

    if create_opcode == Op.CREATE:
        child_code = create_opcode(value=0, offset=0, size=0)
        pushes_gas = 3 * gas_costs.VERY_LOW
    else:
        child_code = create_opcode(value=0, offset=0, size=0, salt=0)
        pushes_gas = 4 * gas_costs.VERY_LOW

    create_regular_gas = gas_costs.OPCODE_CREATE_BASE - new_account_state_gas
    child_gas = pushes_gas + create_regular_gas + new_account_state_gas - 1
    child = pre.deploy_contract(child_code)

    probe = pre.deploy_contract(Op.SSTORE(0, 1))
    probe_gas = _single_sstore_probe_gas(fork)

    caller_storage = Storage()
    caller = pre.deploy_contract(
        Op.POP(Op.CALL(gas=child_gas, address=child))
        + Op.SSTORE(
            caller_storage.store_next(0, "probe_must_fail"),
            Op.CALL(gas=probe_gas, address=probe),
        )
    )

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=caller,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    post = {caller: Account(storage=caller_storage)}
    state_test(pre=pre, tx=tx, post=post)
