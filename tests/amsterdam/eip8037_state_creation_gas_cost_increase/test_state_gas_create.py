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
) -> None:
    """
    Test CREATE charges state gas for new account and code deposit.

    A successful CREATE charges new-account state gas plus code
    deposit state gas proportional to the deployed code size.
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
                storage.store_next(True),
                Op.GT(Op.CREATE(0, 0, len(init_code)), 0),
            )
        ),
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
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
@pytest.mark.valid_from("EIP8037")
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
    create_state_gas = gas_costs.NEW_ACCOUNT

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
        state_gas_reservoir=create_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_create2_child_spill_not_double_charged(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test CREATE2 child state gas paid from `gas_left` is not recharged.

    The factory executes below the Amsterdam tx gas cap, so the CREATE2 child
    pays new-account and storage state gas by spilling from `gas_left`. The
    factory must not charge the same state growth again at frame end.
    """
    init_code = sum(Op.SSTORE(i, i + 1) for i in range(6)) + Op.STOP
    mstore_value, initcode_size = init_code_at_high_bytes(init_code)

    factory = pre.deploy_contract(
        code=(
            Op.MSTORE(0, mstore_value)
            + Op.POP(
                Op.CREATE2(
                    value=0,
                    offset=0,
                    size=initcode_size,
                    salt=0,
                )
            )
        )
    )
    created = compute_create2_address(
        address=factory,
        salt=0,
        initcode=bytes(init_code),
    )

    tx = Transaction(
        to=factory,
        gas_limit=1_000_000,
        sender=pre.fund_eoa(),
    )

    post = {
        created: Account(nonce=1, storage={i: i + 1 for i in range(6)}),
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

    # State gas: new account + code deposit
    total_state_gas = fork.create_state_gas(code_size=code_size)

    # Build init code that returns `code_size` bytes of 0x00
    # PUSH2 code_size, PUSH1 0, RETURN
    init_code = Op.RETURN(0, code_size)

    sender = pre.fund_eoa()
    tx = Transaction(
        to=None,
        data=init_code,
        state_gas_reservoir=total_state_gas,
        sender=sender,
    )

    if code_size > fork.max_code_size():
        create_address = compute_create_address(address=sender, nonce=0)
        post = {create_address: Account.NONEXISTENT}
    else:
        post = {}

    state_test(pre=pre, post=post, tx=tx)


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
    (halts: state restored, NEW_ACCOUNT refilled, no code). The two
    regimes pin the halt billing: over-cap ``reservoir`` rolls the
    reservoir back so the sender pays the cap; in-cap ``spill`` burns
    ``gas_left`` and bills ``gas_limit - NEW_ACCOUNT``. The scaling
    tests assert success only.
    """
    gas_costs = fork.gas_costs()
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None

    code_size = fork.max_code_size() if funding == "reservoir" else 1000

    words = (code_size + 31) // 32
    memory_gas = gas_costs.MEMORY_PER_WORD * words + words * words // 512
    init_code = Op.RETURN(0, code_size)
    init_exec_regular = init_code.regular_cost(fork) + memory_gas
    keccak_gas = gas_costs.OPCODE_KECCAK256_PER_WORD * words
    deposit_state_gas = fork.code_deposit_state_gas(code_size=code_size)

    intrinsic_total = fork.transaction_intrinsic_cost_calculator()(
        calldata=bytes(init_code),
        contract_creation=True,
        return_cost_deducted_prior_execution=True,
    )
    exact_fit_gas = (
        intrinsic_total + init_exec_regular + keccak_gas + deposit_state_gas
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
        receipt_gas_used = (
            cap
            if funding == "reservoir"
            else gas_limit - gas_costs.NEW_ACCOUNT
        )
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
) -> None:
    """
    Test contract creation transaction charges intrinsic state gas.

    A create transaction (to=None) charges new-account state gas
    as intrinsic state gas for the new account, plus code deposit state
    gas for the deployed bytecode.
    """
    tx = Transaction(
        to=None,
        data=Op.STOP,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_create_revert_no_code_deposit_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test reverted CREATE does not charge code deposit state gas.

    When CREATE fails during init code execution (REVERT), the new
    account state gas is consumed but no code deposit state gas is
    charged because no code was deployed.
    """
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
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.valid_from("EIP8037")
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
    regular_create_gas = gas_costs.OPCODE_CREATE_BASE
    gas_limit = intrinsic_cost() + regular_create_gas + 10_000

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
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
@pytest.mark.valid_from("EIP8037")
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


@pytest.mark.exception_test
@pytest.mark.parametrize(
    "extra_gas",
    [
        pytest.param(0, id="at_regular_intrinsic"),
        pytest.param(1, id="one_above_regular_intrinsic"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_create_tx_below_total_intrinsic(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    extra_gas: int,
) -> None:
    """
    Reject CREATE tx when gas_limit covers regular but not state intrinsic.

    EIP-8037 splits the CREATE intrinsic into regular and state
    components (`STATE_BYTES_PER_NEW_ACCOUNT * COST_PER_STATE_BYTE`).
    `test_create_tx_intrinsic_gas_boundary` pins the upper boundary
    (`total - 1`); this pins the lower end — `intrinsic_regular` and
    one gas above — to catch implementations that omit the state
    component from the pre-validate check.
    """
    total_intrinsic = fork.transaction_intrinsic_cost_calculator()(
        contract_creation=True,
    )
    intrinsic_state = fork.transaction_intrinsic_state_gas(
        contract_creation=True,
    )
    intrinsic_regular = total_intrinsic - intrinsic_state
    gas_limit = intrinsic_regular + extra_gas
    assert gas_limit < total_intrinsic

    tx = Transaction(
        to=None,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )

    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.valid_from("EIP8037")
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
    gas_costs = fork.gas_costs()
    new_account_state_gas = gas_costs.NEW_ACCOUNT
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

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
        state_gas_reservoir=new_account_state_gas + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {factory: Account(storage=factory_storage)}
    state_test(pre=pre, post=post, tx=tx)


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
    gas_costs = fork.gas_costs()
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    new_account_state_gas = gas_costs.NEW_ACCOUNT

    initcode = Op.SSTORE(0, 1, original_value=0, new_value=1) + failure_op

    factory_storage = Storage()
    factory_code = (
        Op.MSTORE(0, Op.PUSH32(bytes(initcode)))
        + Op.SSTORE(
            factory_storage.store_next(0, "create_fails"),
            Op.CREATE(
                value=0,
                offset=32 - len(initcode),
                size=len(initcode),
            ),
            original_value=0,
            new_value=0,
        )
        + Op.SSTORE(
            factory_storage.store_next(1, "post_create"),
            1,
            original_value=0,
            new_value=1,
        )
    )
    factory = pre.deploy_contract(code=factory_code)

    gas_limit = (
        gas_limit_cap + new_account_state_gas + sstore_state_gas * 2
        if with_reservoir
        else 5_000_000
    )

    # `bytecode.gas_cost(fork)` accounts for opcode base costs and
    # state-gas charges, but does NOT track memory-expansion or CREATE
    # init-code word costs. Add those back to recover runtime regular
    # gas consumption.
    init_code_word_count = (len(initcode) + 31) // 32
    init_code_word_cost = gas_costs.CODE_INIT_PER_WORD * init_code_word_count
    mstore_memory_expansion = gas_costs.MEMORY_PER_WORD  # 1 word
    gas_cost_helper_extras = init_code_word_cost + mstore_memory_expansion

    # Factory bytecode shape costs, derived from fork.gas_costs():
    #   pre-CREATE: PUSH32 + PUSH1 + MSTORE (with 1-word expansion)
    #               + 3 PUSHes for CREATE inputs
    #   post-CREATE: PUSH key + SSTORE (no-op) + 2 PUSHes + SSTORE
    #                (zero-to-nonzero regular)
    factory_pre_create_regular = (
        gas_costs.VERY_LOW * 2
        + gas_costs.OPCODE_MSTORE_BASE
        + mstore_memory_expansion
        + gas_costs.VERY_LOW * 3
    )
    factory_post_create_regular = (
        gas_costs.VERY_LOW
        + gas_costs.COLD_STORAGE_ACCESS
        + gas_costs.WARM_ACCESS
        + gas_costs.VERY_LOW * 2
        + gas_costs.COLD_STORAGE_WRITE
    )

    factory_regular = (
        factory_code.gas_cost(fork)
        - new_account_state_gas
        - sstore_state_gas
        + gas_cost_helper_extras
    )
    initcode_regular_revert = initcode.gas_cost(fork) - sstore_state_gas

    if failure_op == Op.INVALID:
        # Simulate runtime gas for HALT under EIP-8037 LIFO refills:
        #  1. Regular pool capped by transaction_gas_limit_cap. The
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
        regular_budget = gas_limit_cap - intrinsic_cost
        sim_gas_left = min(regular_budget, execution_gas)
        sim_state_gas_left = execution_gas - sim_gas_left

        sim_gas_left -= factory_pre_create_regular
        sim_gas_left -= gas_costs.OPCODE_CREATE_BASE + init_code_word_cost

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

        sim_gas_left -= factory_post_create_regular

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
            + factory_regular
            + initcode_regular_revert
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


@pytest.mark.valid_from("EIP8037")
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
    code_deposit_state = fork.code_deposit_state_gas(code_size=1)

    factory_mstore = Op.MSTORE(
        0, Op.PUSH32(bytes(init_code)), new_memory_size=32
    )
    factory_create = Op.CREATE(
        value=0,
        offset=32 - len(init_code),
        size=len(init_code),
        init_code_size=len(init_code),
    )
    factory = pre.deploy_contract(
        code=factory_mstore + Op.POP(factory_create),
    )
    created = compute_create_address(address=factory, nonce=1)

    # Init code child execution: PUSH1 + PUSH1 + RETURN's mem_exp.
    # Code deposit (keccak + state) is charged AFTER the child returns.
    init_cost = 2 * gas_costs.VERY_LOW + gas_costs.MEMORY_PER_WORD
    # Target child: enough for init, not enough for code deposit state.
    target_child = (init_cost + code_deposit_state) // 2
    # Invert EIP-150 63/64ths rule: ceil(target_child * 64 / 63).
    factory_remaining = (target_child * 64 + 62) // 63

    # NEW_ACCOUNT state gas spills into gas_left (no reservoir at the
    # top level), so it must be funded out of the regular budget.
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    gas_limit = (
        intrinsic_cost
        + factory_mstore.regular_cost(fork)
        + factory_create.regular_cost(fork)
        + gas_costs.NEW_ACCOUNT
        + factory_remaining
    )

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
@pytest.mark.valid_from("EIP8037")
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
    tx = Transaction(
        sender=sender,
        to=caller,
        data=bytes(initcode),
        state_gas_reservoir=0,
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
    factory_state_gas = fork.create_state_gas(
        code_size=len(initcode.deploy_code)
    ) + Op.SSTORE(new_value=1).state_cost(fork)
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

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        state_gas_reservoir=create_state_gas,
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
@pytest.mark.valid_from("EIP8037")
def test_code_deposit_halt_discards_initcode_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
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
    subcall_forwarded_value = 1
    entry_account_value = 1
    if state_opcode == Op.CALL:
        state_op = Op.POP(
            Op.CALL(
                address=pre.nonexistent_account(),
                value=subcall_forwarded_value,
            )
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
                        value=entry_account_value + subcall_forwarded_value,
                        state_gas_reservoir=0,
                        sender=pre.fund_eoa(),
                    ),
                ],
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

    For a fresh target the NEW_ACCOUNT state gas is charged and
    dominates the regular gas, so gas_used == NEW_ACCOUNT. For a
    pre-existing balance-only leaf the NEW_ACCOUNT charge is refunded,
    so net state gas is zero and the regular intrinsic gas dominates.
    The expected value subtracts NEW_ACCOUNT and so fails if the
    refund regresses.
    """
    gas_costs = fork.gas_costs()
    initcode = Op.STOP
    create_state_gas = fork.create_state_gas(code_size=1)

    if target == "existing":
        sender = pre.fund_eoa(nonce=0)
        contract_address = compute_create_address(address=sender, nonce=0)
        # Balance-only leaf: alive and deployable, so the creation
        # succeeds and the intrinsic NEW_ACCOUNT charge is refunded.
        pre.fund_address(contract_address, amount=1)
    else:
        sender = pre.fund_eoa()

    tx = Transaction(
        to=None,
        data=initcode,
        state_gas_reservoir=create_state_gas,
        sender=sender,
    )

    # block_gas_used = max(block_regular, block_state)
    if target == "existing":
        intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
        intrinsic_total = intrinsic_cost(
            calldata=bytes(initcode), contract_creation=True
        )
        expected_gas_used = intrinsic_total - gas_costs.NEW_ACCOUNT
    else:
        # For a minimal CREATE tx deploying Op.STOP (1 byte),
        # state gas (new account) dominates regular gas.
        expected_gas_used = gas_costs.NEW_ACCOUNT

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
    Verify initcode exceptional halt excludes code deposit state gas.

    A CREATE tx runs initcode that hits INVALID (exceptional halt)
    before returning any code. Code deposit never happens, so code
    deposit state gas must NOT be charged. Only the intrinsic state
    gas (new account creation) should count.

    Complements test_create_revert_no_code_deposit_state_gas which
    covers the REVERT path.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    # Initcode that immediately halts, no code returned
    initcode = Op.INVALID

    # State gas = new account only (no code deposit on halt)
    intrinsic_state_gas = fork.create_state_gas(code_size=0)

    gas_limit = gas_limit_cap + intrinsic_state_gas

    tx = Transaction(
        to=None,
        data=initcode,
        state_gas_reservoir=intrinsic_state_gas,
        sender=pre.fund_eoa(),
    )

    # On exceptional halt all gas_left is consumed.
    # block_gas_used = max(block_regular, block_state)
    # block_state = intrinsic_state_gas (new account only, no deposit)
    # block_regular = gas_limit - intrinsic_state_gas (all remaining)
    tx_regular = gas_limit - intrinsic_state_gas
    tx_state = intrinsic_state_gas
    expected_gas_used = max(tx_regular, tx_state)

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
    evm_regular = sstore_code.regular_cost(fork)

    # Reservoir = half the SSTORE state gas, rest spills to gas_left
    reservoir = sstore_state_gas // 2

    tx = Transaction(
        to=contract,
        state_gas_reservoir=reservoir,
        sender=pre.fund_eoa(),
    )

    tx_regular = intrinsic_gas + evm_regular
    tx_state = sstore_state_gas
    expected_gas_used = max(tx_regular, tx_state)

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
    create_state_gas = fork.create_state_gas(code_size=0)

    if failure_mode == "revert":
        init_code = Op.REVERT(0, 0)
    else:
        init_code = Op.INVALID

    create_call = (
        create_opcode(value=0, offset=0, size=len(init_code), salt=0)
        if create_opcode == Op.CREATE2
        else create_opcode(value=0, offset=0, size=len(init_code))
    )

    storage = Storage()
    factory_code = Op.MSTORE(
        0,
        int.from_bytes(bytes(init_code), "big") << (256 - 8 * len(init_code)),
    ) + Op.SSTORE(
        storage.store_next(0, "create_fails"),
        create_call,
    )

    factory = pre.deploy_contract(factory_code)

    tx = Transaction(
        to=factory,
        state_gas_reservoir=create_state_gas,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[tx]),
        ],
        post={factory: Account(storage=storage)},
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
    gas_costs = fork.gas_costs()
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
    # tx_state.
    tx_regular = (
        intrinsic_cost
        + factory_code.gas_cost(fork)
        - gas_costs.NEW_ACCOUNT
        - sstore_state_gas
    )
    tx_state = sstore_state_gas
    expected = max(tx_regular, tx_state)
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
    and the refund returns to the reservoir (not back to `gas_left`).
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    gas_costs = fork.gas_costs()
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()

    init_code = Op.REVERT(0, 0)
    mstore_value, size = init_code_at_high_bytes(init_code)

    create_call = (
        create_opcode(value=0, offset=0, size=size, salt=0)
        if create_opcode == Op.CREATE2
        else create_opcode(value=0, offset=0, size=size)
    )

    storage = Storage()
    factory_code = (
        Op.MSTORE(0, mstore_value)
        + Op.POP(create_call)
        + Op.SSTORE(storage.store_next(1, "reservoir_ok"), 1)
    )
    factory = pre.deploy_contract(code=factory_code)

    gas_limit = (
        gas_limit_cap
        if gas_limit_mode == "spillover"
        else gas_limit_cap + sstore_state_gas
    )
    tx = Transaction(
        to=factory,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    # CREATE's GAS_NEW_ACCOUNT is refunded on child REVERT. SSTORE's
    # state portion is tracked separately. Child REVERT regular
    # (init_code execution) is propagated via
    # incorporate_child_on_error.
    tx_regular = (
        intrinsic_cost
        + factory_code.gas_cost(fork)
        - gas_costs.NEW_ACCOUNT
        - sstore_state_gas
        + init_code.gas_cost(fork)
    )
    tx_state = sstore_state_gas
    expected = max(tx_regular, tx_state)
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
    consume all forwarded gas as `regular_gas_used`, so block
    accounting cannot strictly discriminate via header gas. Tight
    gas tuning via a caller wrapper leaves the factory with just
    enough `gas_left` to pay the probe SSTORE's regular portion
    but not enough to spill the state portion, so the probe SSTORE
    can only succeed via the refunded reservoir.
    """
    gas_costs = fork.gas_costs()
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    new_account_state_gas = gas_costs.NEW_ACCOUNT

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

    # Tight gas tuning: child halt consumes all forwarded gas as
    # regular_gas_used. Factory retains
    # ~(forwarded - pre_sstore_regular) / 64 after CREATE. Target
    # the discrimination window `(probe_regular,
    # probe_regular + sstore_state_gas)` so the probe SSTORE
    # regular fits but state gas spillover from `gas_left` under
    # the old behavior OOGs.
    pre_sstore_code = Op.MSTORE(0, mstore_value) + Op.POP(create_call)
    pre_sstore_regular = pre_sstore_code.gas_cost(fork) - new_account_state_gas
    probe_code = Op.SSTORE(0, 1)
    probe_regular = probe_code.gas_cost(fork) - sstore_state_gas
    target_gas_left = probe_regular + sstore_state_gas // 2
    forwarded_gas = target_gas_left * 64 + pre_sstore_regular
    # Reservoir sized for CREATE charge only — SSTORE must pull
    # from the refunded reservoir, not from spill.
    caller = pre.deploy_contract(
        code=Op.CALL(gas=forwarded_gas, address=factory)
    )
    tx = Transaction(
        to=caller,
        state_gas_reservoir=new_account_state_gas,
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
    tx_regular = (
        intrinsic_gas
        + factory_code.gas_cost(fork)
        - 2 * create_account_state_gas
    )
    expected = max(tx_regular, block_state)

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
    forwarded regular gas (consumed by the never-spawned child), but
    still refunds `GAS_NEW_ACCOUNT` to the reservoir. Tight gas
    tuning limits the factory's post-collision `gas_left` so the
    probe SSTORE can only succeed via the refunded reservoir, not
    by spilling state gas from `gas_left`.
    """
    gas_costs = fork.gas_costs()
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    new_account_state_gas = gas_costs.NEW_ACCOUNT

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
    # ~(forwarded - pre_sstore_regular) / 64 after collision burns
    # `max_message_call_gas` as regular. Target the discrimination
    # window `(probe_regular, probe_regular + sstore_state_gas)` so
    # the probe SSTORE regular fits but state gas spillover from
    # `gas_left` under the old behavior OOGs.
    pre_sstore_code = Op.MSTORE(0, mstore_value) + Op.POP(create_call)
    pre_sstore_regular = pre_sstore_code.gas_cost(fork) - new_account_state_gas
    probe_code = Op.SSTORE(0, 1)
    probe_regular = probe_code.gas_cost(fork) - sstore_state_gas
    target_gas_left = probe_regular + sstore_state_gas // 2
    forwarded_gas = target_gas_left * 64 + pre_sstore_regular
    # Reservoir sized for CREATE charge only — SSTORE must pull from
    # the refunded reservoir, not from spill.
    caller = pre.deploy_contract(
        code=Op.CALL(gas=forwarded_gas, address=factory)
    )
    tx = Transaction(
        to=caller,
        state_gas_reservoir=new_account_state_gas,
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
    gas_costs = fork.gas_costs()
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    new_account_state_gas = gas_costs.NEW_ACCOUNT
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
    # ~(forwarded - pre_sstore_regular) / 64. Target the
    # discrimination window so SSTORE regular fits but state gas
    # spillover fails.
    pre_sstore_code = Op.MSTORE(0, mstore_value) + Op.POP(create_call)
    pre_sstore_regular = pre_sstore_code.gas_cost(fork) - new_account_state_gas
    probe_code = Op.SSTORE(0, 1)
    probe_regular = probe_code.gas_cost(fork) - sstore_state_gas
    target_gas_left = probe_regular + sstore_state_gas // 2
    forwarded_gas = target_gas_left * 64 + pre_sstore_regular
    caller = pre.deploy_contract(
        code=Op.CALL(gas=forwarded_gas, address=factory)
    )
    tx = Transaction(
        to=caller,
        state_gas_reservoir=new_account_state_gas,
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

    Total gas used is independent of `slots`, so a client that drops the
    slot refund diverges for `slots >= 1`; `slots == 0` is the negative
    control.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

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

    storage = Storage()
    factory = pre.deploy_contract(
        code=(
            Op.MSTORE(0, mstore_value)
            + Op.SSTORE(
                storage.store_next(0, "create2_failed"),
                Op.CREATE2(value=0, offset=0, size=size, salt=0),
            )
        ),
    )

    tx = Transaction(
        to=factory,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    state_test(
        pre=pre,
        post={factory: Account(storage=storage)},
        tx=tx,
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
    The target is a pre-existing balance-only leaf, the EIP-8037
    success-refund path that the old conditional charge skipped.
    """
    new_account = fork.gas_costs().NEW_ACCOUNT
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

    # Init code burns `target_burn` regular gas via one MSTORE memory
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

    # Regular gas the factory spends before the NEW_ACCOUNT charge: the
    # initcode setup MSTORE plus the create opcode regular portion
    # (`gas_cost` folds NEW_ACCOUNT into the create op, so strip it).
    setup = Op.MSTORE(0, mstore_value)
    pre_charge_regular = (
        setup.gas_cost(fork) + create_call.gas_cost(fork) - new_account
    )
    forwarded_gas = gas_at_charge + pre_charge_regular
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
    "init_code",
    [
        pytest.param(Op.REVERT(0, 0), id="revert"),
        pytest.param(Op.INVALID, id="halt"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_failed_create_tx_refunds_intrinsic_new_account(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    init_code: Bytecode,
) -> None:
    """
    Verify the NEW_ACCOUNT × CPSB portion of intrinsic_state_gas is
    refunded on creation-tx revert/halt. Block state-gas excludes it
    so header gas_used reflects only the regular component, and the
    sender's receipt reflects the same refund via cumulative_gas_used.
    """
    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    create_state_gas = fork.create_state_gas(code_size=0)

    intrinsic_total = intrinsic_calc(
        calldata=bytes(init_code), contract_creation=True
    )
    intrinsic_regular = intrinsic_total - create_state_gas
    gas_limit = intrinsic_total + 1000

    if init_code == Op.INVALID:
        regular_consumed = gas_limit - intrinsic_total
    else:
        regular_consumed = init_code.regular_cost(fork)

    expected_gas_used = intrinsic_regular + regular_consumed
    expected_cumulative = intrinsic_total + regular_consumed - create_state_gas

    tx = Transaction(
        to=None,
        data=init_code,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative,
        ),
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.pre_alloc_mutable()
@pytest.mark.valid_from("EIP8037")
def test_create_tx_collision_refunds_intrinsic_new_account(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify the NEW_ACCOUNT × CPSB portion of intrinsic_state_gas is
    refunded on creation-tx address collision, so block state-gas
    excludes it and header gas_used reflects only the regular
    consumption (full forwarded gas, no initcode runs).
    """
    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    create_state_gas = fork.create_state_gas(code_size=0)

    init_code = Op.STOP
    intrinsic_total = intrinsic_calc(
        calldata=bytes(init_code), contract_creation=True
    )
    gas_limit = intrinsic_total + 1000

    sender = pre.fund_eoa()
    collision_target = compute_create_address(address=sender, nonce=0)
    pre[collision_target] = Account(nonce=1)

    expected_gas_used = gas_limit - create_state_gas

    tx = Transaction(
        to=None,
        data=init_code,
        gas_limit=gas_limit,
        sender=sender,
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

    EIP-8037 splits `gas_limit` into the capped regular budget and a
    state-gas reservoir. On collision the inner regular gas is burnt
    and `intrinsic_state_gas` is refunded; the reservoir must also
    be refunded to the sender. `header.gas_used` is fixed at the
    regular cap regardless of reservoir handling, so the sender's
    post-balance is the primary discriminating assertion.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    init_code = Op.STOP
    # +1 above intrinsic_state_gas (= create_state_gas(code_size=0)
    # for empty-code CREATE-tx) makes message.state_gas_reservoir > 0.
    reservoir = fork.create_state_gas(code_size=0) + 1
    gas_limit = gas_limit_cap + reservoir
    initial_fund = 10**18

    sender = pre.fund_eoa(initial_fund)
    collision_target = compute_create_address(address=sender, nonce=0)
    pre[collision_target] = Account(nonce=1)

    tx_gas_price = 7
    tx = Transaction(
        to=None,
        data=init_code,
        gas_limit=gas_limit,
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
    initcode = Initcode(deploy_code=Op.STOP, initcode_length=size)
    initcode_bytes = bytes(initcode)

    gas_costs = fork.gas_costs()
    create_state_gas = gas_costs.NEW_ACCOUNT

    create_call = (
        create_opcode(
            value=0,
            offset=0,
            size=Op.CALLDATASIZE,
            salt=0,
            init_code_size=len(initcode_bytes),
        )
        if create_opcode == Op.CREATE2
        else create_opcode(value=0, offset=0, size=Op.CALLDATASIZE)
    )

    factory = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE) + Op.SSTORE(0, create_call)
    )

    create_address = compute_create_address(
        address=factory,
        nonce=1,
        salt=0,
        initcode=initcode,
        opcode=create_opcode,
    )

    storage = Storage()
    storage[0] = create_address if initcode_size_delta == 0 else 0

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=factory,
        data=initcode_bytes,
        state_gas_reservoir=create_state_gas,
    )

    post: dict = {factory: Account(storage=storage)}
    if initcode_size_delta == 0:
        post[create_address] = Account(code=Op.STOP)
    else:
        post[create_address] = Account.NONEXISTENT

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
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
    """
    gas_costs = fork.gas_costs()
    create_state_gas = fork.create_state_gas(code_size=0)

    beneficiary = 0xDEAD
    initcode = Op.SELFDESTRUCT(beneficiary)

    sender = pre.fund_eoa()
    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    intrinsic_total = intrinsic_calc(
        calldata=bytes(initcode), contract_creation=True
    )

    expected_state = create_state_gas + gas_costs.NEW_ACCOUNT

    initcode_gas = initcode.gas_cost(fork)
    gas_limit = intrinsic_total + initcode_gas + gas_costs.NEW_ACCOUNT + 1000

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
    Verify state gas accumulation and top-level failure refund in a
    creation tx whose initcode runs a successful inner CREATE.
    """
    gas_costs = fork.gas_costs()
    outer_state_gas = fork.create_state_gas(code_size=0)
    inner_code_deposit = fork.code_deposit_state_gas(code_size=1)
    inner_state_gas = gas_costs.NEW_ACCOUNT + inner_code_deposit

    deploy_code = Op.STOP
    inner_initcode = Op.MSTORE(
        0,
        int.from_bytes(bytes(deploy_code), "big") << 248,
    ) + Op.RETURN(31, 1)
    inner_bytes = bytes(inner_initcode)

    setup = Op.MSTORE(
        0,
        int.from_bytes(inner_bytes, "big") << (256 - 8 * len(inner_bytes)),
    )
    if create_opcode == Op.CREATE2:
        inner_create = Op.POP(Op.CREATE2(0, 0, len(inner_bytes), 0))
    else:
        inner_create = Op.POP(Op.CREATE(0, 0, len(inner_bytes)))

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
        initcode_gas = initcode.regular_cost(fork)
    else:
        initcode_gas = initcode.gas_cost(fork)
    gas_limit = intrinsic_total + initcode_gas + inner_code_deposit + 1000

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
def test_nested_create_fail_parent_revert_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    parent_reverts: bool,
    child_failure: str,
    create_opcode: Op,
) -> None:
    """
    Verify factory nonce is rolled back when the factory reverts after
    a failed inner CREATE, and preserved when the factory returns.
    """
    gas_costs = fork.gas_costs()
    create_state_gas = gas_costs.NEW_ACCOUNT

    if child_failure == "revert":
        init_code = Op.REVERT(0, 0)
    else:
        init_code = Op.INVALID

    create_call = (
        create_opcode(value=0, offset=0, size=len(init_code), salt=0)
        if create_opcode == Op.CREATE2
        else create_opcode(value=0, offset=0, size=len(init_code))
    )

    factory = pre.deploy_contract(
        code=(
            Op.MSTORE(
                0,
                int.from_bytes(bytes(init_code), "big")
                << (256 - 8 * len(init_code)),
            )
            + Op.POP(create_call)
            + (Op.REVERT(0, 0) if parent_reverts else Op.STOP)
        ),
    )

    # Nested CALL required so the child-error path has a parent
    # frame to receive the restored state gas.
    caller = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=500_000, address=factory)),
    )

    tx = Transaction(
        to=caller,
        state_gas_reservoir=create_state_gas,
        sender=pre.fund_eoa(),
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
        blocks=[Block(txs=[tx])],
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
    gas_costs = fork.gas_costs()
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
    gas_limit = (
        intrinsic_total
        + initcode_gas
        + num_inner_ops * (gas_costs.NEW_ACCOUNT + per_inner_slack)
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
def test_create_collision_burned_gas_counted_in_block_regular(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Verify gas burned by a CREATE/CREATE2 address collision counts
    toward block regular gas used in the header.
    """
    init_code = Op.STOP
    mstore_value, size = init_code_at_high_bytes(init_code)
    salt = 0

    create_call = (
        create_opcode(value=0, offset=0, size=size, salt=salt)
        if create_opcode == Op.CREATE2
        else create_opcode(value=0, offset=0, size=size)
    )
    factory_code = Op.MSTORE(0, mstore_value) + Op.POP(create_call) + Op.STOP
    factory = pre.deploy_contract(code=factory_code)

    collision_target = compute_create_address(
        address=factory,
        nonce=1,
        salt=salt,
        initcode=bytes(init_code),
        opcode=create_opcode,
    )
    pre.deploy_contract(code=Op.STOP, address=collision_target)

    # Fixed-size budget so the forwarded create_message_gas is
    # deterministic and the baseline below is reproducible.
    gas_limit = 250_000

    tx = Transaction(
        to=factory,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    # CPSB-agnostic baseline: block_state_gas is zero for this tx (the
    # collision refunds the NEW_ACCOUNT state charge), so header.gas_used
    # equals the regular-gas total. Decompose the parent + inner frame
    # accounting from fork APIs so the baseline tracks future cost
    # changes automatically.
    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    new_account = fork.gas_costs().NEW_ACCOUNT
    create_base = fork.gas_costs().OPCODE_CREATE_BASE
    # POP + STOP run in the parent frame after CREATE returns; their
    # cost comes out of the 1/64 retained gas.
    post_create_static = (Op.POP + Op.STOP).gas_cost(fork)
    # factory_code.gas_cost(fork) folds NEW_ACCOUNT into the CREATE op
    # (state gas is treated as part of the opcode total). Strip it
    # back out and split off the post-CREATE tail to isolate the
    # pre-CREATE static gas.
    factory_pre_create = (
        factory_code.gas_cost(fork)
        - new_account
        - create_base
        - post_create_static
    )
    # MSTORE writes the initcode at memory[0:32] (one word).
    memory_expansion = fork.memory_expansion_gas_calculator()(new_bytes=32)
    # gas_left at the moment NEW_ACCOUNT spills into the regular pool
    # (reservoir is empty for tx_gas_limit < TX_MAX_GAS_LIMIT).
    gas_at_create_after_state = (
        gas_limit
        - intrinsic
        - factory_pre_create
        - memory_expansion
        - create_base
        - new_account
    )
    # Inner burns 63/64 of the available gas on collision; the parent
    # retains 1/64. The state-spill of NEW_ACCOUNT is refunded back to
    # gas_left on collision (nets zero). Post-CREATE consumes from the
    # retained pool. A mutation that drops the burned forwarded gas
    # from regular accounting would reduce this baseline.
    retained = gas_at_create_after_state // 64
    baseline_gas_used = gas_limit - retained - new_account + post_create_static

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
    "target",
    [
        pytest.param("new", id="new_account"),
        pytest.param("existing", id="existing_account"),
    ],
)
@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("EIP8037")
def test_create_account_creation_charge(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    target: str,
) -> None:
    """
    Verify NEW_ACCOUNT is charged for a new account and refunded for a
    pre-existing balance-only leaf.

    Empty init code means zero code deposit, so NEW_ACCOUNT is the only
    create state cost. A fresh target is charged it; a pre-existing
    balance-only target (balance, no code, zero nonce) refunds it on
    success. The probe SSTORE both confirms the create succeeded and
    makes state gas dominate, so gas_used drops by exactly NEW_ACCOUNT
    when refunded.
    """
    new_account = fork.gas_costs().NEW_ACCOUNT
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    mstore_value, size = init_code_at_high_bytes(Op.STOP)
    create_call = (
        create_opcode(value=0, offset=0, size=size, salt=0)
        if create_opcode == Op.CREATE2
        else create_opcode(value=0, offset=0, size=size)
    )

    storage = Storage()
    factory = pre.deploy_contract(
        code=Op.MSTORE(0, mstore_value)
        + Op.SSTORE(
            storage.store_next(1, "create_succeeds"), Op.GT(create_call, 0)
        )
    )

    # Factory deployed via deploy_contract starts at nonce 1.
    if create_opcode == Op.CREATE2:
        create_address = compute_create2_address(
            address=factory, salt=0, initcode=bytes(Op.STOP)
        )
    else:
        create_address = compute_create_address(address=factory, nonce=1)
    if target == "existing":
        pre.fund_address(create_address, amount=1)

    tx = Transaction(
        to=factory,
        state_gas_reservoir=new_account + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    # State gas dominates regular: a new account adds NEW_ACCOUNT on top
    # of the probe SSTORE, a pre-existing target refunds it.
    expected = sstore_state_gas + (new_account if target == "new" else 0)
    state_test(
        pre=pre,
        tx=tx,
        post={factory: Account(storage=storage)},
        blockchain_test_header_verify=Header(gas_used=expected),
    )
