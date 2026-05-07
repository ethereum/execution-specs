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
    Address,
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
from execution_testing import (
    Macros as Om,
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
    gas_limit = intrinsic_cost() + gas_costs.COLD_STORAGE_WRITE

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

    # tx2: worst-case state contribution = tx.gas - intrinsic_regular.
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
        gas_costs.TX_BASE
        + 2 * gas_costs.VERY_LOW
        + gas_costs.COLD_STORAGE_WRITE
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
    create_state_gas = gas_costs.NEW_ACCOUNT

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


@pytest.mark.parametrize(
    "failure_mode",
    [
        pytest.param("revert", id="revert"),
        pytest.param("halt", id="halt"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_top_level_failure_spilled_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    failure_mode: str,
) -> None:
    """
    Verify the top-level failure handling for state gas that spilled
    from the reservoir into `gas_left`.

    When the reservoir is smaller than the state gas charge, the
    overflow spills and is drawn from `gas_left`. Both failure
    modes refund the full `state_gas_used` (reservoir-portion +
    spilled-portion) to the reservoir per the updated EIP. They
    differ only in `gas_left` handling:

    - REVERT preserves `gas_left`; sender billed only the regular
      component.
    - Exceptional halt zeros `gas_left` (existing EVM rule); sender
      pays for everything except the state-gas refund.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()

    if failure_mode == "revert":
        code = Op.SSTORE(0, 1) + Op.REVERT(0, 0)
    else:
        code = Op.SSTORE(0, 1) + Op.INVALID
    contract = pre.deploy_contract(code=code)

    # Reservoir sized to cover only half the SSTORE state gas; the
    # other half spills into gas_left.
    tx_gas = gas_limit_cap + sstore_state_gas // 2

    if failure_mode == "revert":
        # gas_left preserved; full state_gas_used refunded to
        # reservoir → sender billed only the regular component.
        expected_cumulative = (
            intrinsic_cost + code.gas_cost(fork) - sstore_state_gas
        )
    else:
        # gas_left burned; full state_gas_used (reservoir-portion +
        # spilled-portion) refunded via reservoir.
        # tx_gas_used = tx_gas - 0 - sstore_state_gas.
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
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_top_level_failure_propagated_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    failure_mode: str,
) -> None:
    """
    Verify the top-level failure handling for state gas propagated
    from a successful subcall.

    The parent calls a child that runs SSTORE and returns. The
    child's `state_gas_used` is folded into the parent frame via the
    success path so the parent's reservoir is empty and its
    `state_gas_used` carries the SSTORE charge.

    Per the updated EIP both failure modes refund the full propagated
    `state_gas_used` (reservoir-portion + spilled-portion) to the
    reservoir. They differ only in `gas_left` handling:

    - REVERT preserves `gas_left`; sender billed only the regular
      component.
    - Exceptional halt zeros `gas_left`; sender pays for everything
      except the state-gas refund.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()

    child_code = Op.SSTORE(0, 1)
    child = pre.deploy_contract(code=child_code)
    if failure_mode == "revert":
        parent_code = Op.POP(Op.CALL(gas=Op.GAS, address=child)) + Op.REVERT(
            0, 0
        )
    else:
        parent_code = Op.POP(Op.CALL(gas=Op.GAS, address=child)) + Op.INVALID
    parent = pre.deploy_contract(code=parent_code)

    # Reservoir sized to half the SSTORE state gas so the child's
    # charge drains the reservoir AND spills into gas_left. The halt
    # path then exercises a non-trivial spill case rather than the
    # degenerate no-spill case.
    tx_gas = gas_limit_cap + sstore_state_gas // 2

    if failure_mode == "revert":
        # gas_left preserved; full propagated state_gas_used refunded
        # → sender billed only the regular component.
        expected_cumulative = (
            intrinsic_cost
            + parent_code.gas_cost(fork)
            + child_code.gas_cost(fork)
            - sstore_state_gas
        )
    else:
        # gas_left burned; full propagated state_gas_used (reservoir
        # + spill) refunded via reservoir.
        # tx_gas_used = tx_gas - 0 - sstore_state_gas.
        expected_cumulative = tx_gas - sstore_state_gas

    tx = Transaction(
        to=parent,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative,
        ),
    )

    state_test(pre=pre, post={child: Account(storage={})}, tx=tx)


def _build_call_chain(
    pre: Alloc,
    frame_bodies: list[Bytecode],
    terminator: Bytecode,
) -> tuple[Address, list[Bytecode]]:
    """
    Build a chain of CALL-nested frames.

    Each non-deepest frame executes its body, CALLs the next frame,
    then terminates with `terminator`. The deepest frame just
    executes its body and terminates.
    """
    deepest_idx = len(frame_bodies) - 1
    deepest_code = frame_bodies[deepest_idx] + terminator
    frame_codes: list[Bytecode] = [deepest_code]
    inner_addr = pre.deploy_contract(code=deepest_code)
    for depth in range(deepest_idx - 1, -1, -1):
        code = (
            frame_bodies[depth]
            + Op.POP(Op.CALL(gas=Op.GAS, address=inner_addr))
            + terminator
        )
        inner_addr = pre.deploy_contract(code=code)
        frame_codes.insert(0, code)
    return inner_addr, frame_codes


def _build_create_chain(
    pre: Alloc,
    frame_bodies: list[Bytecode],
    terminator: Bytecode,
) -> tuple[Address, list[Bytecode]]:
    """
    Build a chain of CREATE-nested frames.

    Top frame is a deployed contract; each non-deepest frame executes
    its body, places the next-level initcode in memory, CREATEs it,
    then terminates with `terminator`. The deepest level's initcode
    just executes its body and terminates.

    Each CREATE pre-charges `STATE_NEW × cpsb` of state-gas on the
    parent frame, which is what makes this chain exercise the
    credit-on-failure path that distinguishes Policy A from Policy B
    for top-level halt.
    """
    n = len(frame_bodies)
    # Deepest level is just body + terminator (runs as initcode of
    # the depth-(N-2) frame's CREATE).
    inner_initcode = frame_bodies[-1] + terminator
    frame_codes: list[Bytecode] = [inner_initcode]

    for i in range(n - 2, -1, -1):
        inner_bytes = bytes(inner_initcode)
        inner_size = len(inner_bytes)
        # Pad to 32-byte alignment so Om.MSTORE uses the cheap
        # PUSH32+MSTORE path on the trailing chunk; CREATE reads
        # only `size` bytes so the trailing zeros are ignored.
        padded = inner_bytes + b"\x00" * ((-inner_size) % 32)
        code = (
            frame_bodies[i]
            + Om.MSTORE(padded, 0)
            + Op.POP(
                Op.CREATE(
                    value=0,
                    offset=0,
                    size=inner_size,
                    init_code_size=inner_size,
                )
            )
            + terminator
        )
        frame_codes.insert(0, code)
        inner_initcode = code

    top = pre.deploy_contract(code=frame_codes[0])
    return top, frame_codes


@pytest.mark.parametrize(
    "frame_bodies",
    [
        pytest.param(
            [
                Op.SSTORE(0, 1),
                Op.SSTORE(1, 1),
                Op.SSTORE(2, 1),
                Op.SSTORE(3, 1),
            ],
            id="depth_4_sstore_each",
        ),
        pytest.param(
            [
                Op.SSTORE(0, 1),
                Bytecode(),
                Op.SSTORE(2, 1),
                Bytecode(),
            ],
            id="depth_4_alternating_state",
        ),
        pytest.param(
            [Bytecode(), Bytecode(), Bytecode(), Bytecode()],
            id="depth_4_no_state",
        ),
        pytest.param(
            [
                Op.SSTORE(0, 1) + Op.SSTORE(1, 1),
                Op.SSTORE(2, 1) + Op.SSTORE(3, 1),
                Op.SSTORE(4, 1) + Op.SSTORE(5, 1),
            ],
            id="depth_3_two_sstores_each",
        ),
        pytest.param(
            [
                Bytecode(),
                Bytecode(),
                Op.SSTORE(0, 1)
                + Op.SSTORE(
                    0,
                    0,
                    key_warm=True,
                    original_value=0,
                    current_value=1,
                    new_value=0,
                ),
            ],
            id="depth_3_deepest_0_to_x_to_0",
        ),
        pytest.param(
            [
                Bytecode(),
                Bytecode(),
                Op.SSTORE(0, 1)
                + Op.SSTORE(
                    0,
                    2,
                    key_warm=True,
                    original_value=0,
                    current_value=1,
                    new_value=2,
                )
                + Op.SSTORE(
                    0,
                    0,
                    key_warm=True,
                    original_value=0,
                    current_value=2,
                    new_value=0,
                ),
            ],
            id="depth_3_deepest_0_to_x_to_y_to_0",
        ),
    ],
)
@pytest.mark.parametrize(
    "failure_mode",
    [
        pytest.param("revert", id="revert"),
        pytest.param("halt", id="halt"),
    ],
)
@pytest.mark.parametrize(
    "spill_mode",
    [
        pytest.param("no_spill", id="no_spill"),
        pytest.param("spill", id="spill"),
    ],
)
@pytest.mark.parametrize(
    "frame_op",
    [
        pytest.param("call", id="call_chain"),
        pytest.param("create", id="create_chain"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_nested_failure_resets_to_tx_reservoir(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    failure_mode: str,
    frame_bodies: list[Bytecode],
    spill_mode: str,
    frame_op: str,
) -> None:
    """
    Verify failure cascade refunds state-gas to the top reservoir.

    Each frame runs its parametrized body, then calls or CREATEs the
    next frame, terminating with the failure mode. Every level fails
    so the cascade reaches the top.

    Axes:
    - `failure_mode`: REVERT vs HALT (top-level gas_left semantics
      differ; state-gas refund must agree per the updated EIP).
    - `spill_mode`: `no_spill` sizes the reservoir to cover all
      state-gas charges. `spill` shrinks it so charges drain into
      gas_left, exercising the spill-refund-on-halt rule.
    - `frame_op`: `call` chains via CALL (no per-frame pre-charge).
      `create` chains via CREATE (each level pre-charges
      `STATE_BYTES_PER_NEW_ACCOUNT × cpsb`, exercising
      credit-on-failure interleaved with the spill).

    Per the updated EIP, every state-gas charge — body charges,
    spilled portions, and CREATE pre-charges — is refunded to the
    top-level reservoir on either revert or halt. So the user pays
    `tx_gas - max(reservoir, total_state_charges)` on halt and only
    regular charges + intrinsic on revert, regardless of axes.

    Two assertions cross-check the gas accounting:
    - `cumulative_gas_used` (receipt) pins `tx.gas - gas_left -
      state_gas_left`, catching bugs in the leftover split.
    - `header.gas_used` pins `max(block_regular, block_state)` via
      the block accumulators.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()
    new_account_state_gas = fork.gas_costs().NEW_ACCOUNT
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()

    body_state_total = sum(b.state_cost(fork) for b in frame_bodies)
    n_creates = (len(frame_bodies) - 1) if frame_op == "create" else 0
    total_state_charges = body_state_total + n_creates * new_account_state_gas

    if spill_mode == "no_spill":
        # Reservoir comfortably covers all state-gas charges.
        reservoir = max(
            total_state_charges + sstore_state_gas, sstore_state_gas
        )
    else:
        # Reservoir is small; charges spill into gas_left.
        reservoir = sstore_state_gas
    tx_gas = gas_limit_cap + reservoir

    terminator = Op.REVERT(0, 0) if failure_mode == "revert" else Op.INVALID

    if frame_op == "call":
        top, frame_codes = _build_call_chain(pre, frame_bodies, terminator)
    else:
        top, frame_codes = _build_create_chain(pre, frame_bodies, terminator)

    sum_regular = sum(code.regular_cost(fork) for code in frame_codes)
    spill = max(0, total_state_charges - reservoir)
    if failure_mode == "halt":
        # Policy A (updated EIP): all state-gas — body charges, spilled
        # portions, and CREATE pre-charges (returned via credit) — folds
        # into state_gas_left at tx end. gas_left is zeroed by halt.
        state_gas_at_end = max(reservoir, total_state_charges)
        expected_cumulative = tx_gas - state_gas_at_end
        # Header: block_regular = gas_limit_cap - spill (spilled
        # state-gas drained gas_left but is no longer reclassified to
        # regular under Policy A); block_state ≈ 0 for plain CALLs.
        expected_header_gas_used = gas_limit_cap - spill
    elif failure_mode == "revert":
        # Revert preserves gas_left; full state-gas refund.
        # User pays only regular costs + intrinsic.
        expected_cumulative = intrinsic_cost + sum_regular
        # Header reflects the regular-vs-state attribution directly:
        # state_gas_used is zeroed by the tx error handler, so only
        # regular gas usage shows up.
        expected_header_gas_used = intrinsic_cost + sum_regular
    else:
        raise ValueError("Invariant, unreachable code.")

    tx = Transaction(
        to=top,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative,
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=expected_header_gas_used),
            )
        ],
        post={},
    )


@pytest.mark.valid_from("EIP8037")
def test_top_level_opcode_oog_before_frame_end_does_not_refund_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify an opcode OOG before frame-end settlement does not refund
    unsettled state gas.

    The transaction has enough gas for the SSTORE and all preceding
    regular work, but is one gas short of the MCOPY regular cost. The
    frame halts before frame-end settlement runs, so the earlier SSTORE
    never contributes execution state gas to refund.
    """
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    sstore_state_gas = fork.sstore_state_gas()

    code = Op.SSTORE(0, 1) + Op.MCOPY(
        0x1000,
        0,
        1,
        old_memory_size=0,
        new_memory_size=0x1001,
        data_size=1,
    )
    contract = pre.deploy_contract(code=code)

    # One gas short of the regular-gas portion of successful execution.
    tx_gas = intrinsic_cost + code.gas_cost(fork) - sstore_state_gas - 1

    tx = Transaction(
        to=contract,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=tx_gas,
        ),
    )

    state_test(pre=pre, post={contract: Account(storage={})}, tx=tx)


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


@pytest.mark.valid_from("EIP8037")
def test_subcall_revert_does_not_leak_grandchild_storage_clear_credit(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify a grandchild's storage-clear reservoir credit cannot leak
    past a reverting parent into the top frame's reservoir.

    Three-frame DELEGATECALL chain so all SSTOREs target the top
    contract's storage:

      - top: SSTOREs slots[0..4]=1, DELEGATECALLs `mid`, then
        SSTOREs slots[10..14]=1.
      - mid: DELEGATECALLs `inner`, then REVERTs.
      - inner: SSTOREs slots[0..4]=0, clearing what top set.

    Inner's frame-end sees byte_delta=-160 against its own snapshot
    (slots non-zero at frame entry, zero at tx start, zero at exit)
    and credits its reservoir by 5 * sstore_state_gas. On mid's
    revert that storage clear is rolled back, but the credit lives
    on inside mid's reservoir from the prior
    `incorporate_child_on_success`. The credit must not propagate
    out of mid via `incorporate_child_on_error`, because the
    underlying state transition no longer exists.

    The reservoir is sized to the legitimate state cost
    (10 * sstore_state_gas: 5 setup writes + 5 phantom writes). Top
    drains the reservoir at frame-end and the receipt charges the
    full legitimate cost. If the credit leaks, an extra
    5 * sstore_state_gas remains in `state_gas_reservoir` at tx end
    and the receipt formula `tx.gas - gas_left -
    state_gas_reservoir` would charge the sender 5 * sstore_state_gas
    less.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()

    num_slots = 5
    phantom_base = 10

    # `inner` clears slots [0..num_slots-1] in the caller's storage
    # context, which under the DELEGATECALL chain is `top`. The
    # slots are warm because top accessed them during setup and
    # `accessed_storage_keys` propagated through the DELEGATECALLs.
    inner_code = Bytecode()
    for i in range(num_slots):
        inner_code += Op.SSTORE.with_metadata(
            key_warm=True,
            original_value=0,
            current_value=1,
            new_value=0,
        )(i, 0)
    inner = pre.deploy_contract(code=inner_code)

    mid_code = Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=inner)) + Op.REVERT(
        0, 0
    )
    mid = pre.deploy_contract(code=mid_code)

    setup_code = Bytecode()
    for i in range(num_slots):
        setup_code += Op.SSTORE(i, 1)
    delegatecall_step = Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=mid))
    phantom_code = Bytecode()
    for i in range(num_slots):
        phantom_code += Op.SSTORE(phantom_base + i, 1)
    top_code = setup_code + delegatecall_step + phantom_code
    top = pre.deploy_contract(code=top_code)

    # Reservoir sized to the legitimate state cost only; any
    # phantom credit surfaces as residual reservoir at tx end.
    legit_state_cost = 2 * num_slots * sstore_state_gas
    tx_gas = gas_limit_cap + legit_state_cost

    # `bytecode.gas_cost(fork)` sums each opcode's regular and state
    # contributions. Setup/phantom SSTOREs predict +sstore_state_gas
    # each; inner's clears predict 0 (the negative byte_delta is a
    # frame-level effect, not per-opcode). The frame-end byte_delta
    # at top is +320 (10 set slots persist, the inner clear is rolled
    # back), so the predicted state total of 10 * sstore_state_gas
    # matches the actual charge.
    expected_cumulative = (
        intrinsic_cost
        + top_code.gas_cost(fork)
        + mid_code.gas_cost(fork)
        + inner_code.gas_cost(fork)
    )

    tx = Transaction(
        to=top,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative,
        ),
    )
    expected_storage = dict.fromkeys(range(num_slots), 1) | {
        phantom_base + i: 1 for i in range(num_slots)
    }

    state_test(
        pre=pre,
        post={top: Account(storage=expected_storage)},
        tx=tx,
    )


