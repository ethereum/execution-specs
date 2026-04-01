"""
Test block-level two-dimensional gas accounting under EIP-8037.

Verify that the block header gas_used equals
max(block_regular_gas_used, block_state_gas_used) across
single-block, multi-block, and mixed-transaction scenarios.

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
    Storage,
    Transaction,
)

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


def sstore_tx_gas(fork: Fork, num_sstores: int = 1) -> tuple[int, int]:
    """Return (regular, state) gas for a tx with N cold SSTOREs."""
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()
    evm_total = num_sstores * Op.SSTORE(0, 1).gas_cost(fork)
    state = num_sstores * fork.sstore_state_gas()
    return intrinsic_gas + evm_total - state, state


def sstore_txs(
    pre: Alloc,
    fork: Fork,
    n: int,
    num_sstores: int = 1,
    tx_gas_limit: int | None = None,
) -> tuple[list[Transaction], dict]:
    """Build n txs each doing num_sstores zero-to-nonzero SSTOREs."""
    if tx_gas_limit is None:
        gas_limit_cap = fork.transaction_gas_limit_cap()
        assert gas_limit_cap is not None
        tx_gas_limit = gas_limit_cap + num_sstores * fork.sstore_state_gas()
    txs, post = [], {}
    for _ in range(n):
        storage = Storage()
        code = Bytecode(Op.STOP)
        for _ in range(num_sstores):
            code = Op.SSTORE(storage.store_next(1), 1) + code
        contract = pre.deploy_contract(code=code)
        txs.append(
            Transaction(
                to=contract,
                gas_limit=tx_gas_limit,
                sender=pre.fund_eoa(),
            )
        )
        post[contract] = Account(storage=storage)
    return txs, post


def stop_txs(pre: Alloc, fork: Fork, n: int) -> list[Transaction]:
    """Build n STOP transactions."""
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()
    txs = []
    for _ in range(n):
        contract = pre.deploy_contract(code=Op.STOP)
        txs.append(
            Transaction(
                to=contract,
                gas_limit=intrinsic_gas,
                sender=pre.fund_eoa(),
            )
        )
    return txs


@pytest.mark.parametrize(
    "num_txs,num_sstores",
    [
        pytest.param(5, 1, id="single_sstore"),
        pytest.param(20, 1, id="single_sstore_many_txs"),
        pytest.param(2, 3, id="multi_sstore_spillover"),
        pytest.param(10, 5, id="multi_sstore_many_txs"),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_block_gas_used_state_dominates(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    num_txs: int,
    num_sstores: int,
) -> None:
    """
    Verify block.gas_used = block_state_gas when state > regular.

    Each tx performs zero-to-nonzero SSTOREs. Since state gas per
    SSTORE exceeds regular gas, block_state_gas exceeds
    block_regular_gas and becomes the header gas_used.

    The spillover variant provides reservoir for only one SSTORE
    per tx; the remaining state gas spills into gas_left.
    Block-level accounting must still separate the two dimensions.
    """
    tx_regular, tx_state = sstore_tx_gas(fork, num_sstores)
    block_regular = num_txs * tx_regular
    block_state = num_txs * tx_state
    assert block_state > block_regular

    txs, post = sstore_txs(
        pre,
        fork,
        num_txs,
        num_sstores=num_sstores,
    )
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                header_verify=Header(gas_used=block_state),
            )
        ],
        post=post,
    )


@pytest.mark.valid_from("Amsterdam")
def test_block_gas_used_regular_dominates(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify block.gas_used = block_regular_gas when state gas is zero.

    A block containing only STOP transactions to existing contracts
    produces no state gas. The block header gas_used must equal the
    sum of regular gas across all transactions, since
    max(regular, 0) = regular.
    """
    num_txs = 3
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()
    txs = stop_txs(pre, fork, num_txs)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                header_verify=Header(gas_used=num_txs * intrinsic_gas),
            )
        ],
        post={},
    )


@pytest.mark.parametrize(
    "num_stop,num_sstore,interleaved",
    [
        pytest.param(2, 3, False, id="grouped"),
        pytest.param(10, 10, True, id="interleaved"),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_block_gas_used_mixed_txs(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    num_stop: int,
    num_sstore: int,
    interleaved: bool,
) -> None:
    """
    Verify block.gas_used with mixed STOP and SSTORE transactions.

    STOP txs contribute only regular gas; SSTORE txs contribute both.
    The interleaved variant alternates SSTORE/STOP to test that
    non-contiguous state gas contributions accumulate correctly.
    """
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()
    tx_regular_sstore, tx_state_sstore = sstore_tx_gas(fork)

    block_regular = num_stop * intrinsic_gas + num_sstore * tx_regular_sstore
    block_state = num_sstore * tx_state_sstore
    expected = max(block_regular, block_state)

    txs_sstore, post = sstore_txs(pre, fork, num_sstore)
    txs_stop = stop_txs(pre, fork, num_stop)

    if interleaved:
        txs = []
        for i in range(max(num_sstore, num_stop)):
            if i < num_sstore:
                txs.append(txs_sstore[i])
            if i < num_stop:
                txs.append(txs_stop[i])
    else:
        txs = txs_stop + txs_sstore

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                header_verify=Header(gas_used=expected),
            )
        ],
        post=post,
    )


