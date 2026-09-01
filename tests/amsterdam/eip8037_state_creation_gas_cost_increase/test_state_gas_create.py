"""
Test CREATE and CREATE2 state gas charging under EIP-8037.

Contract creation charges state gas for the new account and for
code deposit. Execution gas for CREATE is charged separately.

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
    Fork,
    Header,
    Initcode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
    TransactionReceipt,
    compute_create2_address,
    compute_create_address,
)
from execution_testing.checklists import EIPChecklist

from .spec import init_code_at_high_bytes, ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.valid_from("EIP8037")
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
    runtime_code = Op.STOP
    init_code = Initcode(deploy_code=runtime_code)
    mstore_value, size = init_code_at_high_bytes(init_code)

    create_call = Op.CREATE(0, 0, size, init_code_size=size)
    storage = Storage()
    code = Op.MSTORE(0, mstore_value, new_memory_size=32) + Op.SSTORE(
        storage.store_next(False),
        Op.ISZERO(create_call),
        original_value=0,
        current_value=0,
        new_value=0,
    )
    contract = pre.deploy_contract(code=code)
    created = compute_create_address(address=contract, nonce=1)

    new_account_state = create_call.state_cost(fork)
    code_deposit_state = init_code.state_cost(fork)

    assert new_account_state > 0, "test requires a NEW_ACCOUNT charge"
    assert code_deposit_state > 0, "test requires a code-deposit charge"

    expected_state = new_account_state + code_deposit_state

    expected_execution = (
        fork.transaction_intrinsic_cost_calculator()()
        + fork.transaction_top_frame_gas_calculator()(contract_creation=False)
        + code.execution_cost(fork)
        + init_code.gas_cost(fork)
    )
    assert expected_state > expected_execution, (
        "requires state gas > execution gas"
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    post = {
        contract: Account(nonce=2, storage=storage),
        created: Account(nonce=1, code=runtime_code),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_state),
    )


@pytest.mark.with_all_create_opcodes
@pytest.mark.parametrize(
    "gas_delta",
    [pytest.param(0, id="exact_fit"), pytest.param(-1, id="one_short")],
)
@pytest.mark.valid_from("EIP8037")
def test_create_with_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    create_opcode: Op,
    gas_delta: int,
    fork: Fork,
) -> None:
    """
    Test CREATE/CREATE2 with state gas funded from the reservoir.

    The factory is forwarded only the execution gas it needs, so the
    new-account charge can only come from the reservoir riding along.
    One gas short of that grant the factory halts instead.
    """
    init_code = Op.STOP
    mstore_value, size = init_code_at_high_bytes(init_code)

    create_call = create_opcode(
        value=0, offset=0, size=size, init_code_size=size
    )

    factory_code = Op.MSTORE(0, mstore_value, new_memory_size=32) + Op.POP(
        create_call
    )
    factory = pre.deploy_contract(code=factory_code)

    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(
            storage.store_next(1 if gas_delta == 0 else 0, "create_succeeded"),
            Op.CALL(
                gas=factory_code.execution_cost(fork),
                address=factory,
            ),
        ),
        storage=storage.canary(),
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=factory_code.state_cost(fork) + gas_delta,
        sender=pre.fund_eoa(),
    )

    created = compute_create_address(
        address=factory,
        nonce=1,
        salt=0,
        initcode=init_code,
        opcode=create_opcode,
    )

    post = {
        contract: Account(storage=storage),
        created: Account(nonce=1, code=b"")
        if gas_delta == 0
        else Account.NONEXISTENT,
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("enough_gas", [False, True])
@pytest.mark.with_all_create_opcodes
@pytest.mark.valid_from("EIP8037")
def test_create_child_spill_not_double_charged(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    enough_gas: bool,
) -> None:
    """
    Test CREATE/CREATE2 child state gas paid from `gas_left` is not recharged.

    The factory executes below the Amsterdam tx gas cap, so the CREATE child
    pays new-account and storage state gas by spilling from `gas_left`. The
    gas limit covers that bill once, so charging the same state growth again
    at frame end would run the transaction out of gas.
    """
    init_code = sum(Op.SSTORE(i, i + 1) for i in range(6)) + Op.STOP
    mstore_value, initcode_size = init_code_at_high_bytes(init_code)

    factory_code = Op.MSTORE(
        0,
        mstore_value,
        # gas accounting
        new_memory_size=32,
    ) + (
        create_opcode(
            value=0,
            offset=0,
            size=initcode_size,
            # gas accounting
            init_code_size=initcode_size,
        )
    )
    factory = pre.deploy_contract(code=factory_code)
    created = compute_create_address(
        address=factory,
        salt=0,
        nonce=1,
        initcode=init_code,
        opcode=create_opcode,
    )

    # The child's grant is short a 64th of what the factory holds at
    # dispatch, so its bill has to be grossed up by that fraction.
    child_gas = init_code.gas_cost(fork)
    gas_limit = (
        fork.transaction_intrinsic_cost_calculator()()
        + factory_code.gas_cost(fork)
        + child_gas * 64 // 63
    )
    if not enough_gas:
        gas_limit -= 1

    tx = Transaction(
        to=factory,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    post = {
        created: Account(nonce=1, storage={i: i + 1 for i in range(6)})
        if enough_gas
        else Account.NONEXISTENT,
    }
    state_test(pre=pre, post=post, tx=tx)


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
@pytest.mark.valid_from("EIP8037")
def test_code_deposit_state_gas_scales_with_size(
    state_test: StateTestFiller,
    pre: Alloc,
    code_size: int | str,
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

    # State gas: new account + code deposit
    total_state_gas = fork.create_state_gas(code_size=code_size)

    init_code = Op.RETURN(
        0, code_size, new_memory_size=code_size, code_deposit_size=code_size
    )

    total_execution_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=bytes(init_code), contract_creation=True
    ) + init_code.execution_cost(fork)

    sender = pre.fund_eoa()
    tx = Transaction(
        to=None,
        data=init_code,
        state_gas_reservoir=total_state_gas,
        sender=sender,
    )

    create_address = compute_create_address(address=sender, nonce=0)
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    if code_size > fork.max_code_size():
        post = {create_address: Account.NONEXISTENT}
        # The halt rolls the reservoir back, so the sender pays the cap.
        expected_gas_used = gas_limit_cap
    else:
        post = {}
        assert total_state_gas > total_execution_gas, (
            "requires state gas > execution gas"
        )
        expected_gas_used = max(total_execution_gas, total_state_gas)

    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.parametrize(
    ("funding", "gas_delta"),
    [
        pytest.param("reservoir", 0, id="reservoir_success"),
        pytest.param("reservoir", -1, id="reservoir_oog"),
        pytest.param("spill", 0, id="spill_success"),
        pytest.param("spill", -1, id="spill_oog"),
    ],
)
@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.valid_from("EIP8037")
def test_code_deposit_state_gas_exact_fit_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    funding: str,
    gas_delta: int,
) -> None:
    """
    Pin the code-deposit state gas at its exact-fit boundary.

    A CREATE tx deploys ``code_size`` bytes with ``gas_limit`` set so the
    deposit lands exactly at the available gas (deploys) or one gas short
    (halts: state restored, the top-frame ``NEW_ACCOUNT`` refilled, no
    code). Under EIP-2780 the created account's ``NEW_ACCOUNT`` state gas
    is charged at the top frame (not bundled in the intrinsic), so
    ``exact_fit_gas`` includes it explicitly. The two regimes pin the halt
    billing: over-cap ``reservoir`` rolls the reservoir back so the sender
    pays the cap; in-cap ``spill`` refills the spilled state gas into
    ``gas_left`` and burns it all, billing the full ``gas_limit``. The
    scaling tests assert success only.
    """
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None

    code_size = fork.max_code_size() if funding == "reservoir" else 1000

    init_code = Op.RETURN(
        0, code_size, code_deposit_size=code_size, new_memory_size=code_size
    )

    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        calldata=bytes(init_code),
        contract_creation=True,
        return_cost_deducted_prior_execution=True,
    )
    # The fresh target's NEW_ACCOUNT is a top-frame state charge under
    # EIP-2780, no longer folded into the intrinsic. The RETURN metadata
    # folds the memory expansion, code-hash keccak and code-deposit state
    # gas into `init_code`'s own cost.
    exact_fit_gas = (
        intrinsic_execution
        + fork.transaction_top_frame_state_gas(contract_creation=True)
        + init_code.gas_cost(fork)
    )
    if funding == "reservoir":
        assert exact_fit_gas > cap
    else:
        assert exact_fit_gas <= cap

    sender = pre.fund_eoa()
    created = compute_create_address(address=sender, nonce=0)
    gas_limit = exact_fit_gas + gas_delta

    post: dict
    if gas_delta == 0:
        receipt_gas_used = exact_fit_gas
        post = {created: Account(code=b"\x00" * code_size)}
    else:
        # reservoir: the deposit OOG refills the reservoir, so the sender
        # pays the execution cap. spill: the refilled NEW_ACCOUNT lands in
        # gas_left and is burned, so the sender pays the full gas_limit.
        receipt_gas_used = cap if funding == "reservoir" else gas_limit
        post = {created: Account.NONEXISTENT}

    tx = Transaction(
        to=None,
        data=init_code,
        gas_limit=gas_limit,
        sender=sender,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=receipt_gas_used
        ),
    )

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_repeated_create_same_code_charges_each_account(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test code deposit is charged per-account, not per code hash.

    Two CREATEs with identical init code deploy identical bytecode
    and so share a single ``code_hash``. The factory snapshots
    ``gas_left`` around each CREATE via ``Op.GAS`` and stores
    ``(g0 - g1) - (g1 - g2)`` in slot 0. Identical work must cost
    the same — so the difference must be zero.

    Runtime measurement is required: the bug manifests as a
    child-frame state-gas spillover into ``gas_left`` (a runtime
    quantity), which static helpers like ``bytecode.gas_cost()``
    do not model.

    A non-zero result indicates ``compute_state_byte_diff`` is
    keying code-deposit accounting by hash via ``code_writes``,
    silently dropping the second CREATE's ``len(code) × CPSB``
    charge.
    """
    # Y init code returns memory[0:1] = 0x00 to deploy a 1-byte STOP.
    y_init = Op.PUSH1(1) + Op.PUSH1(0) + Op.RETURN
    y_size = len(bytes(y_init))

    # Memory layout:
    #   [ 0: 32) — Y init code (right-aligned PUSH32 padding)
    #   [32: 64) — g0 (gas before first CREATE)
    #   [64: 96) — g1 (gas between the two CREATEs)
    #   [96:128) — g2 (gas after second CREATE)
    factory_code = (
        Op.MSTORE(0, Op.PUSH32(bytes(y_init)))
        + Op.MSTORE(32, Op.GAS)
        + Op.POP(Op.CREATE(value=0, offset=32 - y_size, size=y_size))
        + Op.MSTORE(64, Op.GAS)
        + Op.POP(Op.CREATE(value=0, offset=32 - y_size, size=y_size))
        + Op.MSTORE(96, Op.GAS)
        + Op.SSTORE(
            0,
            Op.SUB(
                Op.SUB(Op.MLOAD(32), Op.MLOAD(64)),  # cost of CREATE 1
                Op.SUB(Op.MLOAD(64), Op.MLOAD(96)),  # cost of CREATE 2
            ),
        )
        + Op.STOP
    )

    factory_storage = Storage()
    factory_storage[0] = 0
    factory = pre.deploy_contract(code=factory_code, storage=factory_storage)

    tx = Transaction(
        to=factory,
        sender=pre.fund_eoa(),
        gas_limit=2_000_000,
    )

    state_test(
        pre=pre,
        post={factory: Account(storage=factory_storage)},
        tx=tx,
    )


