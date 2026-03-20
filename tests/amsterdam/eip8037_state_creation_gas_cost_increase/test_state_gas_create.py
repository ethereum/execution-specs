"""
Test CREATE and CREATE2 state gas charging under EIP-8037.

Contract creation charges state gas for the new account and for
code deposit. Regular gas for CREATE is charged separately.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Fork,
    Initcode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
    compute_create_address,
)
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.valid_from("Amsterdam")
def test_create_charges_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test CREATE charges state gas for new account and code deposit.

    A successful CREATE charges new-account state gas plus code
    deposit state gas proportional to the deployed code size.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    init_code = Op.STOP

    storage = Storage()
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                0,
                int.from_bytes(bytes(init_code), "big")
                << (256 - 8 * len(init_code)),
            )
            + Op.SSTORE(
                storage.store_next(True),
                Op.GT(Op.CREATE(0, 0, len(init_code)), 0),
            )
        ),
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.CREATE, id="create"),
        pytest.param(Op.CREATE2, id="create2"),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_create_with_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    fork: Fork,
) -> None:
    """
    Test CREATE/CREATE2 with state gas funded from the reservoir.

    Provide gas above TX_MAX_GAS_LIMIT so the new account state gas
    is drawn from the reservoir rather than gas_left.
    """
    gas_costs = fork.gas_costs()
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    create_state_gas = gas_costs.GAS_NEW_ACCOUNT

    storage = Storage()
    init_code = Op.STOP

    if opcode == Op.CREATE:
        create_call = Op.CREATE(0, 0, len(init_code))
    else:
        create_call = Op.CREATE2(0, 0, len(init_code), 0)

    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                0,
                int.from_bytes(bytes(init_code), "big")
                << (256 - 8 * len(init_code)),
            )
            + Op.SSTORE(
                storage.store_next(True),
                Op.GT(create_call, 0),
            )
        ),
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + create_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "code_size",
    [
        pytest.param(1, id="tiny_code"),
        pytest.param(32, id="one_word"),
        pytest.param(256, id="small_contract"),
        pytest.param(1024, id="medium_contract"),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_code_deposit_state_gas_scales_with_size(
    state_test: StateTestFiller,
    pre: Alloc,
    code_size: int,
    fork: Fork,
) -> None:
    """
    Test code deposit state gas scales linearly with code size.

    The code deposit charges len(code) * cost_per_state_byte of state
    gas. Larger deployed code requires proportionally more state gas.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    # State gas: new account + code deposit
    total_state_gas = fork.create_state_gas(code_size=code_size)

    # Build init code that returns `code_size` bytes of 0x00
    # PUSH2 code_size, PUSH1 0, RETURN
    init_code = Op.RETURN(0, code_size)

    tx = Transaction(
        to=None,
        data=init_code,
        gas_limit=gas_limit_cap + total_state_gas,
        sender=pre.fund_eoa(),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_create_tx_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test contract creation transaction charges intrinsic state gas.

    A create transaction (to=None) charges new-account state gas
    as intrinsic state gas for the new account, plus code deposit state
    gas for the deployed bytecode.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    tx = Transaction(
        to=None,
        data=Op.STOP,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_create_revert_no_code_deposit_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test reverted CREATE does not charge code deposit state gas.

    When CREATE fails during init code execution (REVERT), the new
    account state gas is consumed but no code deposit state gas is
    charged because no code was deployed.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    init_code = Op.REVERT(0, 0)

    storage = Storage()
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                0,
                int.from_bytes(bytes(init_code), "big")
                << (256 - 8 * len(init_code)),
            )
            + Op.SSTORE(
                storage.store_next(0),  # CREATE returns 0 on failure
                Op.CREATE(0, 0, len(init_code)),
            )
        ),
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.valid_from("Amsterdam")
def test_create_insufficient_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test CREATE OOGs when state gas is insufficient.

    Provide enough gas for CREATE's regular gas cost but not enough
    to cover the new-account state gas. The CREATE should fail,
    returning 0.
    """
    init_code = Op.STOP

    storage = Storage()
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                0,
                int.from_bytes(bytes(init_code), "big")
                << (256 - 8 * len(init_code)),
            )
            + Op.SSTORE(
                storage.store_next(0),  # CREATE returns 0 on OOG
                Op.CREATE(0, 0, len(init_code)),
            )
        ),
    )

    # Tight gas — enough for intrinsic + CREATE regular gas but not
    # enough for the new account state gas
    gas_costs = fork.gas_costs()
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    regular_create_gas = gas_costs.GAS_CREATE - gas_costs.GAS_NEW_ACCOUNT
    gas_limit = intrinsic_cost() + regular_create_gas + 10_000

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_create2_address_collision(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test CREATE2 returns zero on address collision.

    When CREATE2 targets an address that already has code or storage,
    the collision is detected early and returns zero without charging
    state gas. The existing account is left unchanged.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    init_code = Op.STOP
    salt = 0

    storage = Storage()
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                0,
                int.from_bytes(bytes(init_code), "big")
                << (256 - 8 * len(init_code)),
            )
            # First CREATE2 succeeds
            + Op.SSTORE(
                storage.store_next(1, "first_create2"),
                Op.ISZERO(Op.ISZERO(Op.CREATE2(0, 0, len(init_code), salt))),
            )
            # Second CREATE2 with same salt collides
            + Op.SSTORE(
                storage.store_next(0, "collision_create2"),
                Op.CREATE2(0, 0, len(init_code), salt),
            )
        ),
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap * 2,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "gas_delta",
    [
        pytest.param(
            -1,
            id="below_intrinsic",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(0, id="at_intrinsic"),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_create_tx_intrinsic_gas_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_delta: int,
) -> None:
    """
    Test CREATE tx intrinsic gas boundary includes state component.

    The intrinsic gas for a contract-creating transaction includes
    both regular gas and state gas. A transaction with gas_limit
    exactly at the boundary succeeds; one gas below is rejected.
    """
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    gas_limit = intrinsic_cost(
        contract_creation=True,
    )

    tx = Transaction(
        to=None,
        gas_limit=gas_limit + gas_delta,
        sender=pre.fund_eoa(),
        error=(
            TransactionException.INTRINSIC_GAS_TOO_LOW
            if gas_delta < 0
            else None
        ),
    )

    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_nested_create_code_deposit_cannot_borrow_parent_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test nested CREATE code deposit does not borrow parent gas.

    Provide just enough gas for CREATE to start (new account state
    gas + regular gas) but not enough for the child frame to cover
    code deposit after init code runs. The CREATE increments the
    factory nonce but code deposit fails, so no contract is deployed.
    """
    init_code = Op.RETURN(0, 1)
    gas_costs = fork.gas_costs()
    new_acct_state = gas_costs.GAS_NEW_ACCOUNT
    code_deposit_state = fork.code_deposit_state_gas(code_size=1)

    factory = pre.deploy_contract(
        code=(
            Op.MSTORE(0, Op.PUSH32(bytes(init_code)))
            + Op.POP(
                Op.CREATE(
                    value=0,
                    offset=32 - len(init_code),
                    size=len(init_code),
                ),
            )
        ),
    )
    created = compute_create_address(address=factory, nonce=1)

    # Gas consumed before the child CREATE frame receives gas:
    # Intrinsic + factory code (PUSH32+PUSH1+MSTORE+mem +
    # 3xPUSH1) + CREATE regular (+ init_code_cost) + new account
    # state gas (spilled from gas_left, no reservoir).
    init_code_word_cost = gas_costs.GAS_CODE_INIT_PER_WORD * (
        (len(init_code) + 31) // 32
    )
    pre_child_gas = (
        gas_costs.GAS_TX_BASE
        + 7 * gas_costs.GAS_VERY_LOW
        + gas_costs.GAS_MEMORY
        + (gas_costs.GAS_CREATE - new_acct_state)
        + init_code_word_cost
        + new_acct_state
    )

    # Init code cost: PUSH1 + PUSH1 + RETURN(+mem expansion)
    init_cost = 2 * gas_costs.GAS_VERY_LOW + gas_costs.GAS_MEMORY
    # Target child gas: enough for init, not enough for code deposit
    target_child = (init_cost + code_deposit_state) // 2
    # Invert EIP-150 63/64ths rule: ceil(target_child * 64 / 63)
    factory_remaining = (target_child * 64 + 62) // 63
    gas_limit = pre_child_gas + factory_remaining

    tx = Transaction(
        to=factory,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    post = {
        factory: Account(nonce=2),
        created: Account.NONEXISTENT,
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "gas_shortfall",
    [
        pytest.param(0, id="exact_gas"),
        pytest.param(1, id="short_one_gas"),
    ],
)
@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("Amsterdam")
def test_max_initcode_size_gas_metering_via_create(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_shortfall: int,
    create_opcode: Op,
) -> None:
    """
    Verify 2D gas metering for CREATE with max initcode size.

    A caller contract forwards exact regular gas to a factory via CALL.
    State gas is supplied through the reservoir (tx.gas_limit above the
    cap). With short_one_gas, the factory is 1 regular gas short and
    all state changes revert.
    """
    initcode = Initcode(
        deploy_code=Op.STOP, initcode_length=fork.max_initcode_size()
    )
    alice = pre.fund_eoa()

    initcode_len = len(initcode)
    create_call = (
        create_opcode(
            value=0,
            offset=0,
            size=Op.CALLDATASIZE,
            salt=0xC0FFEE,
            init_code_size=initcode_len,
        )
        if create_opcode == Op.CREATE2
        else create_opcode(
            value=0,
            offset=0,
            size=Op.CALLDATASIZE,
            init_code_size=initcode_len,
        )
    )

    factory_code = (
        Op.CALLDATACOPY(
            0,
            0,
            Op.CALLDATASIZE,
            data_size=initcode_len,
            new_memory_size=initcode_len,
        )
        + Op.SSTORE(0, create_call)
        + Op.STOP
    )

    factory = pre.deploy_contract(factory_code)

    create_address = compute_create_address(
        address=factory,
        nonce=1,
        salt=0xC0FFEE,
        initcode=initcode,
        opcode=create_opcode,
    )

    # Split gas into regular and state components.
    # CALL gas only feeds gas_left; state gas must come from the reservoir.
    factory_gas = (
        factory_code.gas_cost(fork)
        + initcode.execution_gas(fork)
        + initcode.deployment_gas(fork)
    )
    factory_state_gas = (
        fork.create_state_gas(code_size=len(initcode.deploy_code))
        + fork.sstore_state_gas()
    )
    factory_regular_gas = factory_gas - factory_state_gas

    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.CALL(
            gas=factory_regular_gas - gas_shortfall,
            address=factory,
            value=0,
            args_offset=0,
            args_size=Op.CALLDATASIZE,
            ret_offset=0,
            ret_size=0,
        )
        + Op.STOP
    )

    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    tx = Transaction(
        sender=alice,
        to=caller,
        data=bytes(initcode),
        gas_limit=gas_limit_cap + factory_state_gas,
    )

    created = not gas_shortfall
    post = {
        create_address: Account(code=Op.STOP)
        if created
        else Account.NONEXISTENT,
        factory: Account(storage={0: create_address if created else 0}),
    }

    state_test(pre=pre, tx=tx, post=post)
