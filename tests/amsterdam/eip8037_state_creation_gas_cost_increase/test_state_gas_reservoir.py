"""
Test cases for the EIP-8037 state gas reservoir and its interaction with the
EIP-7825 TX_MAX_GAS_LIMIT cap.

EIP-8037 splits execution gas into two pools:
- `gas_left` (execution gas): capped at
  `TX_MAX_GAS_LIMIT - intrinsic.execution`
- `state_gas_reservoir`: the overflow beyond the execution gas cap

State gas charges draw from the reservoir first, then spill into gas_left.
Execution gas charges draw only from gas_left.

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
    compute_create_address,
)
from execution_testing import (
    Macros as Om,
)
from execution_testing.checklists import EIPChecklist

from tests.prague.eip7702_set_code_tx.spec import Spec as Spec7702

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
    storage = Storage()
    code = Bytecode()
    for _ in range(num_sstores):
        code += Op.SSTORE(storage.store_next(1), 1)
    contract = pre.deploy_contract(code=code)

    if reservoir_covers_state_gas:
        extra_gas = code.state_cost(fork)
    else:
        extra_gas = 1  # Minimal reservoir, rest spills to gas_left

    tx = Transaction(
        to=contract,
        state_gas_reservoir=extra_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_sstore_state_gas_entirely_from_gas_left(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test SSTORE state gas charged entirely from gas_left (no reservoir).

    When tx.gas <= TX_MAX_GAS_LIMIT, the reservoir is zero. All state
    gas must come from gas_left.
    """
    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
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
def test_insufficient_gas_for_sstore_state_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that execution OOGs when gas is insufficient for SSTORE state cost.

    Provide just enough gas for intrinsic costs plus the SSTORE execution
    gas, but not enough to also cover the SSTORE state gas. The SSTORE
    should OOG, leaving storage slot 0 unchanged at zero.
    """
    contract_code = Op.SSTORE(0, 1)
    contract = pre.deploy_contract(code=contract_code)

    # Enough for intrinsic + warm SSTORE execution gas, but not the
    # state gas cost for zero-to-nonzero transition
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    gas_limit = intrinsic_cost() + contract_code.execution_cost(fork)

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    # Execution OOGs — storage slot 0 remains at default (zero)
    post = {contract: Account(storage={0: 0})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.inclusion_test
@pytest.mark.parametrize(
    "exceed_block_gas_limit",
    [
        pytest.param(True, marks=pytest.mark.exception_test),
        pytest.param(False),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_block_execution_gas_limit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    exceed_block_gas_limit: bool,
    fork: Fork,
) -> None:
    """
    Test check_transaction enforcement of execution gas against block limit.

    The execution gas check uses min(TX_MAX_GAS_LIMIT, tx.gas).
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


@pytest.mark.inclusion_test
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
    its worst-case state contribution `tx.gas` equals `state_available`
    (delta=0, accepted because the check is strict `>`) or exceeds it
    by 1 (delta=1, rejected with `GAS_ALLOWANCE_EXCEEDED`).

    The execution check is asserted to pass so rejection on delta=1 is
    pinned to the state dimension.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    block_gas_limit = 100_000_000

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()

    num_sstores = 50
    tx1_code = Bytecode()
    for i in range(num_sstores):
        tx1_code = tx1_code + Op.SSTORE(i, 1)
    tx1_contract = pre.deploy_contract(code=tx1_code)

    tx1_state = tx1_code.state_cost(fork)
    tx1_execution = intrinsic_cost() + tx1_code.gas_cost(fork) - tx1_state
    tx1_gas = gas_limit_cap + tx1_state

    # tx2: worst-case state contribution = tx.gas (strict EIP rule).
    # Plain call, so intrinsic_state is zero.
    state_available = block_gas_limit - tx1_state
    tx2_gas = state_available + delta

    # Pin the rejection (when delta > 0) to the state check: the
    # execution check must not fire.
    execution_available = block_gas_limit - tx1_execution
    assert min(gas_limit_cap, tx2_gas) < execution_available, (
        "tx2 would fail the execution check instead of the state check"
    )

    tx2_error = (
        TransactionException.GAS_ALLOWANCE_EXCEEDED if delta > 0 else None
    )
    block_exception = tx2_error

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