@pytest.mark.valid_from("EIP8037")
def test_create_tx_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test contract creation transaction charges top-frame state gas.

    A create transaction charges the new account's state gas during
    top-frame preparation, separately from transaction intrinsic gas.
    """
    init_code = Op.STOP

    expected_top_frame_state = fork.transaction_top_frame_state_gas(
        contract_creation=True
    )
    expected_execution = fork.transaction_intrinsic_cost_calculator()(
        calldata=bytes(init_code), contract_creation=True
    ) + init_code.execution_cost(fork)

    assert expected_top_frame_state > expected_execution, (
        "requires top-frame state gas > execution gas"
    )

    sender = pre.fund_eoa()
    tx = Transaction(
        to=None,
        data=init_code,
        state_gas_reservoir=0,
        sender=sender,
    )

    created = compute_create_address(address=sender, nonce=0)
    state_test(
        pre=pre,
        post={created: Account(nonce=1, code=b"")},
        tx=tx,
        blockchain_test_header_verify=Header(
            gas_used=max(expected_execution, expected_top_frame_state)
        ),
    )


@pytest.mark.valid_from("EIP8037")
def test_create_revert_no_code_deposit_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test reverted CREATE does not charge state gas.

    Account-creation state gas is charged in the creating frame but
    refilled when the creation rolls back, so the net state gas is zero,
    and no code deposit state gas is charged because no code was
    deployed. The block therefore bills execution gas alone.
    """
    init_code = Op.REVERT(0, 0)
    mstore_value, size = init_code_at_high_bytes(init_code)

    storage = Storage()
    code = Op.MSTORE(0, mstore_value, new_memory_size=32) + Op.SSTORE(
        storage.store_next(0),  # CREATE returns 0 on failure
        Op.CREATE(0, 0, size, init_code_size=size, account_new=False),
        original_value=0,
        current_value=0,
        new_value=0,
    )
    contract = pre.deploy_contract(code=code)

    assert code.state_cost(fork) == 0, "the rolled-back creation refills"
    expected_execution = (
        fork.transaction_intrinsic_cost_calculator()()
        + code.execution_cost(fork)
        + init_code.execution_cost(fork)
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    post = {
        contract: Account(storage=storage),
        compute_create_address(address=contract, nonce=1): (
            Account.NONEXISTENT
        ),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_execution),
    )


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.with_all_create_opcodes
@pytest.mark.parametrize("enough_gas", [False, True])
@pytest.mark.valid_from("EIP8037")
def test_create_insufficient_account_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    enough_gas: bool,
    create_opcode: Op,
) -> None:
    """
    Test CREATE OOGs when state gas is insufficient for account creation.

    The gas limit covers the frame's execution gas and the required state gas
    minus one, so the new-account state charge has neither a reservoir nor
    spare `gas_left` to draw from. The frame halts before the account is
    created and the whole limit is billed.
    """
    init_code = Op.STOP
    mstore_value, size = init_code_at_high_bytes(init_code)

    code = Op.MSTORE(0, mstore_value, new_memory_size=32) + (
        create_opcode(value=0, offset=0, size=size, init_code_size=size)
    )
    contract = pre.deploy_contract(code=code)

    gas_limit = fork.transaction_intrinsic_cost_calculator()() + (
        code.gas_cost(fork)
    )
    if not enough_gas:
        gas_limit -= 1

    assert code.state_cost(fork) > 0, (
        f"create opcode does not charge state gas at {fork}"
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    post = {
        contract: Account(storage={0: 0}),
        compute_create_address(
            address=contract, nonce=1, initcode=init_code, opcode=create_opcode
        ): (Account(nonce=1) if enough_gas else Account.NONEXISTENT),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_create2_address_collision(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test CREATE2 returns zero on address collision.

    When CREATE2 targets an address that already has code or a
    non-zero nonce (EIP-684), the collision is detected early and
    returns zero without charging state gas. The existing account is
    left unchanged.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    init_code = Op.STOP
    mstore_value, size = init_code_at_high_bytes(init_code)
    salt = 0

    storage = Storage()
    factory_prefix_code = (
        Op.MSTORE(0, mstore_value, new_memory_size=32)
        # First CREATE
        + Op.SSTORE(
            storage.store_next(1),
            Op.ISZERO(
                Op.ISZERO(
                    Op.CREATE2(
                        0,
                        0,
                        size,
                        salt,
                        # gas accounting
                        init_code_size=size,
                        account_new=True,
                    )
                )
            ),
            # gas accounting
            original_value=0,
            new_value=1,
        )
    )
    factory_create_code = Op.CREATE2(
        0,
        0,
        size,
        salt,
        # gas accounting
        init_code_size=size,
        account_new=False,
    )
    factory_code = factory_prefix_code + factory_create_code
    contract = pre.deploy_contract(code=factory_code)
    collision_target = compute_create2_address(
        address=contract, salt=salt, initcode=bytes(init_code)
    )

    state_gas = factory_prefix_code.state_cost(fork)
    # The collision burns all but a 64th of the factory's execution
    # gas, so half again its own cost keeps the trailing SSTORE alive.
    # Execution gas is at most what the limit has left once the state
    # charge is paid, so the assert keeps that burn under the state gas.
    gas_limit = (
        (
            fork.transaction_intrinsic_cost_calculator()()
            + factory_code.gas_cost(fork)
        )
        * 3
        // 2
    )
    assert gas_limit - state_gas < state_gas, "state gas must dominate"

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    post = {
        contract: Account(storage=storage),
        collision_target: Account(nonce=1, code=b""),
    }

    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=state_gas),
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.valid_from("EIP8037")
def test_create_address_collision(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test CREATE returns zero on address collision.

    When CREATE targets an address that already has code or a
    non-zero nonce (EIP-684), the collision is detected early and
    returns zero without charging state gas. The existing account is
    left unchanged.

    Requires mutable pre-alloc in order to prepare the collision that normally
    would require a hash-collision.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    init_code = Op.STOP
    mstore_value, size = init_code_at_high_bytes(init_code)

    storage = Storage()
    factory_prefix_code = (
        Op.MSTORE(0, mstore_value, new_memory_size=32)
        # Fill state gas usage just enough to pass the execution gas
        + Op.SSTORE(storage.store_next(1), 1, original_value=0, new_value=1)
        + Op.SSTORE(storage.store_next(1), 1, original_value=0, new_value=1)
    )
    factory_create_code = Op.CREATE(
        0,
        0,
        size,
        # gas accounting
        init_code_size=size,
        account_new=False,
    )
    factory_code = factory_prefix_code + factory_create_code
    contract = pre.deploy_contract(code=factory_code)
    collision_target = compute_create_address(address=contract, nonce=1)
    pre[collision_target] = Account(nonce=1)

    state_gas = factory_prefix_code.state_cost(fork)
    # The collision burns all but a 64th of the factory's execution
    # gas, so half again its own cost keeps the trailing SSTORE alive.
    # Execution gas is at most what the limit has left once the state
    # charge is paid, so the assert keeps that burn under the state gas.
    gas_limit = (
        (
            fork.transaction_intrinsic_cost_calculator()()
            + factory_code.gas_cost(fork)
        )
        * 3
        // 2
    )
    assert factory_code.gas_cost(fork) - state_gas < state_gas, (
        "state gas must dominate"
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    post = {
        contract: Account(storage=storage),
        collision_target: Account(nonce=1, code=b""),
    }

    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=state_gas),
    )


@pytest.mark.inclusion_test
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
@pytest.mark.valid_from("EIP8037")
def test_create_tx_intrinsic_gas_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_delta: int,
) -> None:
    """
    Test the creation transaction intrinsic gas boundary.

    Intrinsic gas covers execution only. At the boundary the transaction is
    accepted but cannot create a contract; one gas below is rejected.
    """
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    gas_limit = intrinsic_cost(
        contract_creation=True,
    )

    sender = pre.fund_eoa()
    tx = Transaction(
        to=None,
        gas_limit=gas_limit + gas_delta,
        sender=sender,
        error=(
            TransactionException.INTRINSIC_GAS_TOO_LOW
            if gas_delta < 0
            else None
        ),
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account.NONEXISTENT
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.inclusion_test
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "initcode",
    [
        pytest.param(Bytecode(), id="empty_initcode"),
        pytest.param(Op.RETURN(0, 0), id="return_initcode"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_create_tx_below_total_intrinsic(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    initcode: Bytecode,
) -> None:
    """
    Reject a creation tx one gas below the (now execution-only) intrinsic.

    Under EIP-2780 the created account's ``NEW_ACCOUNT`` cost moved out
    of the transaction intrinsic and into the top frame, so the creation
    intrinsic is entirely execution:
    ``fork.transaction_intrinsic_cost_calculator()(contract_creation=True,
    calldata=initcode)``. Pinning ``gas_limit`` at ``intrinsic - 1`` must
    be rejected as intrinsic-gas-too-low, mirroring the set_code case in
    ``test_set_code_tx_below_total_intrinsic``.

    This now overlaps ``test_create_tx_intrinsic_gas_boundary``
    (``gas_delta=-1``), but additionally sweeps the initcode so the
    per-word init-code cost folded into the execution intrinsic is
    exercised.
    """
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        contract_creation=True,
        calldata=initcode,
    )

    sender = pre.fund_eoa()
    tx = Transaction(
        to=None,
        data=initcode,
        gas_limit=intrinsic - 1,
        sender=sender,
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account.NONEXISTENT
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_code_deposit_oog_preserves_parent_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test parent reservoir preserved after child code deposit OOG.

    A caller invokes the factory with limited gas and a reservoir consumed by
    the CREATE account charge. The child returns enough bytes that code-deposit
    state gas cannot spill entirely into its limited gas_left. The factory's
    SSTORE proves the account charge was refunded, while the exact receipt
    proves the reservoir was not inflated by the failed spill.
    """
    deploy_size = 4096
    init_code = Op.RETURN(
        0,
        deploy_size,
        new_memory_size=deploy_size,
        code_deposit_size=deploy_size,
    )
    create_call = Op.CREATE(
        value=0,
        offset=32 - len(init_code),
        size=len(init_code),
        init_code_size=len(init_code),
    )

    factory_storage = Storage()
    factory_create_code = (
        Op.MSTORE(0, Op.PUSH32(bytes(init_code)), new_memory_size=32)
        + create_call
    )
    factory_post_create_code = Op.SSTORE(
        factory_storage.store_next(1, "parent_sstore"),
        1,
        original_value=0,
        current_value=0,
        new_value=1,
    )
    assert factory_create_code.state_cost(
        fork
    ) > factory_post_create_code.state_cost(fork)
    factory_code = factory_create_code + factory_post_create_code
    factory = pre.deploy_contract(code=factory_code)

    # Limited execution gas forwarded to the factory. CREATE leaves it
    # only a 64th of what it holds, so fund 64 times its own execution
    # gas for the SSTOREs that follow.
    child_gas = factory_code.execution_cost(fork) * 64
    caller_code = Op.CALL(gas=child_gas, address=factory)
    caller = pre.deploy_contract(
        code=caller_code,
    )

    gas_before_create_child = child_gas - factory_create_code.execution_cost(
        fork
    )
    create_child_gas = gas_before_create_child - gas_before_create_child // 64
    code_deposit = Op.RETURN(code_deposit_size=deploy_size)
    child_pre_deposit_execution = init_code.execution_cost(
        fork
    ) + code_deposit.execution_cost(fork)
    assert create_child_gas >= child_pre_deposit_execution, (
        "child must reach code deposit"
    )
    assert (
        create_child_gas - child_pre_deposit_execution
        < code_deposit.state_cost(fork)
    ), "child must fail the code-deposit state charge"

    expected_execution = (
        fork.transaction_intrinsic_cost_calculator()()
        + fork.transaction_top_frame_gas_calculator()(contract_creation=False)
        + caller_code.execution_cost(fork)
        + factory_create_code.execution_cost(fork)
        + create_child_gas
        + factory_post_create_code.execution_cost(fork)
    )
    expected_state = factory_post_create_code.state_cost(fork)
    expected_cumulative = expected_execution + expected_state

    # NEW_ACCOUNT consumes the whole reservoir before the child starts, so
    # code deposit must spill entirely into the child's limited gas_left.
    # After failure, its refund funds the factory's SSTORE.
    tx = Transaction(
        to=caller,
        state_gas_reservoir=create_call.state_cost(fork),
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative,
        ),
    )

    # The deposit halts the child, so the factory's nonce bump is the
    # only trace the creation leaves.
    post = {
        factory: Account(nonce=2, storage=factory_storage),
        compute_create_address(address=factory, nonce=1): Account.NONEXISTENT,
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(
            gas_used=max(expected_execution, expected_state)
        ),
    )


@pytest.mark.parametrize(
    ("with_reservoir", "failure_op"),
    [
        pytest.param(True, Op.REVERT(0, 0), id="with_reservoir-revert"),
        pytest.param(True, Op.INVALID, id="with_reservoir-halt"),
        pytest.param(False, Op.REVERT(0, 0), id="no_reservoir-revert"),
        pytest.param(False, Op.INVALID, id="no_reservoir-halt"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_parent_state_gas_after_child_failure(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    with_reservoir: bool,
    failure_op: Bytecode,
) -> None:
    """
    Test parent state-gas pools after CREATE child failure.

    A factory runs CREATE whose initcode does an SSTORE, then either
    REVERTs or hits INVALID. The factory's own SSTORE after the failed
    CREATE checks the parent's reservoir and gas_left are correct.

    Under EIP-8037 state-gas refunds are LIFO. Gas spilled from
    gas_left refunds to gas_left, only the reservoir-funded portion
    returns to the reservoir.

    Four scenarios cover the gas-pool state space:

    - `with_reservoir x revert`: child state gas refills LIFO. The
      reservoir-funded portion returns to the parent reservoir, any
      spill to the parent gas_left.
    - `with_reservoir x halt`: halt refills the child frame LIFO then
      burns its gas_left. Only the child's start reservoir survives.
    - `no_reservoir x revert`: child state gas spilled wholly from
      gas_left, so the LIFO refill returns it there. No phantom
      reservoir forms.
    - `no_reservoir x halt`: no phantom reservoir forms. The spilled
      child state gas is burned with the child gas_left and the
      factory's post-CREATE SSTORE spills from gas_left.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    initcode = Op.SSTORE(0, 1, original_value=0, new_value=1) + failure_op

    create_call = Op.CREATE(
        value=0,
        offset=32 - len(initcode),
        size=len(initcode),
        init_code_size=len(initcode),
    )

    factory_storage = Storage()
    # Split the factory into the CREATE run (memory setup + CREATE, whose
    # result is left on the stack) and the post-CREATE stores, so each
    # step's execution gas is read off `.execution_cost(fork)` rather than
    # rebuilt from constants.
    factory_create_code = (
        Op.MSTORE(0, Op.PUSH32(bytes(initcode)), new_memory_size=32)
        + create_call
    )
    factory_post_create_code = (
        # Store the CREATE result (0 on failure): a cold 0 -> 0 no-op.
        Op.PUSH1(factory_storage.store_next(0, "create_fails"))
        + Op.SSTORE.with_metadata(original_value=0, new_value=0)(
            unchecked=True
        )
        # Factory's own cold 0 -> 1 SSTORE.
        + Op.SSTORE(
            factory_storage.store_next(1, "post_create"),
            1,
            original_value=0,
            new_value=1,
        )
    )
    factory_code = factory_create_code + factory_post_create_code
    factory = pre.deploy_contract(code=factory_code)

    new_account_state_gas = create_call.state_cost(fork)
    gas_limit = (
        gas_limit_cap + new_account_state_gas + sstore_state_gas * 2
        if with_reservoir
        else 5_000_000
    )

    if failure_op == Op.INVALID:
        # Simulate runtime gas for HALT under EIP-8037 LIFO refills:
        #  1. Execution pool capped by transaction_gas_limit_cap. The
        #     remainder forms the state reservoir.
        #  2. CREATE charges new_account state gas, reservoir first
        #     then spilled to gas_left and tracked.
        #  3. 63/64 retention: parent keeps gas_left // 64. The
        #     reservoir is forwarded to the child frame.
        #  4. Child initcode SSTORE charges sstore_state_gas, child
        #     reservoir first then spilled to child gas_left.
        #  5. INVALID refills the child frame LIFO then burns its
        #     gas_left. Only the child's start reservoir survives.
        #  6. CREATE failure refills new_account LIFO: the spill to
        #     parent gas_left, the rest to the parent reservoir.
        #  7. Factory post-CREATE SSTORE charges sstore_state_gas,
        #     reservoir first then spilled to gas_left.
        execution_gas = gas_limit - intrinsic_cost
        execution_budget = gas_limit_cap - intrinsic_cost
        sim_gas_left = min(execution_budget, execution_gas)
        sim_state_gas_left = execution_gas - sim_gas_left

        # Memory setup, the CREATE arg pushes and the CREATE execution
        # cost are all consumed before the 63/64 split.
        sim_gas_left -= factory_create_code.execution_cost(fork)

        # CREATE new_account state gas: reservoir first, spill tracked.
        new_account_from_reservoir = min(
            sim_state_gas_left, new_account_state_gas
        )
        new_account_spill = new_account_state_gas - new_account_from_reservoir
        sim_state_gas_left -= new_account_from_reservoir
        sim_gas_left -= new_account_spill

        # 63/64 retention: parent keeps gas_left // 64. The reservoir
        # is forwarded to the child frame and survives on halt.
        child_reservoir = sim_state_gas_left
        sim_gas_left = sim_gas_left // 64

        # INVALID burns child gas_left, including any spilled SSTORE
        # state gas. Only the forwarded reservoir survives.
        sim_state_gas_left = child_reservoir

        # CREATE failure refills new_account LIFO: spilled portion to
        # gas_left, reservoir-funded portion to the reservoir.
        sim_gas_left += new_account_spill
        sim_state_gas_left += new_account_from_reservoir

        sim_gas_left -= factory_post_create_code.execution_cost(fork)

        # Factory post-CREATE SSTORE: reservoir first, spill otherwise.
        if sim_state_gas_left >= sstore_state_gas:
            sim_state_gas_left -= sstore_state_gas
        else:
            sim_gas_left -= sstore_state_gas - sim_state_gas_left
            sim_state_gas_left = 0

        expected_cumulative = gas_limit - sim_gas_left - sim_state_gas_left
    else:
        # REVERT preserves gas_left and refunds the child frame's
        # state gas (initcode SSTORE + new account). Only the
        # factory's own post-CREATE SSTORE consumes net state gas.
        expected_cumulative = (
            intrinsic_cost
            + factory_create_code.execution_cost(fork)
            + factory_post_create_code.execution_cost(fork)
            + initcode.execution_cost(fork)
            + sstore_state_gas
        )

    tx = Transaction(
        to=factory,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative,
        ),
    )

    state_test(
        pre=pre,
        post={factory: Account(storage=factory_storage)},
        tx=tx,
    )


@pytest.mark.parametrize("enough_gas", [False, True])
@pytest.mark.with_all_create_opcodes
@pytest.mark.valid_from("EIP8037")
def test_nested_create_code_deposit_cannot_borrow_parent_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    enough_gas: bool,
) -> None:
    """
    Test nested CREATE code deposit does not borrow parent gas.

    Give the factory exactly enough remaining execution gas to cover the
    child's initcode, code hash, and code-deposit state gas in aggregate.
    EIP-150 retains 1/64 in the factory, leaving the child short by exactly
    that retained amount. The child cannot borrow it, so code deposit fails:
    the factory nonce increments but no contract is deployed.
    """
    deployed_code_size = 1
    deployed_code = Op.STOP
    init_code = Op.RETURN(
        0,
        deployed_code_size,
        new_memory_size=32,
        code_deposit_size=deployed_code_size,
    )
    factory_mstore = Op.MSTORE(
        0, Op.PUSH32(bytes(init_code)), new_memory_size=32
    )
    factory_create = create_opcode(
        value=0,
        offset=32 - len(init_code),
        size=len(init_code),
        init_code_size=len(init_code),
    )
    factory_code = factory_mstore + factory_create
    factory = pre.deploy_contract(code=factory_code)
    created = compute_create_address(
        address=factory,
        nonce=1,
        salt=0,
        initcode=init_code,
        opcode=create_opcode,
    )

    # Everything is funded by the execution gas, so we can apply the 1/64th
    # rule directly.
    factory_gas = factory_code.gas_cost(fork) + (
        init_code.gas_cost(fork) * 64 // 63
    )
    if not enough_gas:
        factory_gas -= 1

    # Limit the execution gas via a subcall to avoid having to calculate the
    # intrinsic gas cost.
    caller_code = Op.CALL(
        gas=factory_gas,
        address=factory,
    )
    caller = pre.deploy_contract(caller_code)

    # The only guarantee needed is that there will be no gas in the reservoir
    tx = Transaction(to=caller, state_gas_reservoir=0, sender=pre.fund_eoa())

    post = {
        factory: Account(nonce=2),
        created: Account(nonce=1, code=deployed_code)
        if enough_gas
        else Account.NONEXISTENT,
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "gas_shortfall",
    [
        pytest.param(0, id="exact_gas"),
        pytest.param(1, id="short_one_gas"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_sstore_oog_no_reservoir_inflation(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_shortfall: int,
) -> None:
    """
    Verify SSTORE does not inflate the parent reservoir on execution OOG.

    With zero reservoir, all state gas spills into gas_left. The exact-gas
    case succeeds; one gas less makes the factory's SSTORE fail its execution
    gas check. The failing frame has no surviving state charge, so its full
    gas allowance must be reported as execution gas. The exact receipt and
    header catch state gas charged before the execution OOG and incorrectly
    returned to the parent as reservoir gas.
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

    # Total gas includes both execution and state components since
    # reservoir is zero — all state gas comes from gas_left.
    factory_gas = (
        factory_code.gas_cost(fork)
        + initcode.evm_gas(fork)
        + initcode.deployment_gas(fork)
    )

    # Caller forwards total gas (execution + state) through CALL. With zero
    # reservoir, the CALL gas parameter is the factory's only source.
    caller_code = Op.CALLDATACOPY(
        0,
        0,
        Op.CALLDATASIZE,
        data_size=initcode_len,
        new_memory_size=initcode_len,
    ) + Op.CALL(
        gas=factory_gas - gas_shortfall,
        address=factory,
        value=0,
        args_offset=0,
        args_size=Op.CALLDATASIZE,
        ret_offset=0,
        ret_size=0,
    )
    caller = pre.deploy_contract(caller_code)

    expected_cumulative = (
        fork.transaction_intrinsic_cost_calculator()(
            calldata=bytes(initcode),
            return_cost_deducted_prior_execution=True,
        )
        + fork.transaction_top_frame_gas_calculator()(contract_creation=False)
        + caller_code.execution_cost(fork)
        + factory_gas
        - gas_shortfall
    )
    code_deposit = Op.RETURN(code_deposit_size=len(Op.STOP))
    expected_state = (
        factory_code.state_cost(fork) + code_deposit.state_cost(fork)
        if gas_shortfall == 0
        else 0
    )
    expected_execution = expected_cumulative - expected_state

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=caller,
        data=bytes(initcode),
        state_gas_reservoir=0,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative,
        ),
    )

    created = not gas_shortfall
    post = {
        create_address: Account(code=Op.STOP)
        if created
        else Account.NONEXISTENT,
        factory: Account(storage={0: create_address if created else 0}),
    }

    state_test(
        pre=pre,
        tx=tx,
        post=post,
        blockchain_test_header_verify=Header(
            gas_used=max(expected_execution, expected_state)
        ),
    )


@pytest.mark.parametrize(
    "gas_shortfall",
    [
        pytest.param(0, id="exact_gas"),
        pytest.param(1, id="short_one_gas"),
    ],
)
@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("EIP8037")
def test_max_initcode_size_gas_metering_via_create(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_shortfall: int,
    create_opcode: Op,
) -> None:
    """
    Verify 2D gas metering for CREATE with max initcode size.

    A caller contract forwards exact execution gas to a factory via CALL.
    State gas is supplied through the reservoir (tx.gas_limit above the
    cap). With short_one_gas, the factory is 1 execution gas short and
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

    # Split gas into execution and state components.
    # CALL gas only feeds gas_left; state gas must come from the reservoir.
    factory_gas = (
        factory_code.gas_cost(fork)
        + initcode.evm_gas(fork)
        + initcode.deployment_gas(fork)
    )
    factory_state_gas = fork.create_state_gas(
        code_size=len(initcode.deploy_code)
    ) + Op.SSTORE(new_value=1).state_cost(fork)
    factory_execution_gas = factory_gas - factory_state_gas

    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.CALL(
            gas=factory_execution_gas - gas_shortfall,
            address=factory,
            value=0,
            args_offset=0,
            args_size=Op.CALLDATASIZE,
            ret_offset=0,
            ret_size=0,
        )
        + Op.STOP
    )

    tx = Transaction(
        sender=alice,
        to=caller,
        data=bytes(initcode),
        state_gas_reservoir=factory_state_gas,
    )

    created = not gas_shortfall
    post = {
        create_address: Account(code=Op.STOP)
        if created
        else Account.NONEXISTENT,
        factory: Account(storage={0: create_address if created else 0}),
    }

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.valid_from("EIP8037")
def test_create_no_double_charge_new_account(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify CREATE does not double-charge new-account gas.

    CREATE charges EXECUTION_GAS_CREATE as execution gas and new-account
    state gas separately. Provide exactly enough gas for both — if
    GAS_NEW_ACCOUNT were charged twice (once in execution, once in
    state), the CREATE would OOG.
    """
    # Child: just does CREATE(value=0, offset=0, size=0) and stores result.
    # This creates an empty account (no code deposit).
    child_code = Op.SSTORE(0, Op.CREATE(value=0, offset=0, size=0))
    child = pre.deploy_contract(child_code)

    create_address = compute_create_address(address=child, nonce=1)

    # Caller forwards exact execution gas via CALL. State gas for
    # new account comes from the reservoir (gas_limit above the cap).
    caller_storage = Storage()
    caller = pre.deploy_contract(
        Op.SSTORE(
            caller_storage.store_next(1, "create_succeeds"),
            Op.CALL(gas=child_code.execution_cost(fork), address=child),
        )
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        state_gas_reservoir=child_code.state_cost(fork),
    )

    post = {
        caller: Account(storage=caller_storage),
        child: Account(storage={0: create_address}),
        create_address: Account(nonce=1),
    }
    state_test(pre=pre, tx=tx, post=post)


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
        pytest.param("ef_prefix", id="ef_prefix"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_code_deposit_halt_discards_initcode_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    state_opcode: Op,
    deposit_fail_mode: str,
) -> None:
    """
    Verify deposit halt discards all state gas charged by initcode.

    A CREATE tx runs initcode that first performs a state-creating
    operation (charging GAS_NEW_ACCOUNT state gas), then returns
    code that triggers a deposit failure (oversized, OOG, or an
    EIP-3541 0xEF prefix). The exceptional halt reverts all initcode
    state changes including the new account. The reverted
    GAS_NEW_ACCOUNT must not count in block state gas. The deposit halt burns
    the full execution grant, so the exact receipt and header both equal the
    transaction gas-limit cap. Any surviving state charge would split that
    fixed total across the two dimensions and lower the header below the cap.
    """
    subcall_forwarded_value = 1
    entry_account_value = 1
    if state_opcode == Op.CALL:
        state_op = Op.POP(
            Op.CALL(
                address=pre.nonexistent_account(),
                value=subcall_forwarded_value,
                # gas accounting
                value_transfer=True,
                account_new=True,
            )
        )
    else:
        state_op = Op.POP(Op.CREATE(value=0, offset=0, size=1))

    assert state_op.state_cost(fork) > 0, (
        "initcode must perform a non-zero state-gas operation"
    )

    if deposit_fail_mode == "oversized_code":
        deposit_fail = Op.RETURN(0, fork.max_code_size() + 1)
    elif deposit_fail_mode == "oog_deposit":
        # Return code at max size: passes the size check but code
        # deposit state gas (max_code_size * cost_per_state_byte)
        # exceeds available state gas in the child frame, causing OOG.
        deposit_fail = Op.RETURN(0, fork.max_code_size())
    else:
        # Return single 0xEF byte: EIP-3541 rejects the code before
        # the size check or any deposit charging, halting the deposit.
        deposit_fail = Op.MSTORE8(0, 0xEF) + Op.RETURN(0, 1)

    initcode = state_op + deposit_fail
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        to=None,
                        data=initcode,
                        value=entry_account_value + subcall_forwarded_value,
                        state_gas_reservoir=0,
                        sender=pre.fund_eoa(),
                        expected_receipt=TransactionReceipt(
                            status=0,
                            cumulative_gas_used=gas_limit_cap,
                        ),
                    ),
                ],
                header_verify=Header(gas_used=gas_limit_cap),
            ),
        ],
        post={},
    )


@pytest.mark.parametrize(
    "target",
    [
        pytest.param("new", id="new_account"),
        pytest.param("existing", id="existing_account"),
    ],
)
@pytest.mark.pre_alloc_mutable()
@pytest.mark.valid_from("EIP8037")
def test_create_tx_header_gas_used(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    target: str,
) -> None:
    """
    Verify block header gas_used for a successful CREATE transaction.

    A contract creation tx (to=None) with known gas costs. Compute
    exact gas_used from first principles and verify against the block
    header. Catches bugs where clients report gas_limit instead of
    actual consumed gas.

    For a fresh target the top-frame NEW_ACCOUNT state gas is charged and
    dominates the execution gas, so gas_used == NEW_ACCOUNT. For a
    pre-existing balance-only leaf the target is not EMPTY pre-tx, so the
    top-frame NEW_ACCOUNT is never charged: net state gas is zero and only
    the execution dimension remains. The block-level calldata floor tops up
    that execution remainder, so the expected value is the greater of the
    execution intrinsic and the floor, and fails if a stray NEW_ACCOUNT is
    charged.
    """
    initcode = Op.STOP
    create_state_gas = fork.create_state_gas(code_size=1)

    if target == "existing":
        sender = pre.fund_eoa(nonce=0)
        contract_address = compute_create_address(address=sender, nonce=0)
        # Balance-only leaf: alive and deployable, so the creation
        # succeeds and (being non-EMPTY pre-tx) the top-frame NEW_ACCOUNT
        # is never charged.
        pre.fund_address(contract_address, amount=1)
    else:
        sender = pre.fund_eoa()

    tx = Transaction(
        to=None,
        data=initcode,
        state_gas_reservoir=create_state_gas,
        sender=sender,
    )

    # block_gas_used = max(block_execution, block_state)
    if target == "existing":
        intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
        # Execution-only creation intrinsic; STOP initcode deploys empty
        # code (zero deposit) and the pre-existing target adds no state
        # gas. The block-level calldata floor tops up this small execution
        # remainder and, being the larger of the two, is what the header
        # reflects (the floor applies to block-level execution gas).
        execution_intrinsic = intrinsic_cost(
            calldata=bytes(initcode),
            contract_creation=True,
            return_cost_deducted_prior_execution=True,
        )
        floor = fork.transaction_data_floor_cost_calculator()(
            data=bytes(initcode), contract_creation=True
        )
        assert floor > execution_intrinsic, (
            "the floor must bind for this arm to pin floor-in-header"
        )
        expected_gas_used = max(execution_intrinsic, floor)
    else:
        # For a minimal CREATE tx deploying Op.STOP (1 byte),
        # state gas (new account) dominates execution gas.
        expected_gas_used = fork.transaction_top_frame_state_gas(
            contract_creation=True
        )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=expected_gas_used),
            ),
        ],
        post={},
    )


@pytest.mark.valid_from("EIP8037")
def test_create_initcode_halt_no_code_deposit_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify an initcode exceptional halt leaves no state gas charged.

    A CREATE transaction runs INVALID before returning any code, so code
    deposit never happens. The exceptional halt also rolls back the top-frame
    new-account charge. The transaction is deliberately funded below the gas
    limit cap, making that charge spill into execution gas. After rollback the
    restored spill is forfeited as execution gas, so the receipt and header
    must both equal the full transaction gas limit and state gas used is zero.

    Complements test_create_revert_no_code_deposit_state_gas which
    covers the REVERT path.
    """
    initcode = Op.INVALID
    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        calldata=initcode,
        contract_creation=True,
        return_cost_deducted_prior_execution=True,
    )
    new_account_state = fork.transaction_top_frame_state_gas(
        contract_creation=True
    )
    assert new_account_state > intrinsic_execution, (
        "the rolled-back state charge must dominate the intrinsic execution"
    )

    # With no reservoir, the account charge spills into gas_left. INVALID
    # restores that spill and then forfeits it as execution gas.
    gas_limit = intrinsic_execution + new_account_state

    tx = Transaction(
        to=None,
        data=initcode,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            status=0,
            cumulative_gas_used=gas_limit,
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=gas_limit),
            ),
        ],
        post={},
    )


@pytest.mark.valid_from("EIP8037")
def test_state_gas_spill_header_gas_used(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify header gas_used when state gas spills into gas_left.

    A transaction performs an SSTORE with state gas partially from
    the reservoir and partially spilling into gas_left. Verify the
    block header gas_used reflects the correct 2D max accounting.
    """
    # SSTORE zero-to-nonzero with small reservoir
    sstore_code = Op.SSTORE(0, 1) + Op.STOP
    contract = pre.deploy_contract(code=sstore_code)

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas = intrinsic_cost()

    sstore_state_gas = sstore_code.state_cost(fork)
    evm_execution = sstore_code.execution_cost(fork)

    # Reservoir = half the SSTORE state gas, rest spills to gas_left
    reservoir = sstore_state_gas // 2

    tx = Transaction(
        to=contract,
        state_gas_reservoir=reservoir,
        sender=pre.fund_eoa(),
    )

    tx_execution = intrinsic_gas + evm_execution
    tx_state = sstore_state_gas
    expected_gas_used = max(tx_execution, tx_state)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=expected_gas_used),
            ),
        ],
        post={contract: Account(storage={0: 1})},
    )


@pytest.mark.parametrize(
    "failure_mode",
    [
        pytest.param("revert", id="revert"),
        pytest.param("halt", id="halt"),
    ],
)
@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("EIP8037")
def test_failed_create_header_gas_used(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    failure_mode: str,
) -> None:
    """
    Verify block header gas_used for failed CREATE/CREATE2 via opcode.

    A factory contract calls CREATE/CREATE2 which fails (revert or
    halt). Verify the block is accepted with correct gas accounting.
    Parametrized across failure modes and create opcodes.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    create_state_gas = fork.create_state_gas(code_size=0)

    if failure_mode == "revert":
        init_code = Op.REVERT(0, 0)
    else:
        init_code = Op.INVALID

    mstore_value, size = init_code_at_high_bytes(init_code)

    create_call = (
        create_opcode(
            value=0, offset=0, size=size, salt=0, init_code_size=size
        )
        if create_opcode == Op.CREATE2
        else create_opcode(value=0, offset=0, size=size, init_code_size=size)
    )

    factory_code = Op.MSTORE(0, mstore_value, new_memory_size=32) + create_call
    factory = pre.deploy_contract(factory_code)
    create_address = compute_create_address(
        address=factory,
        nonce=1,
        salt=0,
        initcode=bytes(init_code),
        opcode=create_opcode,
    )

    tx = Transaction(
        to=factory,
        state_gas_reservoir=create_state_gas,
        sender=pre.fund_eoa(),
    )

    if failure_mode == "revert":
        # REVERT returns the unused child grant. Net execution consists only
        # of the factory and the initcode instructions that actually ran.
        expected_gas_used = (
            intrinsic_cost
            + factory_code.execution_cost(fork)
            + init_code.execution_cost(fork)
        )
    else:
        # INVALID burns the child's all-but-one-64th grant. The factory keeps
        # one 64th and reaches the end of its code without spending it.
        gas_left_before_child = (
            gas_limit_cap - intrinsic_cost - factory_code.execution_cost(fork)
        )
        parent_gas_left = gas_left_before_child // 64
        expected_gas_used = gas_limit_cap - parent_gas_left

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=expected_gas_used),
            ),
        ],
        post={
            factory: Account(nonce=2),
            create_address: Account.NONEXISTENT,
        },
    )


