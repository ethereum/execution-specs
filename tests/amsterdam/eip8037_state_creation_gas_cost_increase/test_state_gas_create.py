"""
Test CREATE and CREATE2 state gas charging under EIP-8037.

Contract creation charges state gas for the new account and for
code deposit. Regular gas for CREATE is charged separately.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

from typing import Union

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
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


@pytest.fixture
def nonexistent_account(pre: Alloc) -> Address:
    """Return a fresh address that does not exist in pre-state."""
    return pre.fund_eoa(amount=0)


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
        pytest.param("max", id="max_code_size"),
        pytest.param("max+1", id="over_max_code_size"),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_code_deposit_state_gas_scales_with_size(
    state_test: StateTestFiller,
    pre: Alloc,
    code_size: Union[int, str],
    fork: Fork,
) -> None:
    """
    Test code deposit state gas scales linearly with code size.

    The code deposit charges len(code) * cost_per_state_byte of state
    gas. Larger deployed code requires proportionally more state gas.
    When code exceeds MAX_CODE_SIZE, the size check rejects before
    any gas is charged and the contract is not deployed.
    """
    if code_size == "max":
        code_size = fork.max_code_size()
    elif code_size == "max+1":
        code_size = fork.max_code_size() + 1
    assert isinstance(code_size, int)

    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    # State gas: new account + code deposit
    total_state_gas = fork.create_state_gas(code_size=code_size)

    # Build init code that returns `code_size` bytes of 0x00
    # PUSH2 code_size, PUSH1 0, RETURN
    init_code = Op.RETURN(0, code_size)

    sender = pre.fund_eoa()
    tx = Transaction(
        to=None,
        data=init_code,
        gas_limit=gas_limit_cap + total_state_gas,
        sender=sender,
    )

    if code_size > fork.max_code_size():
        create_address = compute_create_address(address=sender, nonce=0)
        post = {create_address: Account.NONEXISTENT}
    else:
        post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


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
def test_code_deposit_oog_preserves_parent_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test parent reservoir preserved after child code deposit OOG.

    A caller contract invokes the factory via CALL with limited gas.
    The child CREATE returns enough bytes that code deposit state gas
    exceeds the child frame's available gas (reservoir spillover plus
    the limited gas_left). The factory's SSTORE after the failed
    CREATE proves the reservoir was not inflated by a spill-then-halt
    refund.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    gas_costs = fork.gas_costs()
    new_account_state_gas = gas_costs.GAS_NEW_ACCOUNT
    sstore_state_gas = fork.sstore_state_gas()

    # Small deploy size; code deposit state gas will exceed the
    # limited gas available in the CREATE child frame.
    deploy_size = 4096
    init_code = Op.RETURN(0, deploy_size)

    # Limited regular gas forwarded to the factory.  After CREATE
    # takes 63/64, the factory retains ~15 K for its SSTOREs.
    child_gas = 1_000_000

    factory_storage = Storage()
    factory = pre.deploy_contract(
        code=(
            Op.MSTORE(0, Op.PUSH32(bytes(init_code)))
            + Op.SSTORE(
                factory_storage.store_next(0, "create_fails"),
                Op.CREATE(
                    value=0,
                    offset=32 - len(init_code),
                    size=len(init_code),
                ),
            )
            # Reservoir must be fully preserved after failed CREATE;
            # parent can still perform its own SSTORE.
            + Op.SSTORE(
                factory_storage.store_next(1, "parent_sstore"),
                1,
            )
        ),
    )

    # Caller invokes factory with limited gas via CALL.
    caller = pre.deploy_contract(
        code=Op.CALL(gas=child_gas, address=factory),
    )

    # Reservoir = new-account state gas + one SSTORE's state gas.
    # Code deposit draws from the reservoir first then spills into
    # gas_left, which the limited CALL gas cannot cover.
    tx = Transaction(
        to=caller,
        gas_limit=(gas_limit_cap + new_account_state_gas + sstore_state_gas),
        sender=pre.fund_eoa(),
    )

    post = {factory: Account(storage=factory_storage)}
    state_test(pre=pre, post=post, tx=tx)


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
@pytest.mark.valid_from("Amsterdam")
def test_sstore_oog_no_reservoir_inflation(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_shortfall: int,
) -> None:
    """
    Verify SSTORE state gas is not charged when regular gas OOGs.

    With zero reservoir, all state gas spills into gas_left. A child
    frame does CREATE (charging state gas from gas_left) followed by
    SSTORE. When the factory is 1 gas short, SSTORE OOGs. If state
    gas is incorrectly charged before regular gas, the extra state gas
    inflates the parent's reservoir on frame failure, changing the
    transaction's effective gas consumption.

    Regression test for SSTORE gas ordering: regular gas must be
    checked before state gas.
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
    create_address = compute_create_address(address=factory, nonce=1)

    # Total gas includes both regular and state components since
    # reservoir is zero — all state gas comes from gas_left.
    factory_gas = (
        factory_code.gas_cost(fork)
        + initcode.execution_gas(fork)
        + initcode.deployment_gas(fork)
    )

    # Caller forwards total gas (regular + state) through CALL.
    # With zero reservoir, the CALL gas parameter is the only source.
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.CALL(
            gas=factory_gas - gas_shortfall,
            address=factory,
            value=0,
            args_offset=0,
            args_size=Op.CALLDATASIZE,
            ret_offset=0,
            ret_size=0,
        )
    )

    sender = pre.fund_eoa()
    # gas_limit = cap, reservoir = 0
    tx = Transaction(
        sender=sender,
        to=caller,
        data=bytes(initcode),
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    created = not gas_shortfall
    post = {
        create_address: Account(code=Op.STOP)
        if created
        else Account.NONEXISTENT,
        factory: Account(storage={0: create_address if created else 0}),
    }

    state_test(pre=pre, tx=tx, post=post)


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


@pytest.mark.valid_from("Amsterdam")
def test_create_no_double_charge_new_account(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify CREATE does not double-charge new-account gas.

    CREATE charges REGULAR_GAS_CREATE as regular gas and new-account
    state gas separately. Provide exactly enough gas for both — if
    GAS_NEW_ACCOUNT were charged twice (once in regular, once in
    state), the CREATE would OOG.
    """
    create_state_gas = fork.create_state_gas(code_size=0)

    # Child: just does CREATE(value=0, offset=0, size=0) and stores result.
    # This creates an empty account (no code deposit).
    child_code = Op.SSTORE(0, Op.CREATE(value=0, offset=0, size=0))
    child = pre.deploy_contract(child_code)

    # Compute exact gas: child bytecode + CREATE child frame.
    # The child frame is empty (size=0) so only the CREATE opcode
    # charges matter: regular (REGULAR_GAS_CREATE) + state (new account).
    child_total = child_code.gas_cost(fork)

    create_address = compute_create_address(address=child, nonce=1)

    # Caller forwards exact regular gas via CALL. State gas for
    # new account comes from the reservoir (gas_limit above the cap).
    caller_storage = Storage()
    regular_gas = child_total - create_state_gas
    caller = pre.deploy_contract(
        Op.SSTORE(
            caller_storage.store_next(1, "create_succeeds"),
            Op.CALL(gas=regular_gas, address=child),
        )
    )

    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        gas_limit=gas_limit_cap + create_state_gas,
    )

    post = {
        caller: Account(storage=caller_storage),
        child: Account(storage={0: create_address}),
        create_address: Account(nonce=1),
    }
    state_test(pre=pre, tx=tx, post=post)


# TODO: Review for bal-devnet-4. If EIP-8037 adopts top-level state gas
# refund (https://github.com/ethereum/EIPs/pull/11476), the expected block
# gas accounting in these tests will change and may need updating.
@pytest.mark.parametrize(
    "state_opcode",
    [
        pytest.param(Op.CALL, id="call_new_account"),
        pytest.param(Op.CREATE, id="inner_create"),
    ],
)
@pytest.mark.parametrize(
    "deposit_fail_mode",
    [
        pytest.param("oversized_code", id="oversized_code"),
        pytest.param("oog_deposit", id="oog_deposit"),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_code_deposit_halt_discards_initcode_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    nonexistent_account: Address,
    state_opcode: Op,
    deposit_fail_mode: str,
) -> None:
    """
    Verify initcode state gas excluded from block on deposit halt.

    A CREATE tx runs initcode that first performs a state-creating
    operation (charging GAS_NEW_ACCOUNT state gas), then returns
    code that triggers a deposit failure (oversized or OOG). The
    exceptional halt reverts all initcode state changes including
    the new account. The reverted GAS_NEW_ACCOUNT must NOT count
    in block_state_gas_used, which determines the block header
    gas_used via max(block_regular_gas, block_state_gas).
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    if state_opcode == Op.CALL:
        state_op = Op.POP(
            Op.CALL(gas=100_000, address=nonexistent_account, value=1)
        )
    else:
        state_op = Op.POP(Op.CREATE(value=0, offset=0, size=1))

    if deposit_fail_mode == "oversized_code":
        deposit_fail = Op.RETURN(0, fork.max_code_size() + 1)
    else:
        # Return code at max size — passes the size check but code
        # deposit state gas (max_code_size * cost_per_state_byte)
        # exceeds available state gas in the child frame, causing OOG.
        deposit_fail = Op.RETURN(0, fork.max_code_size())

    initcode = state_op + deposit_fail

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        to=None,
                        data=initcode,
                        value=10**18,
                        gas_limit=gas_limit_cap,
                        sender=pre.fund_eoa(10**21),
                    ),
                ],
            ),
        ],
        post={},
    )