@pytest.mark.inclusion_test
@pytest.mark.exception_test
@pytest.mark.valid_from("EIP8037")
def test_creation_tx_execution_check_uses_full_tx_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify the execution check uses the full `tx.gas` (no subtraction).

    The EIP execution check is `min(TX_MAX, tx.gas) > execution_available`.
    Under EIP-2780 a creation tx has `intrinsic.state == 0` (the created
    account's `NEW_ACCOUNT` moved to the top frame), so its intrinsic is
    execution-only. This test sizes a creation tx whose full `tx.gas`
    exceeds the remaining execution budget by one — it must be rejected. A
    formula that instead used the execution gas
    (`tx.gas - intrinsic_execution`) would have wrongly accepted.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    # The creation intrinsic is execution-only and cpsb-free
    # (GAS_TX_BASE + EXECUTION_GAS_CREATE + init_code_cost), giving a stable
    # `block_gas_limit` independent of cpsb.
    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        contract_creation=True
    )

    # Tight boundary: after the filler consumes gas_limit_cap, exactly
    # `intrinsic_execution + 1` execution gas remains in the block.
    block_gas_limit = gas_limit_cap + intrinsic_execution + 1

    # Ask for one more than the remaining execution budget: min(TX_MAX,
    # tx.gas) == tx.gas exceeds `remaining_execution` by one, so the strict
    # check rejects. The tx still carries more than its own intrinsic, so
    # it is a valid creation tx on its own — only the block-level execution
    # check fails.
    remaining_execution = block_gas_limit - gas_limit_cap
    create_tx_gas = remaining_execution + 1

    # Filler consumes the full execution cap (OOG on INVALID).
    filler = pre.deploy_contract(code=Op.INVALID)

    assert create_tx_gas <= gas_limit_cap, (
        "min(TX_MAX, tx.gas) must be tx.gas for this boundary"
    )
    assert create_tx_gas > intrinsic_execution, (
        "tx must carry more than its own intrinsic"
    )
    assert min(gas_limit_cap, create_tx_gas) > remaining_execution, (
        "strict formula must reject: full tx.gas exceeds remaining execution"
    )
    assert create_tx_gas - intrinsic_execution <= remaining_execution, (
        "a formula using execution gas would have accepted"
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
        error=TransactionException.GAS_ALLOWANCE_EXCEEDED,
    )

    blockchain_test(
        genesis_environment=Environment(gas_limit=block_gas_limit),
        pre=pre,
        blocks=[
            Block(
                txs=[filler_tx, create_tx],
                gas_limit=block_gas_limit,
                exception=TransactionException.GAS_ALLOWANCE_EXCEEDED,
            )
        ],
        post={},
    )


@pytest.mark.inclusion_test
@pytest.mark.exception_test
@pytest.mark.valid_from("EIP8037")
def test_single_tx_state_check_exceeds_block_limit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify a single tx is rejected when its gas limit exceeds the
    entire block gas limit in the state dimension.

    No prior txs needed. The state check uses the full `tx.gas`, so a
    tx whose `tx.gas` exceeds `block_gas_limit` must be rejected at
    inclusion.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    block_gas_limit = gas_limit_cap + 100
    tx_gas = block_gas_limit + 1

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