@pytest.mark.parametrize(
    "failure_mode",
    [
        pytest.param("nonce_overflow", id="nonce_overflow"),
        pytest.param("insufficient_balance", id="insufficient_balance"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_create_silent_failure_refunds_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    failure_mode: str,
) -> None:
    """
    Verify CREATE silent failure refunds account state gas.

    Failures that skip child spawning (nonce overflow, insufficient
    balance) refund `GAS_NEW_ACCOUNT` to the reservoir. Block state
    gas reflects only the probe SSTORE, not the refunded CREATE.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()

    mstore_value, size = init_code_at_high_bytes(Op.STOP)
    value = 1 if failure_mode == "insufficient_balance" else 0

    storage = Storage()
    factory_code = (
        Op.MSTORE(0, mstore_value)
        + Op.POP(Op.CREATE(value=value, offset=0, size=size))
        + Op.SSTORE(storage.store_next(1, "reservoir_ok"), 1)
    )
    if failure_mode == "nonce_overflow":
        factory = pre.deploy_contract(code=factory_code, nonce=2**64 - 1)
    else:
        factory = pre.deploy_contract(code=factory_code)

    tx = Transaction(
        to=factory,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    # CREATE's GAS_NEW_ACCOUNT is refunded (silent failure, no child
    # spawned). SSTORE's state portion is tracked separately in
    # tx_state, so only the execution dimension remains here.
    tx_execution = intrinsic_cost + factory_code.execution_cost(fork)
    tx_state = sstore_state_gas
    expected = max(tx_execution, tx_state)
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], header_verify=Header(gas_used=expected))],
        post={factory: Account(storage=storage)},
    )


@pytest.mark.parametrize(
    "gas_limit_mode",
    [
        pytest.param("reservoir", id="with_reservoir"),
        pytest.param("spillover", id="spillover"),
    ],
)
@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("EIP8037")
def test_create_child_revert_refunds_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    gas_limit_mode: str,
) -> None:
    """
    Verify CREATE/CREATE2 child REVERT refunds parent's account gas.

    On REVERT the parent's `GAS_NEW_ACCOUNT` charge is refunded to
    the reservoir (on top of the child's state gas returned via
    `incorporate_child_on_error`). Block state gas reflects only the
    probe SSTORE. The spillover variant runs with tx.gas at the cap
    (reservoir zero), so the state gas charge spills into `gas_left`
    and the LIFO refund returns it to `gas_left`.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()

    init_code = Op.REVERT(0, 0)
    mstore_value, size = init_code_at_high_bytes(init_code)

    create_call = create_opcode(
        value=0, offset=0, size=size, init_code_size=size
    )

    storage = Storage()
    factory_code = (
        Op.MSTORE(0, mstore_value, new_memory_size=32)
        + Op.POP(create_call)
        + Op.SSTORE(storage.store_next(1, "reservoir_ok"), 1)
    )
    factory = pre.deploy_contract(code=factory_code)

    tx = Transaction(
        to=factory,
        state_gas_reservoir=(
            0 if gas_limit_mode == "spillover" else sstore_state_gas
        ),
        sender=pre.fund_eoa(),
    )

    # CREATE's GAS_NEW_ACCOUNT is refunded on child REVERT. SSTORE's
    # state portion is tracked separately. Child REVERT execution
    # (init_code execution) is propagated via
    # incorporate_child_on_error.
    tx_execution = (
        intrinsic_cost
        + factory_code.execution_cost(fork)
        + init_code.gas_cost(fork)
    )
    tx_state = sstore_state_gas
    expected = max(tx_execution, tx_state)
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], header_verify=Header(gas_used=expected))],
        post={factory: Account(storage=storage)},
    )