@pytest.mark.valid_from("Amsterdam")
def test_block_gas_refund_eip7778_no_block_reduction(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify block gas accounting excludes refunds per EIP-7778.

    Each tx does SSTORE(0,1) then SSTORE(0,0), set then restore.
    The user gets a refund (reduced receipt gas_used), but EIP-7778
    says block gas is NOT reduced by refunds.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    num_txs = 3
    # Set then restore: second SSTORE is warm with current_value=1
    code = Op.SSTORE(0, 1) + Op.SSTORE.with_metadata(
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )(0, 0)
    tx_regular = intrinsic_gas + code.gas_cost(fork) - sstore_state_gas
    expected = max(num_txs * tx_regular, num_txs * sstore_state_gas)
    txs = []
    for _ in range(num_txs):
        contract = pre.deploy_contract(code=code)
        txs.append(
            Transaction(
                to=contract,
                gas_limit=gas_limit_cap + sstore_state_gas,
                sender=pre.fund_eoa(),
            )
        )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                header_verify=Header(gas_used=expected),
            )
        ],
        post={},
    )


@pytest.mark.parametrize(
    "num_txs,num_sstores",
    [
        pytest.param(5, 1, id="single_sstore"),
        pytest.param(20, 1, id="single_sstore_many_txs"),
        pytest.param(10, 5, id="multi_sstore_many_txs"),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_block_2d_gas_boundary_exact_fit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    num_txs: int,
    num_sstores: int,
) -> None:
    """
    Verify a block is valid when max(regular, state) == gas_limit.

    Set block_gas_limit = block_state_gas (the dominant dimension).
    Clients that sum regular + state will reject this valid block.
    """
    tx_regular, tx_state = sstore_tx_gas(fork, num_sstores)
    block_state = num_txs * tx_state
    block_gas_limit = block_state

    # tx_limit must exceed tx_regular + tx_state so the tx is valid,
    # but the per-tx regular reservation against block gas must still
    # leave room for all txs.
    tx_limit = tx_regular + tx_state + tx_regular // 10
    worst = block_gas_limit - (num_txs - 1) * tx_regular
    assert worst >= tx_limit, "per-tx regular gas check fails"

    txs, post = sstore_txs(
        pre,
        fork,
        num_txs,
        num_sstores=num_sstores,
        tx_gas_limit=tx_limit,
    )
    blockchain_test(
        genesis_environment=Environment(
            gas_limit=block_gas_limit,
        ),
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                gas_limit=block_gas_limit,
                header_verify=Header(gas_used=block_gas_limit),
            )
        ],
        post=post,
    )


@pytest.mark.valid_from("Amsterdam")
def test_block_gas_used_call_new_account(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify block.gas_used includes state gas from CALL creating accounts.

    A contract does CALL(value=1) to a non-existent address (charges
    GAS_NEW_ACCOUNT state gas) then SSTORE. Combined with a STOP tx,
    the 2D max must reflect state gas from account creation.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    new_account_state_gas = fork.gas_costs().GAS_NEW_ACCOUNT
    sstore_state_gas = fork.sstore_state_gas()

    target = pre.fund_eoa(amount=0)

    parent_storage = Storage()
    parent = pre.deploy_contract(
        code=(
            Op.CALL(gas=100_000, address=target, value=1)
            + Op.SSTORE(parent_storage.store_next(1), 1)
        ),
        balance=10**18,
    )

    txs = [
        Transaction(
            to=parent,
            gas_limit=(
                gas_limit_cap + new_account_state_gas + sstore_state_gas
            ),
            sender=pre.fund_eoa(),
        ),
    ] + stop_txs(pre, fork, 1)

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        post={parent: Account(storage=parent_storage)},
    )


@pytest.mark.valid_from("Amsterdam")
def test_block_gas_used_create_tx(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify block.gas_used includes intrinsic state gas from CREATE txs.

    Contract creation charges GAS_NEW_ACCOUNT as intrinsic state gas.
    Combined with a STOP tx, verify the 2D max is correct.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    create_state_gas = fork.create_state_gas(code_size=0)

    init_code = bytes(Op.STOP)
    create_regular = (
        intrinsic_calc(
            calldata=init_code,
            contract_creation=True,
        )
        - create_state_gas
    )
    stop_regular = intrinsic_calc()

    expected = max(create_regular + stop_regular, create_state_gas)

    txs = [
        Transaction(
            to=None,
            data=init_code,
            gas_limit=gas_limit_cap + create_state_gas,
            sender=pre.fund_eoa(),
        ),
    ] + stop_txs(pre, fork, 1)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                header_verify=Header(gas_used=expected),
            )
        ],
        post={},
    )


@pytest.mark.valid_from("Amsterdam")
def test_multi_block_dimension_flip(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify gas_used across blocks where dominant dimension flips.

    Block 1: STOP txs only (regular dominates).
    Block 2: SSTORE txs only (state dominates).
    Each block independently computes its own 2D max.
    """
    n = 3
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()
    tx_regular, tx_state = sstore_tx_gas(fork)

    block_1 = stop_txs(pre, fork, n)
    block_2, post_2 = sstore_txs(pre, fork, n)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=block_1,
                header_verify=Header(gas_used=n * intrinsic_gas),
            ),
            Block(
                txs=block_2,
                header_verify=Header(
                    gas_used=max(n * tx_regular, n * tx_state),
                ),
            ),
        ],
        post=post_2,
    )