@pytest.mark.inclusion_test
@pytest.mark.exception_test
@pytest.mark.valid_from("EIP8037")
def test_creation_tx_state_check_exceeded(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify a creation tx is rejected by the state check.

    A creation tx (`to=None`) goes through the per-dimension inclusion
    check like any other tx. A filler tx consumes state budget; the
    creation tx's `tx.gas` then exceeds the remaining state budget by
    one while its execution contribution still fits, pinning the
    rejection to the state dimension.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    block_gas_limit = 100_000_000

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()

    num_sstores = 50
    tx1_code = Bytecode()
    for i in range(num_sstores):
        tx1_code = tx1_code + Op.SSTORE(i, 1)
    tx1_contract = pre.deploy_contract(code=tx1_code)

    tx1_state = tx1_code.state_cost(fork)
    tx1_execution = intrinsic_cost() + tx1_code.gas_cost(fork) - tx1_state
    tx1_gas = gas_limit_cap + tx1_state
    state_available = block_gas_limit - tx1_state

    # tx2: full tx.gas exceeds state_available by 1, so rejected.
    tx2_gas = state_available + 1

    # Execution check must pass so rejection is pinned to state.
    execution_available = block_gas_limit - tx1_execution
    assert min(gas_limit_cap, tx2_gas) < execution_available

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
    Test block gas_used when execution gas dominates (no state operations).

    With no state-creating operations, state gas is 0 and block gas_used
    should equal execution gas used.
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
    storage = Storage()
    code = Op.SSTORE(storage.store_next(1), 1)
    contract = pre.deploy_contract(code=code)

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    block_execution_gas = intrinsic_cost() + code.execution_cost(fork)
    block_state_gas = code.state_cost(fork)
    assert block_state_gas > block_execution_gas

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(
                    gas_used=block_state_gas,
                ),
            ),
        ],
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

    EIP-8037 block validity: max(execution, state) <= gas_limit.
    Receipt cumulative_gas_used sums both dimensions per-tx, so it
    can legitimately exceed gas_limit. Clients must not use the 1D
    cumulative check for block validation.
    """
    block_gas_limit = 100_000_000

    sstore_code = Op.SSTORE(0, 1, new_value=1)
    sstore_state_gas = sstore_code.state_cost(fork)

    tx_execution = (
        sstore_code.execution_cost(fork)
        + fork.transaction_intrinsic_cost_calculator()()
    )
    tx_state = sstore_state_gas
    tx_gas_used = tx_execution + tx_state

    assert tx_state > tx_execution
    block_gas_used = tx_state

    env = Environment(gas_limit=block_gas_limit)
    tx_limit = tx_gas_used + 1000

    # Strict rule counts full `tx.gas` per dimension; state is the
    # binding one (tx_state > tx_execution), so every `tx_limit` must
    # fit the remaining state gas.
    num_txs = (block_gas_limit - tx_limit) // tx_state + 1
    two_d_bound = num_txs * block_gas_used
    one_d_bound = num_txs * tx_gas_used
    assert two_d_bound <= block_gas_limit < one_d_bound

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
                    gas_used=num_txs * block_gas_used,
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
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    init_code = Op.STOP

    create_state_gas = fork.transaction_top_frame_state_gas(
        contract_creation=True
    )

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

    state_test(pre=pre, post={}, tx=tx)


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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()

    if failure_mode == "revert":
        code = Op.SSTORE(0, 1) + Op.REVERT(0, 0)
    elif failure_mode == "halt":
        code = Op.SSTORE(0, 1) + Op.INVALID
    else:
        # OOG: perform the SSTORE, then consume all remaining gas at
        # once (a spin loop would execute millions of ops in the EVM
        # and slow down filling).
        code = Op.SSTORE(0, 1) + Om.OOG
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
        state_gas_reservoir=sstore_state_gas,
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
    the block header `gas_used` falls back to the execution gas
    component alone.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()

    if failure_mode == "revert":
        code = Op.SSTORE(0, 1) + Op.REVERT(0, 0)
    elif failure_mode == "halt":
        code = Op.SSTORE(0, 1) + Op.INVALID
    else:
        code = Op.SSTORE(0, 1) + Om.OOG
    contract = pre.deploy_contract(code=code)

    tx_gas = gas_limit_cap + sstore_state_gas
    tx = Transaction(
        to=contract,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    if failure_mode == "revert":
        expected_block_execution = (
            intrinsic_cost + code.gas_cost(fork) - sstore_state_gas
        )
    else:
        # Exceptional halt and out of gas zero gas_left.
        expected_block_execution = tx_gas - sstore_state_gas

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=expected_block_execution),
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
    `gas_used` equals `max(block_execution, intrinsic_state_gas)`,
    guarding that the failure path does not raise and that block
    accounting does not underflow when the refund is applied.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    create_intrinsic_state = fork.transaction_top_frame_state_gas(
        contract_creation=True,
    )
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    tx_gas = gas_limit_cap + create_intrinsic_state + sstore_state_gas

    tx = Transaction(
        to=None,
        data=Op.SSTORE(0, 1) + Op.INVALID,
        state_gas_reservoir=create_intrinsic_state + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    block_execution = tx_gas - create_intrinsic_state - sstore_state_gas
    expected_gas_used = max(block_execution, create_intrinsic_state)

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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

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
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    # Parent's SSTORE state gas dominates tx_execution and surfaces in
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
    "spill_source",
    [
        pytest.param("own", id="own_spill"),
        pytest.param("propagated", id="propagated_spill"),
        pytest.param("both", id="own_and_propagated_spill"),
    ],
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
    spill_source: str,
) -> None:
    """
    Verify top-level failure handling for spilled state gas, whether
    the spill is charged in the frame itself, propagated from a
    successful subcall, or both.

    The reservoir covers half an SSTORE's state gas, so each SSTORE
    charge spills into `gas_left`. A successful child propagates its
    `state_gas_spilled` into the parent, accumulating with the parent's
    own spill. Refunds are LIFO, so the spilled portion returns to
    `gas_left` and only the reservoir-funded portion to the reservoir.

    - REVERT preserves `gas_left`, so all state gas is refunded and the
      sender pays only the execution component.
    - Halt refills LIFO then zeros `gas_left`, so the spill is burned
      and only the start reservoir survives.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()

    terminator = Op.REVERT(0, 0) if failure_mode == "revert" else Op.INVALID
    has_child = spill_source in ("propagated", "both")
    child_code = Op.SSTORE(0, 1)

    parent_code = Bytecode()
    if spill_source in ("own", "both"):
        parent_code += Op.SSTORE(0, 1)
    child = None
    if has_child:
        child = pre.deploy_contract(code=child_code)
        parent_code += Op.POP(Op.CALL(gas=Op.GAS, address=child))
    parent_code += terminator
    parent = pre.deploy_contract(code=parent_code)

    # Reservoir covers half an SSTORE's state gas, so every SSTORE
    # spills into gas_left.
    reservoir = sstore_state_gas // 2
    tx_gas = gas_limit_cap + reservoir
    total_state = sstore_state_gas * (
        (1 if spill_source in ("own", "both") else 0) + (1 if has_child else 0)
    )

    if failure_mode == "revert":
        # gas_left preserved, all state gas refunded, so the sender
        # pays only the execution component.
        expected_cumulative = (
            intrinsic_cost + parent_code.gas_cost(fork) - total_state
        )
        if has_child:
            expected_cumulative += child_code.gas_cost(fork)
    else:
        # gas_left burned after LIFO refill. The spill returns to
        # gas_left and is consumed, so only the start reservoir
        # survives.
        expected_cumulative = tx_gas - reservoir

    tx = Transaction(
        to=parent,
        state_gas_reservoir=reservoir,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative,
        ),
    )

    post = {parent: Account(storage={})}
    if child is not None:
        post[child] = Account(storage={})
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "gas_limit",
    [
        pytest.param(150_000, id="gas_150k"),
        pytest.param(200_000, id="gas_200k"),
        pytest.param(300_000, id="gas_300k"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_spilled_state_gas_consumed_across_halt_chain(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_limit: int,
) -> None:
    """
    Verify spilled state gas stays consumed along a chain of halting frames.

    A self-`DELEGATECALL`ing contract writes `NOT(storage[slot])`, so set and
    clear alternate down the shared-storage call stack and the reservoir is
    recycled instead of drained once. Each frame reuses the value it wrote as
    a `CALL`'s `args_size`, so the frames that set the slot halt on the
    memory-size overflow while the frames that cleared it re-enter the
    contract, interleaving halting and surviving frames. Every halt must burn
    its spill rather than credit it back to the caller's reservoir, so the
    top-level halt charges the whole gas limit.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    # Below the cap, so the reservoir starts empty and every set spills.
    assert gas_limit < gas_limit_cap

    slot = 0
    value_offset = 0
    contract = pre.deploy_contract(
        code=(
            # Memory is per-frame, so each frame keeps the value it wrote
            # and reuses it below as the CALL's args_size.
            Op.MSTORE(value_offset, Op.NOT(Op.SLOAD(slot)))
            + Op.SSTORE(slot, Op.MLOAD(value_offset))
            + Op.POP(Op.DELEGATECALL(address=Op.ADDRESS))
            # An all-ones args_size overflows the memory-size calculation
            # and halts the frame. A zero one, in a frame that cleared the
            # slot, re-enters the contract and spawns further frames.
            + Op.POP(
                Op.CALL(address=Op.ADDRESS, args_size=Op.MLOAD(value_offset))
            )
        ),
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(cumulative_gas_used=gas_limit),
    )

    state_test(pre=pre, post={contract: Account(storage={})}, tx=tx)


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
    remaining_frame_bodies = frame_bodies[:]
    deepest_code = remaining_frame_bodies.pop() + terminator
    frame_codes: list[Bytecode] = [deepest_code]
    inner_addr = pre.deploy_contract(code=deepest_code)
    while remaining_frame_bodies:
        code = (
            remaining_frame_bodies.pop()
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

    Each CREATE pre-charges `STATE_NEW * cpsb` of state gas on the
    parent frame, which makes this chain exercise the LIFO
    refill-on-failure path for top-level halt.
    """
    remaining_frame_bodies = frame_bodies[:]
    # Deepest level is just body + terminator (runs as initcode of
    # the depth-(N-2) frame's CREATE).
    inner_initcode = remaining_frame_bodies.pop() + terminator
    frame_codes: list[Bytecode] = [inner_initcode]

    while remaining_frame_bodies:
        inner_bytes = bytes(inner_initcode)
        inner_size = len(inner_bytes)
        # Pad to 32-byte alignment so Om.MSTORE uses the cheap
        # PUSH32+MSTORE path on the trailing chunk. CREATE reads
        # only `size` bytes, so the trailing zeros are ignored.
        padded = inner_bytes + b"\x00" * ((-inner_size) % 32)
        code = (
            remaining_frame_bodies.pop()
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
    - `failure_mode`: REVERT vs HALT. Top-level gas_left semantics
      differ, but state gas refund must agree per the updated EIP.
    - `spill_mode`: `no_spill` sizes the reservoir to cover all state
      gas charges. `spill` shrinks it so charges drain into gas_left,
      exercising the spill-refund-on-halt rule.
    - `frame_op`: `call` chains via CALL with no per-frame pre-charge.
      `create` chains via CREATE, where each level pre-charges
      `STATE_BYTES_PER_NEW_ACCOUNT * cpsb` and exercises
      credit-on-failure interleaved with the spill.

    Refunds are LIFO. On REVERT every state gas charge (body charges,
    spilled portions, and CREATE pre-charges) is refilled, the spill
    landing back in `gas_left`, so the user pays only execution charges
    plus intrinsic. On HALT the LIFO refill returns spilled state gas
    to `gas_left`, which is then zeroed, so only the start reservoir
    survives and the user pays `tx_gas - reservoir = gas_limit_cap`,
    regardless of spill axis or CREATE pre-charges.

    Two assertions cross-check the gas accounting:
    - `cumulative_gas_used` (receipt) pins `tx.gas - gas_left -
      state_gas_left`, catching bugs in the leftover split.
    - `header.gas_used` pins `max(block_execution, block_state)` via
      the block accumulators.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    new_account_state_gas = Op.CREATE(account_new=True).state_cost(fork)
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

    sum_execution = sum(code.execution_cost(fork) for code in frame_codes)
    if failure_mode == "halt":
        # LIFO refill returns spilled state gas (and spilled CREATE
        # pre-charges) to gas_left, which halt then zeros. Only the
        # start reservoir survives.
        expected_cumulative = tx_gas - reservoir
        assert expected_cumulative == gas_limit_cap
        # Header: all gas_left (including the refilled spill) is
        # consumed as execution. Block state gas is zero for plain
        # frames.
        expected_header_gas_used = gas_limit_cap
    elif failure_mode == "revert":
        # Revert preserves gas_left, full state gas refund, so the
        # user pays only execution costs plus intrinsic.
        expected_cumulative = intrinsic_cost + sum_execution
        # Header reflects the execution-vs-state attribution directly:
        # state_gas_used is zeroed by the tx error handler, so only
        # execution gas usage shows up.
        expected_header_gas_used = intrinsic_cost + sum_execution
    else:
        raise ValueError("Invariant, unreachable code.")

    tx = Transaction(
        to=top,
        state_gas_reservoir=reservoir,
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


@pytest.mark.parametrize(
    "refund_scenario",
    [
        pytest.param("sstore_restoration", id="sstore_restoration"),
        pytest.param("create_collision", id="create_collision"),
        pytest.param("create_initcode_revert", id="create_initcode_revert"),
        pytest.param("auth_existing_leaf", id="auth_existing_leaf"),
    ],
)
@pytest.mark.parametrize(
    "depth",
    [1, 3, 10],
)
@pytest.mark.parametrize(
    "consume_at",
    [
        pytest.param("deepest", id="consume_deepest"),
        pytest.param("top", id="consume_top"),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.valid_from("EIP8037")
def test_nested_state_gas_refund_consumed_at_depth(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    refund_scenario: str,
    depth: int,
    consume_at: str,
) -> None:
    """
    Verify no state gas credit routes to the reservoir under LIFO refills.

    Refund sources SSTORE `0->1->0`, CREATE collision, and CREATE
    initcode revert all refund LIFO, so the credit returns to
    `gas_left`, not the reservoir. Under EIP-2780 a SetCode auth on an
    `existing_leaf` authority no longer over-charges and refunds: it
    charges only ``AUTH_BASE`` at the top frame, crediting nothing back.

    A probe CALL sized one short of covering an SSTORE forwards a fixed
    gas to a sub-call, so it can only observe the reservoir, never a
    `gas_left` refund. With no scenario crediting the reservoir the probe
    always OOGs and CALL returns 0. The auth scenario additionally pins
    the applied delegation via post-state, guarding against a regression
    that re-introduces a reservoir credit for existing-authority auths.
    """
    is_auth_scenario = refund_scenario == "auth_existing_leaf"

    probe_address = pre.deploy_contract(code=Op.SSTORE(0, 1))
    probe_gas = Op.SSTORE(0, 1).gas_cost(fork) - 1
    consumer_storage = Storage()
    # The probe forwards a fixed gas and can only see the reservoir. No
    # scenario credits the reservoir under EIP-2780 (SSTORE/CREATE refunds
    # land in gas_left LIFO; the existing-leaf auth incurs no refund), so
    # the sub-call OOGs and CALL returns 0 in every case.
    probe_label = "no_reservoir_credit_probe_must_fail"
    probe_result = 0
    consume_op = Op.SSTORE(
        consumer_storage.store_next(probe_result, probe_label),
        Op.CALL(gas=probe_gas, address=probe_address),
    )

    if refund_scenario == "sstore_restoration":
        refund_body = Op.SSTORE(0, 1) + Op.SSTORE.with_metadata(
            key_warm=True,
            original_value=0,
            current_value=1,
            new_value=0,
        )(0, 0)
    elif refund_scenario == "create_collision":
        refund_body = Op.POP(Op.CREATE(0, 0, 0))
    elif refund_scenario == "create_initcode_revert":
        revert_initcode = bytes(Op.REVERT(0, 0))
        refund_body = Om.MSTORE(revert_initcode, 0) + Op.POP(
            Op.CREATE(0, 0, len(revert_initcode))
        )
    elif is_auth_scenario:
        refund_body = Bytecode()
    else:
        raise ValueError(f"unknown refund_scenario: {refund_scenario!r}")

    deepest_body = refund_body
    if consume_at == "deepest":
        deepest_body = deepest_body + consume_op
    elif consume_at != "top":
        raise ValueError(f"unknown consume_at: {consume_at!r}")

    deepest_address = pre.deploy_contract(code=deepest_body + Op.STOP)
    if refund_scenario == "create_collision":
        # Deepest is reached via plain CALL, so the CREATE's sender is
        # deepest itself with nonce 1 (fresh `deploy_contract` default).
        collision_target = compute_create_address(
            address=deepest_address, nonce=1
        )
        pre.deploy_contract(code=Op.STOP, address=collision_target)

    chain_inner = deepest_address
    for _ in range(depth):
        chain_inner = pre.deploy_contract(
            code=Op.POP(Op.CALL(gas=Op.GAS, address=chain_inner)) + Op.STOP
        )

    top_body = Op.POP(Op.CALL(gas=Op.GAS, address=chain_inner))
    if consume_at == "top":
        top_body = top_body + consume_op
    top = pre.deploy_contract(code=top_body + Op.STOP)

    authorization_list = None
    extra_post: dict = {}
    if is_auth_scenario:
        signer = pre.fund_eoa()
        auth_target = pre.deploy_contract(code=Op.STOP)
        authorization_list = [
            AuthorizationTuple(
                address=auth_target,
                nonce=0,
                signer=signer,
            ),
        ]
        extra_post[signer] = Account(
            nonce=1,
            code=Spec7702.delegation_designation(auth_target),
        )

    tx = Transaction(
        to=top,
        state_gas_reservoir=0,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
    )

    consumer_address = deepest_address if consume_at == "deepest" else top
    post: dict = {consumer_address: Account(storage=consumer_storage)}
    post.update(extra_post)
    state_test(pre=pre, post=post, tx=tx)


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
    execution work, but is one gas short of the MCOPY execution cost. The
    frame halts before frame-end settlement runs, so the earlier SSTORE
    never contributes execution state gas to refund.
    """
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    code = Op.SSTORE(0, 1) + Op.MCOPY(
        0x1000,
        0,
        1,
        old_memory_size=0,
        new_memory_size=0x1001,
        data_size=1,
    )
    contract = pre.deploy_contract(code=code)

    # One gas short of the execution-gas portion of successful execution.
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
def test_access_list_gas_is_execution_not_state(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    num_access_list_entries: int,
    slots_per_entry: int,
) -> None:
    """Verify EIP-2930 access list gas counts as execution, not state."""
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
def test_access_list_warm_savings_stay_execution(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Verify access-list warm savings stay in execution gas."""
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

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

    tx = Transaction(
        to=contract,
        state_gas_reservoir=sstore_state_gas,
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
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

    # `bytecode.gas_cost(fork)` sums each opcode's execution and state
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
        state_gas_reservoir=legit_state_cost,
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
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

    expected_cumulative = (
        intrinsic_cost
        + top_code.gas_cost(fork)
        + reverter_code.gas_cost(fork)
        + sum(c.gas_cost(fork) for c in pass_codes)
        + inner_code.gas_cost(fork)
    )

    tx = Transaction(
        to=top,
        state_gas_reservoir=legit_state_cost,
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
    "spill_mode",
    [
        pytest.param("no_spill", id="no_spill"),
        pytest.param("spill", id="spill"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_subcall_set_clear_revert_pays_no_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    spill_mode: str,
) -> None:
    """
    A child frame doing SSTORE 0 to x to 0 then REVERT must bill the
    sender only intrinsic + execution costs.

    Both SSTOREs roll back with the REVERT, so the matching
    state-gas charge and refund cancel cleanly. The receipt's
    `cumulative_gas_used` equals the execution baseline; a leftover
    `sstore_state_gas` would surface a double-charge at the failure
    boundary.

    `spill_mode` toggles whether the set draws from the reservoir
    directly (`no_spill`, reservoir sized to `sstore_state_gas`) or
    spills into `gas_left` (`spill`, reservoir = 0).
    """
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

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
    inner_code = set_op + clear_op + Op.REVERT(0, 0)
    inner = pre.deploy_contract(code=inner_code)

    top_code = Op.POP(Op.CALL(gas=Op.GAS, address=inner)) + Op.STOP
    top = pre.deploy_contract(code=top_code)

    reservoir = 0 if spill_mode == "spill" else sstore_state_gas

    expected_cumulative = (
        intrinsic_cost
        + top_code.execution_cost(fork)
        + inner_code.execution_cost(fork)
    )

    tx = Transaction(
        to=top,
        state_gas_reservoir=reservoir,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative,
        ),
    )
    state_test(
        pre=pre,
        post={top: Account(), inner: Account(storage={0: 0})},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_cumulative),
    )