@pytest.mark.parametrize(
    "failure_mode",
    [
        pytest.param("initcode_halt", id="initcode_halt"),
        pytest.param("invalid_prefix", id="invalid_prefix"),
    ],
)
@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("EIP8037")
def test_create_child_halt_refunds_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    failure_mode: str,
) -> None:
    """
    Verify CREATE/CREATE2 child halt refunds parent's account gas.

    Exceptional halts (invalid opcode, EIP-3541 invalid prefix)
    consume all forwarded execution gas, so block accounting cannot
    strictly discriminate via header gas. Tight
    gas tuning via a caller wrapper leaves the factory with just
    enough `gas_left` to pay the probe SSTORE's execution portion
    but not enough to spill the state portion, so the probe SSTORE
    can only succeed via the refunded reservoir.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    init_code: Op | Bytecode
    if failure_mode == "initcode_halt":
        init_code = Op.INVALID
    elif failure_mode == "invalid_prefix":
        # Return code starting with 0xEF (EIP-3541 invalid prefix).
        init_code = Op.MSTORE8(0, 0xEF) + Op.RETURN(0, 1)

    mstore_value, size = init_code_at_high_bytes(init_code)

    create_call = (
        create_opcode(value=0, offset=0, size=size, salt=0)
        if create_opcode == Op.CREATE2
        else create_opcode(value=0, offset=0, size=size)
    )

    storage = Storage()
    factory = pre.deploy_contract(
        code=(
            Op.MSTORE(0, mstore_value)
            + Op.POP(create_call)
            + Op.SSTORE(storage.store_next(1, "reservoir_ok"), 1)
        ),
    )

    # Tight gas tuning: child halt consumes all forwarded execution
    # gas. Factory retains
    # ~(forwarded - pre_sstore_execution) / 64 after CREATE. Target
    # the discrimination window `(probe_execution,
    # probe_execution + sstore_state_gas)` so the probe SSTORE
    # execution fits but state gas spillover from `gas_left` under
    # the old behavior OOGs.
    pre_sstore_code = Op.MSTORE(0, mstore_value) + Op.POP(create_call)
    pre_sstore_execution = pre_sstore_code.execution_cost(fork)
    probe_code = Op.SSTORE(0, 1)
    probe_execution = probe_code.execution_cost(fork)
    target_gas_left = probe_execution + sstore_state_gas // 2
    forwarded_gas = target_gas_left * 64 + pre_sstore_execution
    # Reservoir sized for CREATE charge only — SSTORE must pull
    # from the refunded reservoir, not from spill.
    caller = pre.deploy_contract(
        code=Op.CALL(gas=forwarded_gas, address=factory)
    )
    tx = Transaction(
        to=caller,
        state_gas_reservoir=create_call.state_cost(fork),
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={factory: Account(storage=storage)}, tx=tx)


@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("EIP8037")
def test_create_mixed_success_and_failure_block_accounting(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Verify block state gas excludes refunded charges from failed CREATE.

    One successful CREATE plus one failed CREATE (REVERT): block
    state gas reflects only the successful charges.
    """
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()
    create_account_state_gas = fork.create_state_gas(code_size=0)

    success_value, success_size = init_code_at_high_bytes(Op.STOP)
    fail_value, fail_size = init_code_at_high_bytes(Op.REVERT(0, 0))

    def call(size: int, salt: int) -> Bytecode:
        if create_opcode == Op.CREATE2:
            return create_opcode(value=0, offset=0, size=size, salt=salt)
        return create_opcode(value=0, offset=0, size=size)

    factory_code = (
        Op.MSTORE(0, success_value)
        + Op.POP(call(size=success_size, salt=0))
        + Op.MSTORE(0, fail_value)
        + Op.POP(call(size=fail_size, salt=1))
    )
    factory = pre.deploy_contract(code=factory_code)

    # STOP deploys empty code, so only GAS_NEW_ACCOUNT counts for
    # the successful CREATE, and the failed CREATE is refunded.
    block_state = create_account_state_gas
    tx_execution = intrinsic_gas + factory_code.execution_cost(fork)
    assert block_state > tx_execution, "state gas must dominate"
    expected = max(tx_execution, block_state)

    tx = Transaction(
        to=factory,
        state_gas_reservoir=2 * create_account_state_gas,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], header_verify=Header(gas_used=expected))],
        post={},
    )


