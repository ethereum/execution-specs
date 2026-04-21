"""
Test cases for the EIP-8037 state gas reservoir and its interaction with the
EIP-7825 TX_MAX_GAS_LIMIT cap.

EIP-8037 splits execution gas into two pools:
- `gas_left` (regular gas): capped at `TX_MAX_GAS_LIMIT - intrinsic.regular`
- `state_gas_reservoir`: the overflow beyond the regular gas cap

State gas charges draw from the reservoir first, then spill into gas_left.
Regular gas charges draw only from gas_left.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    AccessList,
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
    TransactionException,
    TransactionReceipt,
)
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


@pytest.mark.parametrize(
    "gas_limit_delta",
    [
        pytest.param(-1, id="below_cap"),
        pytest.param(0, id="at_cap"),
        pytest.param(1, id="above_cap"),
    ],
)
@EIPChecklist.ModifiedTransactionValidityConstraint.Test()
@pytest.mark.valid_from("EIP8037")
def test_reservoir_allocation_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    gas_limit_delta: int,
    fork: Fork,
) -> None:
    """
    Test state gas reservoir allocation at TX_MAX_GAS_LIMIT boundary.

    When tx.gas <= TX_MAX_GAS_LIMIT, all execution gas fits in gas_left
    and the reservoir is zero. When tx.gas > TX_MAX_GAS_LIMIT, the
    excess goes to the reservoir. In all cases, an SSTORE should
    succeed because state gas can spill from gas_left.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + gas_limit_delta,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "num_sstores,reservoir_covers_state_gas",
    [
        pytest.param(1, True, id="single_sstore_from_reservoir"),
        pytest.param(5, True, id="multiple_sstores_from_reservoir"),
        pytest.param(1, False, id="single_sstore_spill_to_gas_left"),
        pytest.param(5, False, id="multiple_sstores_spill_to_gas_left"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_sstore_state_gas_source(
    state_test: StateTestFiller,
    pre: Alloc,
    num_sstores: int,
    reservoir_covers_state_gas: bool,
    fork: Fork,
) -> None:
    """
    Test SSTORE zero-to-nonzero drawing state gas from different sources.

    When reservoir_covers_state_gas is True, enough gas is provided above
    TX_MAX_GAS_LIMIT to cover all SSTORE state gas from the reservoir.
    When False, the reservoir is minimal (1 gas unit) and state gas must
    spill into gas_left.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    storage = Storage()
    code = Bytecode()
    for _ in range(num_sstores):
        code += Op.SSTORE(storage.store_next(1), 1)
    contract = pre.deploy_contract(code=code)

    if reservoir_covers_state_gas:
        extra_gas = sstore_state_gas * num_sstores
    else:
        extra_gas = 1  # Minimal reservoir, rest spills to gas_left

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + extra_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_sstore_state_gas_entirely_from_gas_left(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SSTORE state gas charged entirely from gas_left (no reservoir).

    When tx.gas <= TX_MAX_GAS_LIMIT, the reservoir is zero. All state
    gas must come from gas_left.
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


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.valid_from("EIP8037")
def test_insufficient_gas_for_sstore_state_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that execution OOGs when gas is insufficient for SSTORE state cost.

    Provide just enough gas for intrinsic costs plus the SSTORE regular
    gas, but not enough to also cover the SSTORE state gas. The SSTORE
    should OOG, leaving storage slot 0 unchanged at zero.
    """
    gas_costs = fork.gas_costs()
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, 1),
    )

    # Enough for intrinsic + warm SSTORE regular gas, but not the
    # state gas cost for zero-to-nonzero transition
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    gas_limit = intrinsic_cost() + gas_costs.GAS_COLD_STORAGE_WRITE

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    # Execution OOGs — storage slot 0 remains at default (zero)
    post = {contract: Account(storage={0: 0})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "exceed_block_gas_limit",
    [
        pytest.param(True, marks=pytest.mark.exception_test),
        pytest.param(False),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_block_regular_gas_limit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    exceed_block_gas_limit: bool,
    fork: Fork,
) -> None:
    """
    Test check_transaction enforcement of regular gas against block limit.

    The regular gas check uses min(TX_MAX_GAS_LIMIT, tx.gas).
    Fill the block with transactions at TX_MAX_GAS_LIMIT and verify
    the last one is accepted or rejected based on remaining capacity.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    tx_count = env.gas_limit // gas_limit_cap

    gas_spender = pre.deploy_contract(code=Op.INVALID)

    total_txs = tx_count + int(exceed_block_gas_limit)
    block = Block(
        txs=[
            Transaction(
                to=gas_spender,
                sender=pre.fund_eoa(),
                gas_limit=gas_limit_cap,
                error=(
                    TransactionException.GAS_ALLOWANCE_EXCEEDED
                    if i >= tx_count
                    else None
                ),
            )
            for i in range(total_txs)
        ],
        exception=(
            TransactionException.GAS_ALLOWANCE_EXCEEDED
            if exceed_block_gas_limit
            else None
        ),
    )

    blockchain_test(pre=pre, post={}, blocks=[block])


@pytest.mark.parametrize(
    "delta",
    [
        pytest.param(0, id="exact_fit"),
        pytest.param(1, id="exceeded", marks=pytest.mark.exception_test),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_block_state_gas_limit_boundary(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    delta: int,
) -> None:
    """
    Verify the per-tx state check at the strict-greater-than boundary.

    tx1 consumes `tx1_state` via cold SSTOREs. tx2 is sized so that
    its worst-case state contribution `tx.gas - intrinsic_regular`
    equals `state_available` (delta=0, accepted because the check is
    strict `>`) or exceeds it by 1 (delta=1, rejected with
    `GAS_ALLOWANCE_EXCEEDED`).

    The regular check is asserted to pass so rejection on delta=1 is
    pinned to the state dimension.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    # TODO(EIP-8037): pin block_gas_limit (and therefore cpsb)
    # up-front; see test_creation_tx_state_check_exceeded for
    # rationale. Revisit if the framework exposes a cpsb query
    # that doesn't require mutating the fork.
    block_gas_limit = 100_000_000
    fork._env_gas_limit = block_gas_limit

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    sstore_state_gas = fork.sstore_state_gas()

    num_sstores = 50
    tx1_code = Bytecode()
    for i in range(num_sstores):
        tx1_code = tx1_code + Op.SSTORE(i, 1)
    tx1_contract = pre.deploy_contract(code=tx1_code)

    tx1_state = num_sstores * sstore_state_gas
    tx1_regular = intrinsic_cost() + tx1_code.gas_cost(fork) - tx1_state
    tx1_gas = gas_limit_cap + tx1_state

    # tx2: worst-case state contribution = state_available + delta.
    # Plain call, so intrinsic_state is zero.
    tx2_intrinsic_regular = intrinsic_cost()
    state_available = block_gas_limit - tx1_state
    tx2_gas = tx2_intrinsic_regular + state_available + delta

    # Pin the rejection (when delta > 0) to the state check: the
    # regular check must not fire.
    regular_available = block_gas_limit - tx1_regular
    assert min(gas_limit_cap, tx2_gas) < regular_available, (
        "tx2 would fail the regular check instead of the state check"
    )

    tx2_error = (
        TransactionException.GAS_ALLOWANCE_EXCEEDED if delta > 0 else None
    )
    block_exception = (
        TransactionException.GAS_ALLOWANCE_EXCEEDED if delta > 0 else None
    )

    tx1 = Transaction(
        to=tx1_contract,
        gas_limit=tx1_gas,
        sender=pre.fund_eoa(),
    )
    tx2 = Transaction(
        to=pre.deploy_contract(code=Op.STOP),
        gas_limit=tx2_gas,
        sender=pre.fund_eoa(),
        error=tx2_error,
    )

    blockchain_test(
        genesis_environment=Environment(gas_limit=block_gas_limit),
        pre=pre,
        blocks=[
            Block(
                txs=[tx1, tx2],
                gas_limit=block_gas_limit,
                exception=block_exception,
            )
        ],
        post={},
    )


@pytest.mark.valid_from("EIP8037")
def test_creation_tx_regular_check_subtracts_intrinsic_state(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify the regular check subtracts `intrinsic.state` from tx.gas.

    The EIP regular check is
    `min(TX_MAX, tx.gas - intrinsic.state) > regular_available`. For a
    creation tx, `intrinsic.state = GAS_NEW_ACCOUNT`. This test sizes a
    creation tx whose raw `tx.gas` exceeds `regular_available` but
    `tx.gas - intrinsic.state` fits; it must be accepted. The old
    formula `min(TX_MAX, tx.gas)` would reject the same tx, proving
    the subtraction is honored.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    # `intrinsic_regular` for a creation tx is cpsb-free
    # (GAS_TX_BASE + REGULAR_GAS_CREATE + init_code_cost), so
    # reading it at the current cpsb and using it to size the block
    # gives a stable `block_gas_limit` independent of cpsb.
    intrinsic_regular = fork.transaction_intrinsic_cost_calculator()(
        contract_creation=True
    ) - fork.transaction_intrinsic_state_gas(contract_creation=True)

    # Tight boundary: after the filler consumes gas_limit_cap, the
    # remaining regular is exactly intrinsic_regular + 1. The old
    # formula `min(TX_MAX, tx.gas)` rejects (tx.gas = intrinsic_total
    # > intrinsic_regular + 1); the new formula `min(TX_MAX, tx.gas
    # - intrinsic.state)` accepts (equals intrinsic_regular).
    block_gas_limit = gas_limit_cap + intrinsic_regular + 1

    # TODO(EIP-8037): pin `_env_gas_limit` to the actual block limit
    # and re-read every cpsb-dependent value. The intrinsic calculator
    # captures `gas_costs()` at creation time, so it must be
    # re-obtained. Revisit if the framework exposes a cpsb query
    # that doesn't require mutating the fork.
    fork._env_gas_limit = block_gas_limit
    intrinsic_state = fork.transaction_intrinsic_state_gas(
        contract_creation=True,
    )
    create_tx_gas = fork.transaction_intrinsic_cost_calculator()(
        contract_creation=True,
    )

    # Filler consumes the full regular cap (OOG on INVALID).
    filler = pre.deploy_contract(code=Op.INVALID)

    remaining_regular = block_gas_limit - gas_limit_cap

    assert create_tx_gas > remaining_regular, (
        "old formula must reject to prove new formula differs"
    )
    assert create_tx_gas - intrinsic_state <= remaining_regular, (
        "new formula must accept"
    )

    filler_tx = Transaction(
        to=filler,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )
    create_tx = Transaction(
        to=None,
        gas_limit=create_tx_gas,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        genesis_environment=Environment(gas_limit=block_gas_limit),
        pre=pre,
        blocks=[
            Block(
                txs=[filler_tx, create_tx],
                gas_limit=block_gas_limit,
            )
        ],
        post={},
    )


@pytest.mark.exception_test
@pytest.mark.valid_from("EIP8037")
def test_single_tx_state_check_exceeds_block_limit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify a single tx is rejected when its state contribution exceeds
    the entire block gas limit.

    No prior txs needed. A tx whose tx.gas - intrinsic_regular exceeds
    block_gas_limit must be rejected at inclusion.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    intrinsic_regular = intrinsic_cost()

    block_gas_limit = gas_limit_cap + 100
    tx_gas = block_gas_limit + intrinsic_regular + 1

    tx = Transaction(
        to=pre.deploy_contract(code=Op.STOP),
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
        error=TransactionException.GAS_ALLOWANCE_EXCEEDED,
    )

    blockchain_test(
        genesis_environment=Environment(gas_limit=block_gas_limit),
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                gas_limit=block_gas_limit,
                exception=TransactionException.GAS_ALLOWANCE_EXCEEDED,
            )
        ],
        post={},
    )


