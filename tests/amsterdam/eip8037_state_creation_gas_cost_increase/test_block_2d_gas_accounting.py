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
    TransactionException,
    TransactionReceipt,
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
@pytest.mark.valid_from("EIP8037")
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


@pytest.mark.valid_from("EIP8037")
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
@pytest.mark.valid_from("EIP8037")
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


@pytest.mark.valid_from("EIP8037")
def test_block_gas_refund_eip7778_no_block_reduction(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify block gas accounting for SSTORE 0→x→0 refund paths.

    Regular gas refund via `refund_counter` does NOT reduce block gas
    (EIP-7778). State gas refund goes to the reservoir and DOES reduce
    `block_state_gas_used` (net zero state growth).
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
    expected = num_txs * tx_regular
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
@pytest.mark.valid_from("EIP8037")
def test_block_2d_gas_boundary_exact_fit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    num_txs: int,
    num_sstores: int,
) -> None:
    """
    Verify a block is valid when state gas dominates regular gas.

    Clients that sum regular + state will reject this valid block.
    """
    tx_regular, tx_state = sstore_tx_gas(fork, num_sstores)
    intrinsic_regular = fork.transaction_intrinsic_cost_calculator()()

    tx_limit = tx_regular + tx_state + tx_regular // 10

    # Per-tx worst-case state contribution: tx.gas - intrinsic_regular.
    # The block_gas_limit must leave enough state budget for every tx.
    worst_state_per_tx = tx_limit - intrinsic_regular
    block_gas_limit = max(
        # Regular dimension: last tx must fit.
        (num_txs - 1) * tx_regular + tx_limit,
        # State dimension: cumulative worst-case must fit.
        num_txs * worst_state_per_tx,
    )

    block_regular = num_txs * tx_regular
    block_state = num_txs * tx_state
    expected_gas_used = max(block_regular, block_state)

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
                header_verify=Header(gas_used=expected_gas_used),
            )
        ],
        post=post,
    )


@pytest.mark.valid_from("EIP8037")
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


@pytest.mark.valid_from("EIP8037")
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


@pytest.mark.valid_from("EIP8037")
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


@pytest.mark.exception_test
@pytest.mark.valid_from("EIP8037")
def test_tx_rejected_when_regular_gas_exceeds_block_limit_small(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Reject a small-gas tx whose regular gas overflows the block."""
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    block_gas_limit = intrinsic_gas * 2

    filler = pre.deploy_contract(code=Op.STOP)
    filler_tx = Transaction(
        to=filler,
        gas_limit=intrinsic_gas,
        sender=pre.fund_eoa(),
    )

    rejected_gas_limit = intrinsic_gas + 1
    assert rejected_gas_limit < gas_limit_cap
    rejected = pre.deploy_contract(code=Op.STOP)
    rejected_tx = Transaction(
        to=rejected,
        gas_limit=rejected_gas_limit,
        sender=pre.fund_eoa(),
        error=TransactionException.GAS_ALLOWANCE_EXCEEDED,
    )

    blockchain_test(
        genesis_environment=Environment(gas_limit=block_gas_limit),
        pre=pre,
        blocks=[
            Block(
                txs=[filler_tx, rejected_tx],
                gas_limit=block_gas_limit,
                exception=TransactionException.GAS_ALLOWANCE_EXCEEDED,
            )
        ],
        post={},
    )


@pytest.mark.parametrize(
    "tx2_gas_limit_equals_block_gas_limit",
    [
        pytest.param(True, id="tx_gas_limit_equals_block_limit"),
        pytest.param(False, id="tx_gas_limit_just_above_remaining"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_block_2d_gas_tx_gas_limit_exceeds_regular_remaining(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    tx2_gas_limit_equals_block_gas_limit: bool,
) -> None:
    """
    Verify a block is valid when a later tx's gas_limit exceeds the
    regular budget remaining but its capped regular contribution fits.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()
    env = Environment()
    block_gas_limit = int(env.gas_limit)

    if tx2_gas_limit_equals_block_gas_limit:
        tx2_gas_limit = block_gas_limit
    else:
        tx2_gas_limit = block_gas_limit - intrinsic_gas + 1

    assert tx2_gas_limit > gas_limit_cap
    assert tx2_gas_limit > block_gas_limit - intrinsic_gas

    stop_contract = pre.deploy_contract(code=Op.STOP)

    storage = Storage()
    sstore_contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    tx1_regular = intrinsic_gas
    tx2_regular, tx2_state = sstore_tx_gas(fork)
    expected_gas_used = max(tx1_regular + tx2_regular, tx2_state)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        to=stop_contract,
                        gas_limit=intrinsic_gas,
                        sender=pre.fund_eoa(),
                    ),
                    Transaction(
                        to=sstore_contract,
                        gas_limit=tx2_gas_limit,
                        sender=pre.fund_eoa(),
                    ),
                ],
                header_verify=Header(gas_used=expected_gas_used),
            ),
        ],
        post={sstore_contract: Account(storage=storage)},
    )


@pytest.mark.valid_from("EIP8037")
def test_receipt_cumulative_differs_from_header_gas_used(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify receipt cumulative_gas_used can diverge from header
    gas_used under 2D accounting when state gas dominates.
    """
    tx_regular, tx_state = sstore_tx_gas(fork)
    num_txs = 3

    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    tx_gas_limit = gas_limit_cap + fork.sstore_state_gas()
    per_tx_gas_used = tx_regular + tx_state

    txs: list[Transaction] = []
    post: dict = {}
    for i in range(num_txs):
        storage = Storage()
        contract = pre.deploy_contract(
            code=Op.SSTORE(storage.store_next(1), 1) + Op.STOP,
        )
        txs.append(
            Transaction(
                to=contract,
                gas_limit=tx_gas_limit,
                sender=pre.fund_eoa(),
                expected_receipt=TransactionReceipt(
                    cumulative_gas_used=(i + 1) * per_tx_gas_used,
                ),
            )
        )
        post[contract] = Account(storage=storage)

    block_regular = num_txs * tx_regular
    block_state = num_txs * tx_state
    header_gas_used = max(block_regular, block_state)

    assert block_state > block_regular
    assert header_gas_used < num_txs * per_tx_gas_used

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                header_verify=Header(gas_used=header_gas_used),
            ),
        ],
        post=post,
    )