@pytest.mark.pre_alloc_mutable()
@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("EIP8037")
def test_create_collision_refunds_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Verify CREATE/CREATE2 address collision refunds account state gas.

    The collision path increments the factory nonce and burns the
    forwarded execution gas (consumed by the never-spawned child), but
    still refunds `GAS_NEW_ACCOUNT` to the reservoir. Tight gas
    tuning limits the factory's post-collision `gas_left` so the
    probe SSTORE can only succeed via the refunded reservoir, not
    by spilling state gas from `gas_left`.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    init_code = Op.STOP
    mstore_value, size = init_code_at_high_bytes(init_code)
    salt = 0

    storage = Storage()
    create_call = (
        create_opcode(value=0, offset=0, size=size, salt=salt)
        if create_opcode == Op.CREATE2
        else create_opcode(value=0, offset=0, size=size)
    )
    factory_code = (
        Op.MSTORE(0, mstore_value)
        + Op.POP(create_call)
        + Op.SSTORE(storage.store_next(1, "reservoir_ok"), 1)
    )
    factory = pre.deploy_contract(code=factory_code)

    collision_target = compute_create_address(
        address=factory,
        nonce=1,
        salt=salt,
        initcode=bytes(init_code),
        opcode=create_opcode,
    )
    pre.deploy_contract(code=Op.STOP, address=collision_target)

    # Tight gas tuning: factory retains
    # ~(forwarded - pre_sstore_execution) / 64 after collision burns
    # `max_message_call_gas` as execution. Target the discrimination
    # window `(probe_execution, probe_execution + sstore_state_gas)` so
    # the probe SSTORE execution fits but state gas spillover from
    # `gas_left` under the old behavior OOGs.
    pre_sstore_code = Op.MSTORE(0, mstore_value) + Op.POP(create_call)
    pre_sstore_execution = pre_sstore_code.execution_cost(fork)
    probe_code = Op.SSTORE(0, 1)
    probe_execution = probe_code.execution_cost(fork)
    target_gas_left = probe_execution + sstore_state_gas // 2
    forwarded_gas = target_gas_left * 64 + pre_sstore_execution
    # Reservoir sized for CREATE charge only — SSTORE must pull from
    # the refunded reservoir, not from spill.
    caller = pre.deploy_contract(
        code=Op.CALL(gas=forwarded_gas, address=factory)
    )
    tx = Transaction(
        to=caller,
        state_gas_reservoir=create_call.state_cost(fork),
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={factory: Account(storage=storage)}, tx=tx)