@pytest.mark.exception_test
@pytest.mark.valid_from("EIP8037")
def test_creation_tx_state_check_exceeded(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify a creation tx is rejected by the state check.

    A creation tx has non-zero intrinsic_state (new account) AND
    intrinsic_regular (base + CREATE cost). Both formulas are
    exercised: the regular check subtracts intrinsic_state, the state
    check subtracts intrinsic_regular.

    A filler tx consumes state budget. The creation tx's state
    contribution (tx.gas - intrinsic_regular) exceeds the remaining
    state budget while its regular contribution
    (tx.gas - intrinsic_state) fits the regular budget.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    # TODO(EIP-8037): pin block_gas_limit (and therefore cpsb)
    # up-front so every cpsb-dependent read below is consistent with
    # what the block uses at execution time. 100_000_000 is the
    # canonical value the spec uses (cost_per_state_byte = 1174 at
    # this limit). Revisit if the framework exposes a cpsb query
    # that doesn't require mutating the fork.
    block_gas_limit = 100_000_000
    fork._env_gas_limit = block_gas_limit

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    sstore_state_gas = fork.sstore_state_gas()
    create_intrinsic_total = intrinsic_cost(contract_creation=True)
    create_intrinsic_state = fork.transaction_intrinsic_state_gas(
        contract_creation=True,
    )
    create_intrinsic_regular = create_intrinsic_total - create_intrinsic_state

    num_sstores = 50
    tx1_code = Bytecode()
    for i in range(num_sstores):
        tx1_code = tx1_code + Op.SSTORE(i, 1)
    tx1_contract = pre.deploy_contract(code=tx1_code)

    tx1_state = num_sstores * sstore_state_gas
    tx1_regular = intrinsic_cost() + tx1_code.gas_cost(fork) - tx1_state
    tx1_gas = gas_limit_cap + tx1_state
    state_available = block_gas_limit - tx1_state

    # tx2 state contribution = state_available + 1 → rejected
    tx2_gas = create_intrinsic_regular + state_available + 1

    # Regular check must pass so rejection is pinned to state.
    regular_available = block_gas_limit - tx1_regular
    assert min(gas_limit_cap, tx2_gas - create_intrinsic_state) < (
        regular_available
    )

    tx1 = Transaction(
        to=tx1_contract,
        gas_limit=tx1_gas,
        sender=pre.fund_eoa(),
    )
    tx2 = Transaction(
        to=None,
        gas_limit=tx2_gas,
        sender=pre.fund_eoa(),
        error=TransactionException.GAS_ALLOWANCE_EXCEEDED,
    )

    blockchain_test(
        genesis_environment=Environment(gas_limit=block_gas_limit),
        pre=pre,
        blocks=[
            Block(
                txs=[tx1, tx2],
                gas_limit=block_gas_limit,
                exception=TransactionException.GAS_ALLOWANCE_EXCEEDED,
            )
        ],
        post={},
    )


@pytest.mark.valid_from("EIP8037")
def test_block_gas_used_no_state_ops(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test block gas_used when regular gas dominates (no state operations).

    With no state-creating operations, state gas is 0 and block gas_used
    should equal regular gas used.
    """
    contract = pre.deploy_contract(code=Op.STOP)

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    gas_needed = intrinsic_cost()

    tx = Transaction(
        to=contract,
        gas_limit=gas_needed,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], header_verify=Header(gas_used=gas_needed))],
        post={},
    )


@pytest.mark.valid_from("EIP8037")
def test_block_gas_used_with_state_ops(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test block gas_used includes state gas contribution.

    A transaction performing SSTORE zero-to-nonzero contributes to both
    block_gas_used and block_state_gas_used. The block header gas_used
    is max(block_gas_used, block_state_gas_used).
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

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post={contract: Account(storage=storage)},
    )


@pytest.mark.valid_from("EIP8037")
def test_block_2d_gas_valid_when_cumulative_exceeds_limit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify block validity under 2D gas when sum(txGasUsed) > gas_limit.

    EIP-8037 block validity: max(regular, state) <= gas_limit.
    Receipt cumulative_gas_used sums both dimensions per-tx, so it
    can legitimately exceed gas_limit. Clients must not use the 1D
    cumulative check for block validation.
    """
    # TODO(EIP-8037): pin block_gas_limit (and therefore cpsb)
    # up-front. Choosing a value where cpsb is its canonical 1174
    # keeps `tx_state` comparable to `tx_regular` so the 2D-max vs
    # 1D-sum discrimination the test exercises is meaningful.
    # Revisit if the framework exposes a cpsb query that doesn't
    # require mutating the fork.
    block_gas_limit = 100_000_000
    fork._env_gas_limit = block_gas_limit

    gas_costs = fork.gas_costs()
    sstore_state_gas = fork.sstore_state_gas()

    tx_regular = (
        gas_costs.GAS_TX_BASE
        + 2 * gas_costs.GAS_VERY_LOW
        + gas_costs.GAS_COLD_STORAGE_WRITE
    )
    tx_state = sstore_state_gas
    tx_gas_used = tx_regular + tx_state

    # num_txs sized so `one_d_bound > block_gas_limit > two_d_bound`:
    # per-dimension maxes fit (accepted under 2D-max) but the 1D sum
    # exceeds the limit (would be rejected by a summing client).
    num_txs = block_gas_limit // max(tx_regular, tx_state)
    two_d_bound = num_txs * max(tx_regular, tx_state)
    one_d_bound = num_txs * tx_gas_used
    assert two_d_bound <= block_gas_limit < one_d_bound

    env = Environment(gas_limit=block_gas_limit)
    tx_limit = tx_gas_used + 1000

    txs = []
    post = {}
    for _ in range(num_txs):
        storage = Storage()
        contract = pre.deploy_contract(
            code=Op.SSTORE(storage.store_next(1), 1),
        )
        txs.append(
            Transaction(
                to=contract,
                gas_limit=tx_limit,
                sender=pre.fund_eoa(),
            ),
        )
        post[contract] = Account(storage=storage)

    blockchain_test(
        genesis_environment=env,
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                gas_limit=block_gas_limit,
                header_verify=Header(
                    gas_used=num_txs * max(tx_regular, tx_state),
                ),
            ),
        ],
        post=post,
    )


