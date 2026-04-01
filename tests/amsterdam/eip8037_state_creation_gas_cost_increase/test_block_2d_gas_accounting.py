"""
Block-level 2D gas accounting tests for EIP-8037.

EIP-8037 introduces two-dimensional gas metering: each transaction
contributes to both ``block_gas_used`` (regular gas) and
``block_state_gas_used`` (state gas).  The block header's ``gas_used``
field is ``max(block_gas_used, block_state_gas_used)``.

These tests target inter-client disagreements observed on BAL devnet-3.

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


# -- Helpers --


def _sstore_tx_gas(fork, num_sstores=1):
    """Return (regular, state) gas for a tx with N SSTOREs."""
    gc = fork.gas_costs()
    evm = num_sstores * (
        2 * gc.GAS_VERY_LOW + gc.GAS_COLD_STORAGE_WRITE
    )
    state = num_sstores * fork.sstore_state_gas()
    return gc.GAS_TX_BASE + evm, state


def _stop_tx_gas(fork):
    """Return per-tx regular gas for a STOP transaction."""
    return fork.transaction_intrinsic_cost_calculator()()


def _make_sstore_txs(pre, fork, n, num_sstores=1,
                     tx_gas_limit=None):
    """
    Build n txs each doing num_sstores zero-to-nonzero SSTOREs.

    Return (txs, post).
    """
    if tx_gas_limit is None:
        cap = fork.transaction_gas_limit_cap()
        assert cap is not None
        tx_gas_limit = (
            cap + num_sstores * fork.sstore_state_gas()
        )
    txs, post = [], {}
    for _ in range(n):
        storage = Storage()
        code = Bytecode()
        for _ in range(num_sstores):
            code += Op.SSTORE(storage.store_next(1), 1)
        contract = pre.deploy_contract(code=code)
        txs.append(Transaction(
            to=contract,
            gas_limit=tx_gas_limit,
            max_priority_fee_per_gas=1,
            max_fee_per_gas=8,
            sender=pre.fund_eoa(),
        ))
        post[contract] = Account(storage=storage)
    return txs, post


def _make_stop_txs(pre, fork, n):
    """Build n STOP transactions. Return list of txs."""
    gas = _stop_tx_gas(fork)
    txs = []
    for _ in range(n):
        contract = pre.deploy_contract(code=Op.STOP)
        txs.append(Transaction(
            to=contract,
            gas_limit=gas,
            max_priority_fee_per_gas=1,
            max_fee_per_gas=8,
            sender=pre.fund_eoa(),
        ))
    return txs


# -- Tests --


@pytest.mark.parametrize(
    "num_txs,num_sstores",
    [
        pytest.param(5, 1, id="5tx_1sstore"),
        pytest.param(20, 1, id="20tx_1sstore"),
        pytest.param(2, 3, id="2tx_3sstore_spillover"),
        pytest.param(10, 5, id="10tx_5sstore"),
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

    Each tx does ``num_sstores`` zero-to-nonzero SSTOREs.  Since
    state gas per SSTORE exceeds regular gas, block_state_gas exceeds
    block_regular_gas and becomes the header gas_used.

    The spillover variant (2tx_3sstore) provides reservoir for only
    one SSTORE per tx; the remaining state gas spills into gas_left.
    Block-level accounting must still separate the two dimensions.

    Catches: clients ignoring state gas, summing instead of max,
    or conflating spillover gas with the regular dimension.
    """
    tx_regular, tx_state = _sstore_tx_gas(fork, num_sstores)
    block_regular = num_txs * tx_regular
    block_state = num_txs * tx_state
    assert block_state > block_regular
    expected = block_state

    txs, post = _make_sstore_txs(
        pre, fork, num_txs, num_sstores=num_sstores,
    )
    blockchain_test(
        pre=pre,
        blocks=[Block(
            txs=txs,
            header_verify=Header(gas_used=expected),
        )],
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

    STOP transactions to existing contracts produce no state gas.
    """
    num_txs = 3
    stop_gas = _stop_tx_gas(fork)
    txs = _make_stop_txs(pre, fork, num_txs)

    blockchain_test(
        pre=pre,
        blocks=[Block(
            txs=txs,
            header_verify=Header(gas_used=num_txs * stop_gas),
        )],
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
    tx_r_sstore, tx_s_sstore = _sstore_tx_gas(fork)
    stop_gas = _stop_tx_gas(fork)

    block_regular = (
        num_stop * stop_gas + num_sstore * tx_r_sstore
    )
    block_state = num_sstore * tx_s_sstore
    expected = max(block_regular, block_state)

    sstore_txs, post = _make_sstore_txs(pre, fork, num_sstore)
    stop_txs = _make_stop_txs(pre, fork, num_stop)

    if interleaved:
        txs = []
        for i in range(max(num_sstore, num_stop)):
            if i < num_sstore:
                txs.append(sstore_txs[i])
            if i < num_stop:
                txs.append(stop_txs[i])
    else:
        txs = stop_txs + sstore_txs

    blockchain_test(
        pre=pre,
        blocks=[Block(
            txs=txs,
            header_verify=Header(gas_used=expected),
        )],
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

    Each tx does SSTORE(0,1) then SSTORE(0,0) — set then restore.
    The user gets a refund (reduced receipt gas_used), but EIP-7778
    says block gas is NOT reduced by refunds.
    """
    gc = fork.gas_costs()
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None
    sstore_state_gas = fork.sstore_state_gas()

    num_txs = 3
    tx_regular = (
        gc.GAS_TX_BASE
        + 4 * gc.GAS_VERY_LOW
        + gc.GAS_COLD_STORAGE_WRITE
        + gc.GAS_WARM_SLOAD
    )
    tx_state = sstore_state_gas
    expected = max(num_txs * tx_regular, num_txs * tx_state)

    txs = []
    for _ in range(num_txs):
        contract = pre.deploy_contract(
            code=Op.SSTORE(0, 1) + Op.SSTORE(0, 0),
        )
        txs.append(Transaction(
            to=contract,
            gas_limit=cap + sstore_state_gas,
            max_priority_fee_per_gas=1,
            max_fee_per_gas=8,
            sender=pre.fund_eoa(),
        ))

    blockchain_test(
        pre=pre,
        blocks=[Block(
            txs=txs,
            header_verify=Header(gas_used=expected),
        )],
        post={},
    )


@pytest.mark.parametrize(
    "num_txs,num_sstores",
    [
        pytest.param(5, 1, id="5tx_1sstore"),
        pytest.param(20, 1, id="20tx_1sstore"),
        pytest.param(10, 5, id="10tx_5sstore"),
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
    tx_regular, tx_state = _sstore_tx_gas(fork, num_sstores)
    block_state = num_txs * tx_state
    block_gas_limit = block_state

    tx_limit = tx_regular + tx_state + 1000
    worst = block_gas_limit - (num_txs - 1) * tx_regular
    assert worst >= tx_limit, "per-tx regular gas check fails"

    txs, post = _make_sstore_txs(
        pre, fork, num_txs,
        num_sstores=num_sstores,
        tx_gas_limit=tx_limit,
    )
    blockchain_test(
        genesis_environment=Environment(
            gas_limit=block_gas_limit,
        ),
        pre=pre,
        blocks=[Block(
            txs=txs,
            gas_limit=block_gas_limit,
            header_verify=Header(gas_used=block_gas_limit),
        )],
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

    A contract does CALL(value=1) to a dead address (charges
    GAS_NEW_ACCOUNT state gas) then SSTORE.  Combined with a STOP tx,
    the 2D max must reflect state gas from account creation.
    """
    gc = fork.gas_costs()
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None
    sstore_state_gas = fork.sstore_state_gas()

    parent_storage = Storage()
    parent = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=500_000, address=0xDEAD0001, value=1,
            )
            + Op.SSTORE(parent_storage.store_next(1), 1)
        ),
        balance=10**18,
    )

    stop_contract = pre.deploy_contract(code=Op.STOP)
    stop_gas = _stop_tx_gas(fork)

    txs = [
        Transaction(
            to=parent,
            gas_limit=(
                cap + gc.GAS_NEW_ACCOUNT + sstore_state_gas
            ),
            max_priority_fee_per_gas=1,
            max_fee_per_gas=8,
            sender=pre.fund_eoa(),
        ),
        Transaction(
            to=stop_contract,
            gas_limit=stop_gas,
            max_priority_fee_per_gas=1,
            max_fee_per_gas=8,
            sender=pre.fund_eoa(),
        ),
    ]

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
    gc = fork.gas_costs()
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None

    init_code = bytes(Op.STOP)
    intrinsic = fork.transaction_intrinsic_cost_calculator()

    create_total = intrinsic(
        calldata=init_code, contract_creation=True,
    )
    create_state = gc.GAS_NEW_ACCOUNT
    create_regular = create_total - create_state

    stop_contract = pre.deploy_contract(code=Op.STOP)
    stop_gas = _stop_tx_gas(fork)

    expected = max(create_regular + stop_gas, create_state)

    txs = [
        Transaction(
            to=None,
            data=init_code,
            gas_limit=cap + create_state,
            max_priority_fee_per_gas=1,
            max_fee_per_gas=8,
            sender=pre.fund_eoa(),
        ),
        Transaction(
            to=stop_contract,
            gas_limit=stop_gas,
            max_priority_fee_per_gas=1,
            max_fee_per_gas=8,
            sender=pre.fund_eoa(),
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=[Block(
            txs=txs,
            header_verify=Header(gas_used=expected),
        )],
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
    stop_gas = _stop_tx_gas(fork)
    tx_regular, tx_state = _sstore_tx_gas(fork)

    block1_txs = _make_stop_txs(pre, fork, n)
    block2_txs, post = _make_sstore_txs(pre, fork, n)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=block1_txs,
                header_verify=Header(gas_used=n * stop_gas),
            ),
            Block(
                txs=block2_txs,
                header_verify=Header(
                    gas_used=max(
                        n * tx_regular, n * tx_state,
                    ),
                ),
            ),
        ],
        post=post,
    )