@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("EIP8037")
def test_create_code_deposit_oog_refunds_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Verify CREATE/CREATE2 code-deposit OOG refunds account state gas.

    The initcode executes successfully and returns code longer than
    `MAX_CODE_SIZE`, triggering an exceptional halt during code
    deposit. Tight gas tuning limits the factory's post-halt
    `gas_left` so the probe SSTORE can only succeed via the
    refunded reservoir, not by spilling state gas from `gas_left`.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    max_code_size = fork.max_code_size()

    # Init code returns (max_code_size + 1) bytes, triggering the
    # OOG path in process_create_message code deposit.
    init_code = Op.RETURN(0, max_code_size + 1)
    mstore_value, size = init_code_at_high_bytes(init_code)

    create_call = (
        create_opcode(value=0, offset=0, size=size, salt=0)
        if create_opcode == Op.CREATE2
        else create_opcode(value=0, offset=0, size=size)
    )

    storage = Storage()
    factory = pre.deploy_contract(
        code=(
            Op.MSTORE(0, mstore_value)
            + Op.POP(create_call)
            + Op.SSTORE(storage.store_next(1, "reservoir_ok"), 1)
        ),
    )

    # Child halt consumes all forwarded gas; factory retains only
    # ~(forwarded - pre_sstore_execution) / 64. Target the
    # discrimination window so SSTORE execution fits but state gas
    # spillover fails.
    pre_sstore_code = Op.MSTORE(0, mstore_value) + Op.POP(create_call)
    pre_sstore_execution = pre_sstore_code.execution_cost(fork)
    probe_code = Op.SSTORE(0, 1)
    probe_execution = probe_code.execution_cost(fork)
    target_gas_left = probe_execution + sstore_state_gas // 2
    forwarded_gas = target_gas_left * 64 + pre_sstore_execution
    caller = pre.deploy_contract(
        code=Op.CALL(gas=forwarded_gas, address=factory)
    )
    tx = Transaction(
        to=caller,
        state_gas_reservoir=create_call.state_cost(fork),
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={factory: Account(storage=storage)}, tx=tx)


@pytest.mark.parametrize("slots", [0, 1, 3])
@pytest.mark.parametrize("fail_mode", ["eip3541", "oog_deposit"])
@pytest.mark.valid_from("EIP8037")
def test_create2_failed_deposit_refunds_storage_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    slots: int,
    fail_mode: str,
) -> None:
    """
    Test a failed CREATE2 deposit refunds the init's storage-slot state gas.

    Total state gas refunded is independent of `slots`, so a client
    that drops the slot refund diverges for `slots >= 1` and
    `slots == 0` is the negative control. The receipt pins the init
    frame's whole 63/64 share as burned, slot spills included.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()

    # init: write `slots` new storage slots, then trigger a deposit failure
    init_code = Bytecode()
    for i in range(slots):
        init_code += Op.SSTORE(i, i + 1)
    if fail_mode == "eip3541":
        # return 0xEF -> EIP-3541 rejects the deposited code
        init_code += Op.MSTORE8(0, 0xEF) + Op.RETURN(0, 1)
    else:
        # return max-size code: the code-deposit state gas cannot be paid
        init_code += Op.RETURN(0, fork.max_code_size())
    mstore_value, size = init_code_at_high_bytes(init_code)

    create_call = Op.CREATE2(
        value=0, offset=0, size=size, salt=0, init_code_size=size
    )
    storage = Storage()
    factory_create_code = (
        Op.MSTORE(0, mstore_value, new_memory_size=32) + create_call
    )
    factory_post_create_code = (
        # Store the CREATE2 result (0 on failure): a cold 0 -> 0 no-op.
        Op.PUSH1(storage.store_next(0, "create2_failed"))
        + Op.SSTORE.with_metadata(original_value=0, new_value=0)(
            unchecked=True
        )
    )
    factory = pre.deploy_contract(
        code=factory_create_code + factory_post_create_code,
    )

    # Simulate the runtime gas: the whole-cap gas limit leaves no
    # reservoir, so every state charge spills from `gas_left` and the
    # failed deposit burns the init frame's whole share regardless of
    # `slots` or `fail_mode`.
    sim_gas_left = (
        gas_limit_cap
        - intrinsic_cost
        - factory_create_code.execution_cost(fork)
    )
    # CREATE2's new-account state gas spills wholly from gas_left and
    # refills there when the create fails.
    new_account_state_gas = create_call.state_cost(fork)
    sim_gas_left -= new_account_state_gas
    # 63/64 retention: the factory keeps gas_left // 64.
    sim_gas_left = sim_gas_left // 64
    sim_gas_left += new_account_state_gas
    sim_gas_left -= factory_post_create_code.execution_cost(fork)
    expected_cumulative = gas_limit_cap - sim_gas_left

    tx = Transaction(
        to=factory,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative,
        ),
    )

    state_test(
        pre=pre,
        post={factory: Account(storage=storage)},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_cumulative),
    )


@pytest.mark.parametrize(
    "reservoir_covers",
    [
        pytest.param(True, id="charge_from_reservoir"),
        pytest.param(False, id="charge_spills_from_gas_left"),
    ],
)
@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("EIP8037")
def test_create_account_charge_reduces_child_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    reservoir_covers: bool,
) -> None:
    """
    Verify the early NEW_ACCOUNT charge reduces forwarded child gas.

    `generic_create` charges NEW_ACCOUNT before computing the child's
    63/64 share. When the reservoir covers the charge `gas_left` is
    untouched and the child receives the full share. When the reservoir
    is empty the charge spills NEW_ACCOUNT from `gas_left` first, so the
    child receives `NEW_ACCOUNT * 63 / 64` less. The init code burns a
    fixed amount sized between the two shares, so it deploys when the
    charge comes from the reservoir and runs out of gas when it spills.
    The target is fresh, so NEW_ACCOUNT is required. The created account is
    checked directly, avoiding a post-CREATE SSTORE with an unrelated state
    gas requirement.
    """
    new_account = create_opcode(account_new=True).state_cost(fork)
    memory_gas = fork.memory_expansion_gas_calculator()

    # Factory `gas_left` at the NEW_ACCOUNT charge. Three times
    # NEW_ACCOUNT gives a wide discrimination window and a large
    # absolute child share.
    gas_at_charge = 3 * new_account
    full_share = gas_at_charge - gas_at_charge // 64
    spilled = gas_at_charge - new_account
    reduced_share = spilled - spilled // 64
    # Burn the middle of `(reduced_share, full_share]` for robustness.
    target_burn = (full_share + reduced_share) // 2

    # Init code burns `target_burn` execution gas via one MSTORE memory
    # expansion, then deploys empty code (zero code deposit). Invert
    # `words * MEMORY_PER_WORD + words ** 2 // 512 = target_mem` to size
    # the sink offset from gas rather than a magic number.
    init_static = (Op.MSTORE(0, 0) + Op.RETURN(0, 0)).gas_cost(fork)
    target_mem = target_burn - init_static
    # Memory cost is monotonic in word count, so binary search the
    # largest word count whose expansion stays within `target_mem`.
    low, high = 1, target_mem
    while low < high:
        mid = (low + high + 1) // 2
        if int(memory_gas(new_bytes=mid * 32)) <= target_mem:
            low = mid
        else:
            high = mid - 1
    words = low
    sink_offset = (words - 1) * 32
    child_burn = init_static + int(memory_gas(new_bytes=words * 32))
    assert reduced_share < child_burn <= full_share

    init_code = Op.MSTORE(sink_offset, 0) + Op.RETURN(0, 0)
    mstore_value, size = init_code_at_high_bytes(init_code)
    create_call = (
        create_opcode(value=0, offset=0, size=size, salt=0)
        if create_opcode == Op.CREATE2
        else create_opcode(value=0, offset=0, size=size)
    )

    storage = Storage()
    expected = 1 if reservoir_covers else 0
    factory = pre.deploy_contract(
        code=Op.MSTORE(0, mstore_value)
        + Op.SSTORE(
            storage.store_next(expected, "child_succeeds"),
            Op.GT(create_call, 0),
        ),
    )

    # Pre-existing balance-only target: the success-refund path. Under
    # the old conditional approach this alive target skips NEW_ACCOUNT,
    # so the child gets the full share and fits in both cases.
    if create_opcode == Op.CREATE2:
        create_address = compute_create2_address(
            address=factory, salt=0, initcode=bytes(init_code)
        )
    else:
        create_address = compute_create_address(address=factory, nonce=1)
    pre.fund_address(create_address, amount=1)

    # Execution gas the factory spends before the NEW_ACCOUNT charge: the
    # initcode setup MSTORE plus the create opcode's execution portion.
    setup = Op.MSTORE(0, mstore_value)
    pre_charge_execution = setup.gas_cost(fork) + create_call.execution_cost(
        fork
    )
    forwarded_gas = gas_at_charge + pre_charge_execution
    caller = pre.deploy_contract(
        code=Op.CALL(gas=forwarded_gas, address=factory)
    )
    tx = Transaction(
        to=caller,
        state_gas_reservoir=new_account if reservoir_covers else 0,
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={factory: Account(storage=storage)}, tx=tx)


@pytest.mark.parametrize(
    ("init_code", "floor_binds"),
    [
        pytest.param(
            Op.REVERT(0, 10_000, new_memory_size=10_000),
            False,
            id="revert",
        ),
        pytest.param(Op.REVERT(0, 0), True, id="revert_floor_bound"),
        pytest.param(Op.INVALID, None, id="halt"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_failed_create_tx_refills_top_frame_new_account(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    init_code: Bytecode,
    floor_binds: bool | None,
) -> None:
    """
    Verify the top-frame NEW_ACCOUNT of a creation tx is refilled when the
    initcode fails.

    Under EIP-2780 the created account's ``NEW_ACCOUNT`` state gas is
    charged in the top-frame preparation (not the intrinsic), so
    ``gas_limit`` must cover it for the initcode to run at all. When the
    initcode then fails the whole creation rolls back and no account
    persists:

    * REVERT preserves ``gas_left`` and ``restore_state_gas`` returns
      the spilled ``NEW_ACCOUNT`` to it, so the state block nets to zero
      and only the execution consumption counts as work. The calldata floor
      tops up the billed amount and the block-level execution gas alike, so
      receipt and header agree at the greater of consumption and floor:
      the memory expansion keeps ``revert`` above the floor, while the
      bare ``revert_floor_bound`` pins the floor in both.
    * HALT (INVALID) refills the spilled ``NEW_ACCOUNT`` to ``gas_left``
      and then burns all of it, so the sender pays the full ``gas_limit``.
    """
    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()

    intrinsic_execution = intrinsic_calc(
        calldata=bytes(init_code),
        contract_creation=True,
        return_cost_deducted_prior_execution=True,
    )
    # gas_limit must cover the top-frame NEW_ACCOUNT and the initcode's own
    # execution gas so the initcode runs to completion.
    gas_limit = (
        intrinsic_execution
        + fork.transaction_top_frame_state_gas(contract_creation=True)
        + init_code.execution_cost(fork)
        + 1000
    )

    if init_code == Op.INVALID:
        # Exceptional halt burns all gas_left (the refilled NEW_ACCOUNT
        # included).
        expected_gas_used = gas_limit
    else:
        # REVERT refills the spilled NEW_ACCOUNT, netting the state block
        # to zero, so only the execution consumption counts as work. The
        # calldata floor binds the billed amount and the block-level
        # execution gas alike, so receipt and header agree either way.
        execution_consumed = intrinsic_execution + init_code.execution_cost(
            fork
        )
        floor = fork.transaction_data_floor_cost_calculator()(
            data=bytes(init_code), contract_creation=True
        )
        assert (floor > execution_consumed) == floor_binds, (
            "init code lands on the wrong side of the floor"
        )
        expected_gas_used = max(execution_consumed, floor)

    sender = pre.fund_eoa()
    created = compute_create_address(address=sender, nonce=0)

    tx = Transaction(
        to=None,
        data=init_code,
        gas_limit=gas_limit,
        sender=sender,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_gas_used,
        ),
    )

    state_test(
        pre=pre,
        post={created: Account.NONEXISTENT},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.pre_alloc_mutable()
@pytest.mark.valid_from("EIP8037")
def test_create_tx_collision_has_no_net_new_account_charge(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify a creation-tx collision leaves no net NEW_ACCOUNT charge.

    Under EIP-2780 the created account's ``NEW_ACCOUNT`` is a top-frame
    charge, but on an address collision the target already exists
    pre-tx, the create path returns ``AddressCollision`` before the top
    frame is prepared. A full NEW_ACCOUNT-sized reservoir is supplied as an
    oracle: collision burns the capped execution grant but must return that
    reservoir unused. The exact receipt and header therefore equal the gas
    limit cap; any surviving account charge increases the receipt.
    """
    init_code = Op.STOP
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    new_account_state = fork.transaction_top_frame_state_gas(
        contract_creation=True
    )

    sender = pre.fund_eoa()
    collision_target = compute_create_address(address=sender, nonce=0)
    pre[collision_target] = Account(nonce=1)

    tx = Transaction(
        to=None,
        data=init_code,
        state_gas_reservoir=new_account_state,
        sender=sender,
        expected_receipt=TransactionReceipt(
            status=0,
            cumulative_gas_used=gas_limit_cap,
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=gas_limit_cap),
            ),
        ],
        post={collision_target: Account(nonce=1)},
    )


