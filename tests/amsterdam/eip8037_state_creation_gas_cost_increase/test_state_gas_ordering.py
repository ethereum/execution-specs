"""
Test state gas consumption ordering under EIP-8037.

When an opcode charges both execution gas and state gas, execution gas MUST
be charged first. If execution gas OOGs, state gas is not consumed. This
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
    Block,
    BlockchainTestFiller,
    Fork,
    Header,
    Initcode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version

WORD_SIZE = 32


def _single_sstore_probe_gas(fork: Fork) -> int:
    """
    Return the gas for a single-SSTORE probe that OOGs by 1 when the
    reservoir is 0 but succeeds when the reservoir holds any state gas.

    The probe bytecode is Op.SSTORE(0, 1): two pushes + SSTORE.
    """
    return Op.SSTORE(0, 1).gas_cost(fork) - 1


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

    With correct ordering (execution gas first): probe OOGs on 4th SSTORE.
    With wrong ordering (state gas first): reservoir is inflated,
    probe succeeds.
    """
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
        + initcode.evm_gas(fork)
        + initcode.deployment_gas(fork)
    )

    # Probe: 4 SSTOREs to cold slots. Total state gas exceeds the
    # correct reservoir (CREATE state gas only) but fits within the
    # inflated reservoir (CREATE + SSTORE state gas).
    probe = pre.deploy_contract(
        Op.SSTORE(0, 1) + Op.SSTORE(1, 1) + Op.SSTORE(2, 1) + Op.SSTORE(3, 1)
    )

    # Compute probe gas: enough for 4 SSTOREs' execution gas + pushes,
    # but after 4th execution charge, gas_left < the state gas spill.
    sstore_state = Op.SSTORE(new_value=1).state_cost(fork)
    sstore_execution = Op.SSTORE(0, 1).execution_cost(fork)
    create_state_gas = fork.create_state_gas(
        code_size=len(initcode.deploy_code)
    )
    spill = 4 * sstore_state - create_state_gas
    probe_gas = 4 * sstore_execution + spill // 2

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
        state_gas_reservoir=0,
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
    the execution gas charge OOGs by 1. If state gas (new account) is
    incorrectly charged first, the parent's reservoir is inflated.

    A single-SSTORE probe detects the inflation: with correct reservoir
    (0) it OOGs; with inflated reservoir it succeeds.
    """
    dead_address = 0xDEAD
    child_code = Op.CALL(
        gas=0,
        address=dead_address,
        value=1,
        args_offset=0,
        args_size=0,
        ret_offset=0,
        ret_size=0,
        value_transfer=True,
        account_new=True,
    )
    # One gas short of the CALL's full cost (execution plus the NEW_ACCOUNT
    # state charge), so it OOGs on the account-creation charge.
    child_gas = child_code.gas_cost(fork) - 1
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
        state_gas_reservoir=0,
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
    with gas tuned so the execution gas charge OOGs by 1. If state gas
    is incorrectly charged first, the parent's reservoir is inflated.

    Single-SSTORE probe detects the inflation.
    """
    dead_beneficiary = 0xBEEF
    child_code = Op.SELFDESTRUCT(dead_beneficiary, account_new=True)
    # One gas short of the SELFDESTRUCT's full cost (execution plus the
    # NEW_ACCOUNT state charge), so it OOGs on the account-creation charge.
    child_gas = child_code.gas_cost(fork) - 1
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
        state_gas_reservoir=0,
    )

    post = {caller: Account(storage=caller_storage)}
    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "oog_step",
    [
        pytest.param("create_base", id="oog_on_create_base"),
        pytest.param("init_code_word_cost", id="oog_on_init_code_word_cost"),
    ],
)
@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("EIP8037")
def test_create_oog_reservoir_inflation_detection(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    oog_step: str,
) -> None:
    """
    Detect CREATE/CREATE2 state-gas ordering via parent-reservoir
    inflation. Two OOG boundaries are exercised: `oog_on_create_base`
    (empty initcode) and `oog_on_init_code_word_cost` (32-byte
    initcode).
    """
    if oog_step == "create_base":
        initcode_size = 0
    else:
        initcode_size = WORD_SIZE

    if create_opcode == Op.CREATE:
        create_op = create_opcode(
            value=0, offset=0, size=initcode_size, init_code_size=initcode_size
        )
    else:
        create_op = create_opcode(
            value=0,
            offset=0,
            size=initcode_size,
            salt=0,
            init_code_size=initcode_size,
        )

    if oog_step == "create_base":
        child_code = create_op
    else:
        child_code = Op.MSTORE(0, 0, new_memory_size=WORD_SIZE) + create_op

    # One gas short of the CREATE's full cost (execution plus the NEW_ACCOUNT
    # state charge), so it OOGs on the account-creation charge.
    child_gas = child_code.gas_cost(fork) - 1
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
        state_gas_reservoir=0,
    )

    post = {caller: Account(storage=caller_storage)}
    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "oog_step",
    [
        pytest.param("create_base", id="oog_on_create_base"),
        pytest.param("init_code_word_cost", id="oog_on_init_code_word_cost"),
    ],
)
@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("EIP8037")
def test_create_oog_full_burn_no_state_credit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    oog_step: str,
) -> None:
    """
    Verify a CREATE OOG inside a non-creation tx burns the whole
    tx gas_limit — no state-gas leftover is credited at tx-end.
    """
    if oog_step == "create_base":
        initcode_size = 0
    else:
        initcode_size = WORD_SIZE

    if create_opcode == Op.CREATE:
        create_op = create_opcode(
            value=0, offset=0, size=initcode_size, init_code_size=initcode_size
        )
    else:
        create_op = create_opcode(
            value=0,
            offset=0,
            size=initcode_size,
            salt=0,
            init_code_size=initcode_size,
        )

    if oog_step == "create_base":
        factory_code = create_op
    else:
        factory_code = Op.MSTORE(0, 0, new_memory_size=WORD_SIZE) + create_op
    factory = pre.deploy_contract(factory_code)

    # One gas short of the CREATE's full cost (execution plus the NEW_ACCOUNT
    # state charge), so it OOGs on the account-creation charge.
    body_gas = factory_code.gas_cost(fork) - 1

    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    tx_gas_limit = intrinsic_calc() + body_gas

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=factory,
        gas_limit=tx_gas_limit,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=tx_gas_limit),
            ),
        ],
        post={},
    )