@pytest.mark.parametrize(
    "intermediate_depth",
    [
        pytest.param(0, id="direct"),
        pytest.param(1, id="depth_1"),
        pytest.param(3, id="depth_3"),
        pytest.param(10, id="depth_10"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_revert_discards_descendant_storage_clear_credit_through_depth(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    intermediate_depth: int,
) -> None:
    """
    A reverted ancestor must discard a clear-credit regardless of
    how many successful frames sit between the X→0 source and the
    revert.

    top → reverter (REVERT)
            → pass_1 → … → pass_k → inner (X→0)

    Each pass frame returns successfully, so the inner credit walks
    up through `incorporate_child_on_success` at every layer before
    landing in the reverter, where it must be dropped on
    `incorporate_child_on_error`. The receipt invariant holds for
    every `k`.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()

    num_slots = 5
    phantom_base = 10

    # Slots are warm at inner: top's setup populates the access list
    # and DELEGATECALL preserves it down the chain.
    inner_code = Bytecode()
    for i in range(num_slots):
        inner_code += Op.SSTORE.with_metadata(
            key_warm=True,
            original_value=0,
            current_value=1,
            new_value=0,
        )(i, 0)
    inner = pre.deploy_contract(code=inner_code)

    # Build the pass-through chain bottom-up so each frame can encode
    # the next address. Each pass_i DELEGATECALLs into the next frame
    # and STOPs successfully, propagating inner's credit upward.
    pass_codes = []
    next_addr = inner
    for _ in range(intermediate_depth):
        pass_code = (
            Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=next_addr)) + Op.STOP
        )
        pass_codes.append(pass_code)
        next_addr = pre.deploy_contract(code=pass_code)

    # Reverter sits between top and the chain: enters, then REVERTs.
    reverter_code = Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=next_addr)) + (
        Op.REVERT(0, 0)
    )
    reverter = pre.deploy_contract(code=reverter_code)

    setup_code = Bytecode()
    for i in range(num_slots):
        setup_code += Op.SSTORE(i, 1)
    delegatecall_step = Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=reverter))
    phantom_code = Bytecode()
    for i in range(num_slots):
        phantom_code += Op.SSTORE(phantom_base + i, 1)
    top_code = setup_code + delegatecall_step + phantom_code
    top = pre.deploy_contract(code=top_code)

    legit_state_cost = 2 * num_slots * sstore_state_gas
    tx_gas = gas_limit_cap + legit_state_cost

    expected_cumulative = (
        intrinsic_cost
        + top_code.gas_cost(fork)
        + reverter_code.gas_cost(fork)
        + sum(c.gas_cost(fork) for c in pass_codes)
        + inner_code.gas_cost(fork)
    )

    tx = Transaction(
        to=top,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative,
        ),
    )
    expected_storage = dict.fromkeys(range(num_slots), 1) | {
        phantom_base + i: 1 for i in range(num_slots)
    }

    state_test(
        pre=pre,
        post={top: Account(storage=expected_storage)},
        tx=tx,
    )


@pytest.mark.valid_from("EIP8037")
def test_set_and_clear_pays_no_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A 0→X SSTORE paired with an X→0 on the same slot must cancel in
    the state-gas reservoir. With a tight regular-gas budget and no
    reservoir headroom (tx.gas <= TX_MAX_GAS_LIMIT, so reservoir = 0),
    the tx completes only because the frame-end byte_delta nets to
    zero.

    A standalone 0→X here would charge +sstore_state_gas at frame
    end, spill into gas_left, and OOG against this budget. The
    follow-up X→0 returns the slot to its tx-start original (0), so
    `compute_state_byte_diff` reports byte_delta=0 and the
    state-gas reservoir is never touched.
    """
    gas_costs = fork.gas_costs()
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()

    # Same slot, set then cleared. Frame-end byte_delta = 0.
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
    code = set_op + clear_op
    contract = pre.deploy_contract(code=code)

    # Tight budget: bytecode regular gas plus the headroom required by
    # the warm SSTORE's `check_gas(CALL_STIPEND + 1)` precondition.
    # The warm 100-gas charge is already inside `code.regular_cost`,
    # so the extra headroom needed is `CALL_STIPEND + 1 - WARM_ACCESS`.
    extra_for_stipend = gas_costs.CALL_STIPEND + 1 - gas_costs.WARM_ACCESS
    gas_limit = intrinsic_cost + code.regular_cost(fork) + extra_for_stipend

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    # Slot 0 returns to its tx-start value (0). The reservoir was
    # never touched because frame-end byte_delta was zero.
    post = {contract: Account(storage={0: 0})}
    state_test(pre=pre, post=post, tx=tx)