@pytest.mark.pre_alloc_mutable()
@pytest.mark.execute(pytest.mark.skip(reason="Requires specific gas price"))
@pytest.mark.valid_from("EIP8037")
def test_create_tx_collision_refunds_reservoir(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify the state-gas reservoir is refunded on a depth-0 CREATE-tx
    address collision when `gas_limit > TX_MAX_GAS_LIMIT`.

    EIP-8037 splits `gas_limit` into the capped execution budget and a
    state-gas reservoir. On collision the inner execution gas is burnt
    and `intrinsic_state_gas` is refunded; the reservoir must also
    be refunded to the sender. `header.gas_used` is fixed at the
    execution cap regardless of reservoir handling, so the sender's
    post-balance is the primary discriminating assertion.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    init_code = Op.STOP
    # +1 above intrinsic_state_gas (= create_state_gas(code_size=0)
    # for empty-code CREATE-tx) makes message.state_gas_reservoir > 0.
    reservoir = fork.create_state_gas(code_size=0) + 1
    initial_fund = 10**18

    sender = pre.fund_eoa(initial_fund)
    collision_target = compute_create_address(address=sender, nonce=0)
    pre[collision_target] = Account(nonce=1)

    tx_gas_price = 7
    tx = Transaction(
        to=None,
        data=init_code,
        state_gas_reservoir=reservoir,
        sender=sender,
        gas_price=tx_gas_price,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=gas_limit_cap),
            ),
        ],
        post={
            sender: Account(
                balance=initial_fund - gas_limit_cap * tx_gas_price,
                nonce=1,
            ),
            collision_target: Account(nonce=1, code=b"", storage={}),
        },
    )


@pytest.mark.valid_from("EIP8037")
def test_create_onto_alive_skips_new_account_charge(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify CREATE2 skips the NEW_ACCOUNT charge for an alive target.

    A pre-funded, code-less target is alive but remains deployable. The
    transaction budget includes the static NEW_ACCOUNT estimate; because
    runtime must skip that charge, the unused gas lets the following SSTORE
    succeed. Charging NEW_ACCOUNT incorrectly consumes that headroom and
    prevents the storage probe.
    """
    salt = 0
    create = Op.POP(Op.CREATE2(0, 0, 0, salt))
    storage = Storage()
    contract = pre.deploy_contract(
        code=create + Op.SSTORE(storage.store_next(1), 1)
    )
    target = compute_create2_address(address=contract, salt=salt, initcode=b"")
    pre.fund_address(target, amount=1)

    gas_limit = (
        fork.transaction_intrinsic_cost_calculator()() + create.gas_cost(fork)
    )
    tx = Transaction(to=contract, gas_limit=gas_limit, sender=pre.fund_eoa())

    post = {
        contract: Account(storage=storage),
        target: Account(nonce=1, balance=1),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.inclusion_test
@pytest.mark.parametrize(
    "initcode_size_delta",
    [
        pytest.param(0, id="at_max"),
        pytest.param(1, id="over_max", marks=pytest.mark.exception_test),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_oversized_initcode_tx_no_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    initcode_size_delta: int,
) -> None:
    """
    Verify a creation tx with oversized initcode is rejected before
    any state gas is charged.
    """
    max_size = fork.max_initcode_size()
    size = max_size + initcode_size_delta
    initcode = Initcode(deploy_code=Op.STOP, initcode_length=size)

    sender = pre.fund_eoa()
    create_address = compute_create_address(address=sender, nonce=0)

    create_state_gas = fork.create_state_gas(code_size=len(Op.STOP))

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        state_gas_reservoir=create_state_gas,
    )

    if initcode_size_delta > 0:
        tx.error = TransactionException.INITCODE_SIZE_EXCEEDED
        post: dict = {create_address: Account.NONEXISTENT}
    else:
        post = {create_address: Account(code=Op.STOP)}

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                exception=(
                    TransactionException.INITCODE_SIZE_EXCEEDED
                    if initcode_size_delta > 0
                    else None
                ),
            ),
        ],
        post=post,
    )


@pytest.mark.parametrize(
    "initcode_size_delta",
    [
        pytest.param(0, id="at_max"),
        pytest.param(1, id="over_max"),
    ],
)
@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("EIP8037")
def test_oversized_initcode_opcode_no_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    initcode_size_delta: int,
) -> None:
    """
    Verify CREATE/CREATE2 with oversized initcode fails the size
    check before any state gas is charged.
    """
    max_size = fork.max_initcode_size()
    size = max_size + initcode_size_delta
    initcode = bytes(size)

    factory_code = (
        create_opcode(
            value=0,
            offset=0,
            size=size,
            salt=0,
            init_code_size=size,
            new_memory_size=size,
        )
        if create_opcode == Op.CREATE2
        else create_opcode(
            value=0,
            offset=0,
            size=size,
            init_code_size=size,
            new_memory_size=size,
        )
    )

    factory = pre.deploy_contract(factory_code)
    factory_execution = factory_code.execution_cost(fork)

    caller_code = Op.POP(
        Op.CALL(
            gas=factory_execution,
            address=factory,
        )
    )
    caller = pre.deploy_contract(caller_code)

    create_address = compute_create_address(
        address=factory,
        nonce=1,
        salt=0,
        initcode=initcode,
        opcode=create_opcode,
    )

    create_state_gas = factory_code.state_cost(fork)
    expected_execution = (
        fork.transaction_intrinsic_cost_calculator()()
        + caller_code.execution_cost(fork)
        + factory_execution
    )
    assert create_state_gas > expected_execution, (
        "NEW_ACCOUNT must dominate execution to detect a stray state charge"
    )
    expected_state = create_state_gas if initcode_size_delta == 0 else 0
    expected_gas_used = max(expected_execution, expected_state)

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        state_gas_reservoir=create_state_gas,
    )

    post: dict = {factory: Account(nonce=2 if initcode_size_delta == 0 else 1)}
    if initcode_size_delta == 0:
        post[create_address] = Account(nonce=1, code=b"")
    else:
        post[create_address] = Account.NONEXISTENT

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=expected_gas_used),
            )
        ],
        post=post,
    )


@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_in_create_tx_initcode(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify state gas accounting when a creation tx's initcode
    immediately SELFDESTRUCTs to a new beneficiary.

    Under EIP-2780 the created contract's ``NEW_ACCOUNT`` is charged at
    the top frame from ``gas_left`` (not the intrinsic), so ``gas_limit``
    must cover it on top of the initcode. The block state gas is the
    created contract's ``NEW_ACCOUNT`` plus the fresh beneficiary's
    ``NEW_ACCOUNT`` charged by the SELFDESTRUCT.
    """
    create_state_gas = fork.create_state_gas(code_size=0)

    beneficiary = 0xDEAD
    # `account_new` folds the beneficiary's `ACCOUNT_WRITE` execution
    # cost and account-creation state gas into `gas_cost`.
    initcode = Op.SELFDESTRUCT(beneficiary, account_new=True)

    sender = pre.fund_eoa()
    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    intrinsic_execution = intrinsic_calc(
        calldata=bytes(initcode), contract_creation=True, sends_value=True
    )

    # State: the created contract's top-frame NEW_ACCOUNT plus the fresh
    # beneficiary's NEW_ACCOUNT from the SELFDESTRUCT.
    expected_state = create_state_gas + initcode.state_cost(fork)

    initcode_gas = initcode.gas_cost(fork)
    gas_limit = intrinsic_execution + create_state_gas + initcode_gas + 1000

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        value=1,
        gas_limit=gas_limit,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=expected_state),
            ),
        ],
        post={},
    )


@pytest.mark.parametrize(
    "outer_outcome",
    [
        pytest.param("succeeds", id="outer_succeeds"),
        pytest.param("reverts", id="outer_reverts"),
        pytest.param("halts", id="outer_halts"),
    ],
)
@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("EIP8037")
def test_inner_create_succeeds_code_deposit_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    outer_outcome: str,
) -> None:
    """
    Verify state gas accumulation and top-level failure handling in a
    creation tx whose initcode runs a successful inner CREATE.

    Under EIP-2780 the outer (tx-level) created account's ``NEW_ACCOUNT``
    is charged at the top frame from ``gas_left`` (not the intrinsic), so
    ``gas_limit`` must cover it on top of the inner CREATE's own state
    gas. On success the block state gas is the outer ``NEW_ACCOUNT`` plus
    the inner account creation and code deposit.
    """
    outer_state_gas = fork.create_state_gas(code_size=0)

    deploy_code = Op.STOP
    inner_initcode = Op.MSTORE(
        0,
        int.from_bytes(bytes(deploy_code), "big") << 248,
    ) + Op.RETURN(31, 1, code_deposit_size=len(deploy_code))
    inner_bytes = bytes(inner_initcode)
    inner_code_deposit = inner_initcode.state_cost(fork)

    setup = Op.MSTORE(
        0,
        int.from_bytes(inner_bytes, "big") << (256 - 8 * len(inner_bytes)),
    )
    if create_opcode == Op.CREATE2:
        inner_create = Op.POP(Op.CREATE2(0, 0, len(inner_bytes), 0))
    else:
        inner_create = Op.POP(Op.CREATE(0, 0, len(inner_bytes)))
    # Inner account creation plus the inner contract's code deposit.
    inner_state_gas = inner_create.state_cost(fork) + inner_code_deposit

    if outer_outcome == "succeeds":
        termination = Op.RETURN(0, 0)
    elif outer_outcome == "reverts":
        termination = Op.REVERT(0, 0)
    else:
        termination = Op.INVALID

    initcode = setup + inner_create + termination

    sender = pre.fund_eoa()
    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    intrinsic_total = intrinsic_calc(
        calldata=bytes(initcode), contract_creation=True
    )

    if outer_outcome == "halts":
        initcode_gas = initcode.execution_cost(fork)
    else:
        initcode_gas = initcode.gas_cost(fork)
    # The outer created account's NEW_ACCOUNT is a top-frame state charge
    # under EIP-2780; gas_limit must cover it alongside the initcode and
    # the inner code deposit.
    gas_limit = (
        intrinsic_total
        + outer_state_gas
        + initcode_gas
        + inner_code_deposit
        + 1000
    )

    create_address = compute_create_address(address=sender, nonce=0)

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=gas_limit,
    )

    if outer_outcome == "succeeds":
        post: dict = {create_address: Account(code=b"")}
        block = Block(
            txs=[tx],
            header_verify=Header(gas_used=outer_state_gas + inner_state_gas),
        )
    else:
        post = {create_address: Account.NONEXISTENT}
        block = Block(txs=[tx])

    blockchain_test(pre=pre, blocks=[block], post=post)