@pytest.mark.parametrize(
    "gas_above_cap",
    [
        pytest.param(True, id="state_gas_from_reservoir"),
        pytest.param(False, id="state_gas_from_gas_left"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_create_tx_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    gas_above_cap: bool,
    fork: Fork,
) -> None:
    """
    Test contract creation with state gas from reservoir or gas_left.

    Contract creation charges intrinsic state gas for the new account
    (new-account state gas). When gas_above_cap is True, extra gas
    beyond TX_MAX_GAS_LIMIT feeds the reservoir. When False, all state
    gas comes from gas_left (reservoir is zero).
    """
    gas_costs = fork.gas_costs()
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    init_code = Op.STOP

    env = Environment()
    create_state_gas = gas_costs.GAS_NEW_ACCOUNT

    if gas_above_cap:
        gas_limit = gas_limit_cap + create_state_gas
    else:
        gas_limit = gas_limit_cap

    tx = Transaction(
        to=None,
        data=init_code,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


@pytest.mark.parametrize(
    "failure_mode",
    [
        pytest.param("revert", id="revert"),
        pytest.param("halt", id="halt"),
        pytest.param("oog", id="oog"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_top_level_failure_refunds_execution_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    failure_mode: str,
) -> None:
    """
    Verify top level tx failure returns execution state gas to the
    reservoir across revert, exceptional halt, and out of gas paths.

    On top level failure no state was created, so execution state gas
    is credited back to the reservoir and `state_gas_used` is zeroed.
    The billing formula `tx.gas - gas_left - state_gas_left` sees a
    restored reservoir and refunds the sender. Without the refund the
    receipt would bill the consumed state gas despite the failure.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()

    if failure_mode == "revert":
        code = Op.SSTORE(0, 1) + Op.REVERT(0, 0)
    elif failure_mode == "halt":
        code = Op.SSTORE(0, 1) + Op.INVALID
    else:
        # OOG: perform the SSTORE then spin with JUMPDEST loop until
        # gas runs out.
        code = Op.SSTORE(0, 1) + Op.JUMPDEST + Op.JUMP(0x5)
    contract = pre.deploy_contract(code=code)

    tx_gas = gas_limit_cap + sstore_state_gas

    if failure_mode == "revert":
        # REVERT preserves unused gas_left.
        expected_cumulative = (
            intrinsic_cost + code.gas_cost(fork) - sstore_state_gas
        )
    else:
        # Exceptional halt and out of gas zero gas_left.
        expected_cumulative = tx_gas - sstore_state_gas

    tx = Transaction(
        to=contract,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative,
        ),
    )

    state_test(pre=pre, post={contract: Account(storage={})}, tx=tx)


@pytest.mark.parametrize(
    "failure_mode",
    [
        pytest.param("revert", id="revert"),
        pytest.param("halt", id="halt"),
        pytest.param("oog", id="oog"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_top_level_failure_zeros_block_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    failure_mode: str,
) -> None:
    """
    Verify the block header reflects zero execution state gas after a
    top level failure.

    With `state_gas_used` zeroed on failure, `block_state_gas_used`
    excludes any state gas consumed during the failed transaction and
    the block header `gas_used` falls back to the regular gas
    component alone.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()

    if failure_mode == "revert":
        code = Op.SSTORE(0, 1) + Op.REVERT(0, 0)
    elif failure_mode == "halt":
        code = Op.SSTORE(0, 1) + Op.INVALID
    else:
        code = Op.SSTORE(0, 1) + Op.JUMPDEST + Op.JUMP(0x5)
    contract = pre.deploy_contract(code=code)

    tx_gas = gas_limit_cap + sstore_state_gas
    tx = Transaction(
        to=contract,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
    )

    if failure_mode == "revert":
        expected_block_regular = (
            intrinsic_cost + code.gas_cost(fork) - sstore_state_gas
        )
    else:
        # Exceptional halt and out of gas zero gas_left.
        expected_block_regular = tx_gas - sstore_state_gas

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=expected_block_regular),
            ),
        ],
        post={contract: Account(storage={})},
    )


@pytest.mark.valid_from("EIP8037")
def test_creation_tx_failure_preserves_intrinsic_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Regression test for the creation tx failure path.

    A creation tx (to=None) whose initcode halts exercises both the
    intrinsic state gas for the new account and the top level failure
    refund of execution state gas. The test asserts the block header
    `gas_used` equals `max(block_regular, intrinsic_state_gas)`,
    guarding that the failure path does not raise and that block
    accounting does not underflow when the refund is applied.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    create_intrinsic_state = fork.transaction_intrinsic_state_gas(
        contract_creation=True,
    )
    sstore_state_gas = fork.sstore_state_gas()
    tx_gas = gas_limit_cap + create_intrinsic_state + sstore_state_gas

    tx = Transaction(
        to=None,
        data=Op.SSTORE(0, 1) + Op.INVALID,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
    )

    block_regular = tx_gas - create_intrinsic_state - sstore_state_gas
    expected_gas_used = max(block_regular, create_intrinsic_state)

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
def test_subcall_failure_does_not_zero_top_level_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify a subcall failure does not zero the top level execution
    state gas.

    The top level tx succeeds end to end even though a subcall
    reverts, so the top level failure refund does not apply. The
    parent's own SSTORE contributes state gas that appears in
    `block_state_gas_used`.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()

    child = pre.deploy_contract(code=Op.REVERT(0, 0))
    parent_storage = Storage()
    parent = pre.deploy_contract(
        code=(
            Op.POP(Op.CALL(gas=Op.GAS, address=child))
            + Op.SSTORE(parent_storage.store_next(1, "parent_sstore"), 1)
        ),
    )

    tx = Transaction(
        to=parent,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    # Parent's SSTORE state gas dominates tx_regular and surfaces in
    # the block header, proving the top level refund is scoped to
    # top level failures and not child reverts.
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=sstore_state_gas),
            ),
        ],
        post={parent: Account(storage=parent_storage)},
    )


