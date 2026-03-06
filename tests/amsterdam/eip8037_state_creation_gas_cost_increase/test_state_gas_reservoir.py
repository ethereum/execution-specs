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
)
from execution_testing.checklists import EIPChecklist

from .spec import Spec, ref_spec_8037

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
@pytest.mark.valid_from("Amsterdam")
def test_reservoir_allocation_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    gas_limit_delta: int,
) -> None:
    """
    Test state gas reservoir allocation at TX_MAX_GAS_LIMIT boundary.

    When tx.gas <= TX_MAX_GAS_LIMIT, all execution gas fits in gas_left
    and the reservoir is zero. When tx.gas > TX_MAX_GAS_LIMIT, the
    excess goes to the reservoir. In all cases, an SSTORE should
    succeed because state gas can spill from gas_left.
    """
    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    tx = Transaction(
        to=contract,
        gas_limit=Spec.TX_MAX_GAS_LIMIT + gas_limit_delta,
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
@pytest.mark.valid_from("Amsterdam")
def test_sstore_state_gas_source(
    state_test: StateTestFiller,
    pre: Alloc,
    num_sstores: int,
    reservoir_covers_state_gas: bool,
) -> None:
    """
    Test SSTORE zero-to-nonzero drawing state gas from different sources.

    When reservoir_covers_state_gas is True, enough gas is provided above
    TX_MAX_GAS_LIMIT to cover all SSTORE state gas from the reservoir.
    When False, the reservoir is minimal (1 gas unit) and state gas must
    spill into gas_left.
    """
    env = Environment()
    cpsb = Spec.COST_PER_STATE_BYTE
    sstore_state_gas = Spec.STATE_BYTES_PER_STORAGE_SET * cpsb

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
        gas_limit=Spec.TX_MAX_GAS_LIMIT + extra_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
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
        gas_limit=Spec.TX_MAX_GAS_LIMIT,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.valid_from("Amsterdam")
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
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, 1),
    )

    # Enough for intrinsic + warm SSTORE regular gas, but not the
    # state gas cost for zero-to-nonzero transition
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    gas_limit = intrinsic_cost() + Spec.GAS_STORAGE_UPDATE

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
@pytest.mark.valid_from("Amsterdam")
def test_block_regular_gas_limit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    exceed_block_gas_limit: bool,
) -> None:
    """
    Test check_transaction enforcement of regular gas against block limit.

    The regular gas check uses min(TX_MAX_GAS_LIMIT, tx.gas).
    Fill the block with transactions at TX_MAX_GAS_LIMIT and verify
    the last one is accepted or rejected based on remaining capacity.
    """
    env = Environment()
    tx_count = env.gas_limit // Spec.TX_MAX_GAS_LIMIT

    gas_spender = pre.deploy_contract(code=Op.INVALID)

    total_txs = tx_count + int(exceed_block_gas_limit)
    block = Block(
        txs=[
            Transaction(
                to=gas_spender,
                sender=pre.fund_eoa(),
                gas_limit=Spec.TX_MAX_GAS_LIMIT,
                error=TransactionException.GAS_ALLOWANCE_EXCEEDED
                if i >= tx_count
                else None,
            )
            for i in range(total_txs)
        ],
        exception=TransactionException.GAS_ALLOWANCE_EXCEEDED
        if exceed_block_gas_limit
        else None,
    )

    blockchain_test(pre=pre, post={}, blocks=[block])


@pytest.mark.parametrize(
    "exceed_block_gas_limit",
    [
        pytest.param(True, marks=pytest.mark.exception_test),
        pytest.param(False),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_block_state_gas_limit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    exceed_block_gas_limit: bool,
) -> None:
    """
    Test check_transaction enforcement of state gas against block limit.

    The block-level state gas check compares tx.gas against remaining
    state gas capacity. The first tx performs an SSTORE (consuming
    state gas from its reservoir), which increases block_state_gas_used.
    A second tx with gas_limit equal to block_gas_limit then exceeds
    the remaining state gas capacity.
    """
    env = Environment()
    high_gas = env.gas_limit

    # Contract that performs a single SSTORE (consumes state gas)
    state_gas_spender = pre.deploy_contract(
        code=Op.SSTORE(0, 1),
    )

    txs = [
        Transaction(
            to=state_gas_spender,
            sender=pre.fund_eoa(),
            gas_limit=high_gas,
        ),
    ]

    if exceed_block_gas_limit:
        txs.append(
            Transaction(
                to=state_gas_spender,
                sender=pre.fund_eoa(),
                gas_limit=high_gas,
                error=TransactionException.GAS_ALLOWANCE_EXCEEDED,
            ),
        )

    block = Block(
        txs=txs,
        exception=TransactionException.GAS_ALLOWANCE_EXCEEDED
        if exceed_block_gas_limit
        else None,
    )

    blockchain_test(pre=pre, post={}, blocks=[block])


@pytest.mark.valid_from("Amsterdam")
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


@pytest.mark.valid_from("Amsterdam")
def test_block_gas_used_with_state_ops(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test block gas_used includes state gas contribution.

    A transaction performing SSTORE zero-to-nonzero contributes to both
    block_gas_used and block_state_gas_used. The block header gas_used
    is max(block_gas_used, block_state_gas_used).
    """
    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    tx = Transaction(
        to=contract,
        gas_limit=Spec.TX_MAX_GAS_LIMIT,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post={contract: Account(storage=storage)},
    )


@pytest.mark.parametrize(
    "gas_above_cap",
    [
        pytest.param(True, id="state_gas_from_reservoir"),
        pytest.param(False, id="state_gas_from_gas_left"),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_create_tx_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    gas_above_cap: bool,
) -> None:
    """
    Test contract creation with state gas from reservoir or gas_left.

    Contract creation charges intrinsic state gas for the new account
    (new-account state gas). When gas_above_cap is True, extra gas
    beyond TX_MAX_GAS_LIMIT feeds the reservoir. When False, all state
    gas comes from gas_left (reservoir is zero).
    """
    init_code = Op.STOP

    env = Environment()
    cpsb = Spec.COST_PER_STATE_BYTE
    create_state_gas = Spec.STATE_BYTES_PER_NEW_ACCOUNT * cpsb

    if gas_above_cap:
        gas_limit = Spec.TX_MAX_GAS_LIMIT + create_state_gas
    else:
        gas_limit = Spec.TX_MAX_GAS_LIMIT

    tx = Transaction(
        to=None,
        data=init_code,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)