@pytest.mark.parametrize(
    "parent_reverts",
    [
        pytest.param(True, id="parent_reverts"),
        pytest.param(False, id="parent_succeeds"),
    ],
)
@pytest.mark.parametrize(
    "child_failure",
    [
        pytest.param("revert", id="child_revert"),
        pytest.param("halt", id="child_halt"),
    ],
)
@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("EIP8037")
def test_nested_create_failure_refunds_state_gas_before_parent_exit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    parent_reverts: bool,
    child_failure: str,
    create_opcode: Op,
) -> None:
    """
    Verify failed inner CREATE state gas is refunded before its parent exits.

    The child fails by REVERT or exceptional halt, and the factory then either
    returns or reverts. In every case the failed creation leaves no state gas
    charged, so the exact receipt and header contain execution gas only. The
    factory nonce additionally proves that a parent revert rolls back the
    failed CREATE's nonce bump while a successful parent preserves it.
    """
    if child_failure == "revert":
        init_code = Op.REVERT(0, 0)
    else:
        init_code = Op.INVALID

    setup = Op.MSTORE(
        0,
        int.from_bytes(bytes(init_code), "big") << (256 - 8 * len(init_code)),
        new_memory_size=32,
    )

    create_call = (
        create_opcode(
            value=0,
            offset=0,
            size=len(init_code),
            salt=0,
            # gas accounting
            init_code_size=len(init_code),
        )
        if create_opcode == Op.CREATE2
        else create_opcode(
            value=0,
            offset=0,
            size=len(init_code),
            # gas accounting
            init_code_size=len(init_code),
        )
    )
    create_state_gas = create_call.state_cost(fork)

    factory_before_child = setup + create_call
    factory_after_child = Op.REVERT(0, 0) if parent_reverts else Op.STOP
    factory_code = factory_before_child + factory_after_child
    factory = pre.deploy_contract(code=factory_code)

    # Nested CALL required so the child-error path has a parent
    # frame to receive the restored state gas.
    factory_gas = 500_000
    caller_code = Op.POP(Op.CALL(gas=factory_gas, address=factory))
    caller = pre.deploy_contract(code=caller_code)

    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()()
    if child_failure == "revert":
        expected_execution = (
            intrinsic_execution
            + caller_code.execution_cost(fork)
            + factory_code.execution_cost(fork)
            + init_code.execution_cost(fork)
        )
    else:
        gas_before_child = factory_gas - factory_before_child.execution_cost(
            fork
        )
        child_gas = gas_before_child - gas_before_child // 64
        expected_execution = (
            intrinsic_execution
            + caller_code.execution_cost(fork)
            + factory_before_child.execution_cost(fork)
            + child_gas
            + factory_after_child.execution_cost(fork)
        )

    tx = Transaction(
        to=caller,
        state_gas_reservoir=create_state_gas,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            status=1,
            cumulative_gas_used=expected_execution,
        ),
    )

    inner_address = compute_create_address(
        address=factory,
        nonce=1,
        salt=0,
        initcode=bytes(init_code),
        opcode=create_opcode,
    )

    if parent_reverts:
        post = {
            factory: Account(nonce=1),
            inner_address: Account.NONEXISTENT,
        }
    else:
        post = {
            factory: Account(nonce=2),
            inner_address: Account.NONEXISTENT,
        }

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=expected_execution),
            )
        ],
        post=post,
    )


@pytest.mark.valid_from("EIP8037")
def test_create_stack_depth_state_gas_consumed(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify the state gas reservoir survives a deep recursion of
    nested CALLs that silently fail on gas or depth exhaustion.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    storage = Storage()
    recursive = pre.deploy_contract(
        code=(
            Op.POP(Op.CALL(Op.GAS, Op.ADDRESS, 0, 0, 0, 0, 0))
            + Op.SSTORE(storage.store_next(1, "reservoir_ok"), 1)
        ),
    )

    tx = Transaction(
        to=recursive,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {recursive: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "num_inner_ops",
    [
        pytest.param(1, id="single"),
        pytest.param(3, id="accumulate"),
    ],
)
@pytest.mark.parametrize(
    "outer_outcome",
    [
        pytest.param("succeeds", id="outer_succeeds"),
        pytest.param("reverts", id="outer_reverts"),
    ],
)
@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("EIP8037")
def test_inner_create_fail_refunds_in_creation_tx(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    outer_outcome: str,
    num_inner_ops: int,
) -> None:
    """
    Verify failed inner CREATEs inside a creation tx refund state
    gas so only the outer intrinsic state gas remains.
    """
    outer_state_gas = fork.create_state_gas(code_size=0)

    inner_initcode = bytes(Op.REVERT(0, 0))

    setup = Op.MSTORE(
        0,
        int.from_bytes(inner_initcode, "big")
        << (256 - 8 * len(inner_initcode)),
    )

    inner_ops = Bytecode()
    for i in range(num_inner_ops):
        if create_opcode == Op.CREATE2:
            inner_ops += Op.POP(Op.CREATE2(0, 0, len(inner_initcode), i))
        else:
            inner_ops += Op.POP(Op.CREATE(0, 0, len(inner_initcode)))

    if outer_outcome == "succeeds":
        termination = Op.RETURN(0, 0)
    else:
        termination = Op.REVERT(0, 0)

    initcode = setup + inner_ops + termination

    sender = pre.fund_eoa()
    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    intrinsic_total = intrinsic_calc(
        calldata=bytes(initcode), contract_creation=True
    )

    initcode_gas = initcode.gas_cost(fork)
    per_inner_slack = 2_000
    new_account = create_opcode(account_new=True).state_cost(fork)
    gas_limit = (
        intrinsic_total
        + initcode_gas
        + num_inner_ops * (new_account + per_inner_slack)
    )

    create_address = compute_create_address(address=sender, nonce=0)

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=gas_limit,
    )

    if outer_outcome == "succeeds":
        post: dict = {create_address: Account(code=b"")}
        block = Block(
            txs=[tx],
            header_verify=Header(gas_used=outer_state_gas),
        )
    else:
        post = {create_address: Account.NONEXISTENT}
        block = Block(txs=[tx])

    blockchain_test(pre=pre, blocks=[block], post=post)


@pytest.mark.pre_alloc_mutable
@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("EIP8037")
def test_create_collision_burned_gas_counted_in_block_execution(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Verify gas burned by a CREATE/CREATE2 address collision counts
    toward block execution gas used in the header.
    """
    init_code = Op.STOP
    mstore_value, size = init_code_at_high_bytes(init_code)
    factory_create_code = Op.MSTORE(
        0, mstore_value, new_memory_size=32
    ) + create_opcode(value=0, offset=0, size=size, account_new=False)
    factory_post_create_code = Op.POP + Op.STOP
    factory_code = factory_create_code + factory_post_create_code
    factory = pre.deploy_contract(code=factory_code)

    collision_target = compute_create_address(
        address=factory,
        nonce=1,
        salt=0,
        initcode=bytes(init_code),
        opcode=create_opcode,
    )
    pre.deploy_contract(code=Op.STOP, address=collision_target)

    # CPSB-agnostic baseline: block_state_gas is zero for this tx (the
    # existent collision target is not charged), so header.gas_used
    # equals the execution-gas total. Decompose the parent + inner frame
    # accounting from fork APIs so the baseline tracks future cost
    # changes automatically.
    gas_used_until_collision = (
        fork.transaction_intrinsic_cost_calculator()()
        + factory_create_code.gas_cost(fork)
    )
    # Fixed-size budget so the forwarded create_message_gas is
    # deterministic and the baseline below is reproducible.
    gas_limit = gas_used_until_collision * 2
    # Remaining gas can be derived due to the fixed gas limit
    gas_at_create = gas_limit - gas_used_until_collision
    # Inner burns 63/64 of the available gas on collision; the parent
    # retains 1/64. Post-CREATE consumes from the retained pool. A
    # mutation that drops the burned forwarded gas from execution
    # accounting would reduce this baseline.
    retained = gas_at_create // 64
    gas_post_create = factory_post_create_code.gas_cost(fork)
    assert retained >= gas_post_create
    baseline_gas_used = gas_limit - retained + gas_post_create

    tx = Transaction(
        to=factory,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=baseline_gas_used),
            ),
        ],
        post={},
    )


@pytest.mark.parametrize(
    "account_new",
    [
        pytest.param(True, id="new_account"),
        pytest.param(False, id="existing_account"),
    ],
)
@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("EIP8037")
def test_create_account_creation_charge(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    account_new: bool,
) -> None:
    """
    Verify NEW_ACCOUNT is charged only when the created account does not
    already exist in the trie.

    Empty init code means zero code deposit, so NEW_ACCOUNT is the only
    create state cost. A fresh target is charged it; a pre-existing
    balance-only target (balance, no code, zero nonce) is not. The probe
    SSTORE both confirms the create succeeded and makes state gas dominate
    the header, so gas_used differs by exactly NEW_ACCOUNT between the two
    cases.
    """
    mstore_value, size = init_code_at_high_bytes(Op.STOP)
    create_call = create_opcode(
        value=0, offset=0, size=size, account_new=account_new
    )
    storage = Storage()
    factory_code = Op.MSTORE(0, mstore_value) + Op.SSTORE(
        storage.store_next(1, "create_succeeds"), Op.GT(create_call, 0)
    )
    factory = pre.deploy_contract(code=factory_code)

    # Factory deployed via deploy_contract starts at nonce 1.
    create_address = compute_create_address(
        address=factory,
        nonce=1,
        salt=0,
        initcode=bytes(Op.STOP),
        opcode=create_opcode,
    )
    if not account_new:
        pre.fund_address(create_address, amount=1)

    # State gas dominates the header, so gas_used equals the factory's
    # state cost: NEW_ACCOUNT plus the probe SSTORE for a fresh target,
    # just the SSTORE for a pre-existing one.
    state_cost = factory_code.state_cost(fork)
    tx = Transaction(
        to=factory,
        state_gas_reservoir=state_cost,
        sender=pre.fund_eoa(),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={factory: Account(storage=storage)},
        blockchain_test_header_verify=Header(gas_used=state_cost),
    )


@pytest.mark.with_all_create_opcodes()
@pytest.mark.parametrize(
    "sufficient_gas",
    [
        pytest.param(True, id="sufficient_gas"),
        pytest.param(False, id="insufficient_gas"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_no_account_charge_on_existing_account(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    sufficient_gas: bool,
) -> None:
    """
    Verify the create opcode is not charged NEW_ACCOUNT when the target
    account already exists in the trie.

    The factory is forwarded exactly the create's execution gas, with no
    NEW_ACCOUNT included. Because the target is pre-funded (alive), that
    budget is sufficient and the create succeeds, deploying empty code
    (created nonce 1). With one gas less it runs out of gas at the
    create's upfront charge, before the nonce bump, leaving the target
    untouched (nonce 0). The empty reservoir keeps the state-gas
    dimension from masking the boundary.
    """
    factory_code = create_opcode(
        value=0,
        offset=0,
        size=1,  # Nothing in memory, equivalent to Op.STOP
        # Gas accounting
        init_code_size=1,
        new_memory_size=1,
        account_new=False,
    )

    factory = pre.deploy_contract(code=factory_code)

    created = compute_create_address(
        address=factory,
        nonce=1,
        salt=0,
        initcode=Op.STOP,
        opcode=create_opcode,
    )
    pre.fund_address(created, amount=1)

    call_gas = factory_code.gas_cost(fork)
    if not sufficient_gas:
        call_gas -= 1
    entry_code = Op.CALL(gas=call_gas, address=factory)
    entry = pre.deploy_contract(code=entry_code)

    tx = Transaction(
        to=entry,
        state_gas_reservoir=0,  # To allow subcall to run OOG
        sender=pre.fund_eoa(),
    )

    post = {
        created: Account(
            nonce=1 if sufficient_gas else 0, balance=1, code=b""
        ),
    }
    state_test(pre=pre, post=post, tx=tx)