@pytest.mark.valid_from("EIP8037")
def test_top_level_failure_refunds_spilled_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify the top level failure refund covers state gas that
    spilled from the reservoir into gas_left.

    When the reservoir is smaller than the state gas charge, the
    overflow spills and is drawn from gas_left. On top level failure
    the full consumed state gas (reservoir portion plus spilled
    portion) is credited back to the reservoir so the sender is not
    billed for any of it.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()

    code = Op.SSTORE(0, 1) + Op.REVERT(0, 0)
    contract = pre.deploy_contract(code=code)

    # Reservoir sized to cover only half the SSTORE state gas; the
    # other half must spill into gas_left.
    tx_gas = gas_limit_cap + sstore_state_gas // 2
    expected_cumulative = (
        intrinsic_cost + code.gas_cost(fork) - sstore_state_gas
    )

    tx = Transaction(
        to=contract,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative,
        ),
    )

    state_test(pre=pre, post={contract: Account(storage={})}, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_top_level_failure_refunds_state_gas_propagated_from_child(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify the top level failure refund catches state gas propagated
    from a successful subcall.

    The parent calls a child that runs SSTORE and returns. The
    child's state gas usage is folded into the parent frame via the
    success path. When the parent then reverts at the top level, the
    full propagated state gas must be refunded so the sender fee
    excludes it.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()

    child_code = Op.SSTORE(0, 1)
    child = pre.deploy_contract(code=child_code)
    parent_code = Op.POP(Op.CALL(gas=Op.GAS, address=child)) + Op.REVERT(0, 0)
    parent = pre.deploy_contract(code=parent_code)

    # Reservoir sized for the child's SSTORE. After the propagated
    # state gas is refunded, the sender is billed only the regular
    # gas: parent + CALL dispatch + child regular (SSTORE minus its
    # state component).
    tx_gas = gas_limit_cap + sstore_state_gas
    expected_cumulative = (
        intrinsic_cost
        + parent_code.gas_cost(fork)
        + child_code.gas_cost(fork)
        - sstore_state_gas
    )

    tx = Transaction(
        to=parent,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative,
        ),
    )

    state_test(pre=pre, post={child: Account(storage={})}, tx=tx)


@pytest.mark.parametrize(
    "num_access_list_entries",
    [
        pytest.param(1, id="one_entry"),
        pytest.param(10, id="ten_entries"),
    ],
)
@pytest.mark.parametrize(
    "slots_per_entry",
    [
        pytest.param(0, id="addresses_only"),
        pytest.param(3, id="with_storage_keys"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_access_list_gas_is_regular_not_state(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    num_access_list_entries: int,
    slots_per_entry: int,
) -> None:
    """Verify EIP-2930 access list gas counts as regular, not state."""
    contract = pre.deploy_contract(code=Op.STOP)

    access_list = []
    for _ in range(num_access_list_entries):
        target = pre.fund_eoa(amount=0)
        storage_keys = list(range(slots_per_entry))
        access_list.append(
            AccessList(address=target, storage_keys=storage_keys)
        )

    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    gas_needed = intrinsic_calc(access_list=access_list)

    tx = Transaction(
        to=contract,
        gas_limit=gas_needed,
        sender=pre.fund_eoa(),
        access_list=access_list,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=gas_needed),
            ),
        ],
        post={},
    )


@pytest.mark.valid_from("EIP8037")
def test_access_list_warm_savings_stay_regular(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Verify access-list warm savings stay in regular gas."""
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()

    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.SLOAD(0)),
        storage={0: 1},
    )

    access_list = [AccessList(address=contract, storage_keys=[0])]

    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas = intrinsic_calc(access_list=access_list)

    contract_code = Op.SSTORE.with_metadata(
        key_warm=True,
        original_value=1,
        current_value=1,
        new_value=1,
    )(0, Op.SLOAD.with_metadata(key_warm=True)(0))
    evm_gas = contract_code.gas_cost(fork)

    expected_gas_used = intrinsic_gas + evm_gas
    gas_limit = gas_limit_cap + sstore_state_gas

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
        access_list=access_list,
    )

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
