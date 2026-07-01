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
    Hash,
    Header,
    Op,
    Storage,
    Transaction,
    TransactionException,
    TransactionReceipt,
    add_kzg_version,
)

from ...cancun.eip4844_blobs.spec import Spec as EIP4844_Spec
from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


def sstore_tx_gas(fork: Fork, num_sstores: int = 1) -> tuple[int, int]:
    """Return (regular, state) gas for a tx with N cold SSTOREs."""
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()
    evm_total = num_sstores * Op.SSTORE(0, 1).gas_cost(fork)
    state = num_sstores * Op.SSTORE(new_value=1).state_cost(fork)
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
        tx_gas_limit = gas_limit_cap + num_sstores * Op.SSTORE(
            new_value=1
        ).state_cost(fork)
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
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
                state_gas_reservoir=sstore_state_gas,
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
        pytest.param(1, 1, id="single_sstore_single_tx"),
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
    block_gas_limit = 30_000_000
    while True:
        # We have a circular dependency to calculate the block gas limit based
        # on the transactions required gas (tx gas increments as we increase
        # the block gas limit to fit). This loops tries incrementing the
        # block gas limit by consistent steps in order to find the minimum gas
        # allows the transactions required to fit.
        env = Environment(
            gas_limit=block_gas_limit,
        )
        tx_regular, tx_state = sstore_tx_gas(fork, num_sstores)
        intrinsic_regular = fork.transaction_intrinsic_cost_calculator()()

        tx_limit = tx_regular + tx_state + tx_regular // 10

        # Per-tx worst-case state contribution: tx.gas - intrinsic_regular.
        # The block_gas_limit must leave enough state budget for every tx.
        worst_state_per_tx = tx_limit - intrinsic_regular
        minimum_block_gas_limit = max(
            # Regular dimension: last tx must fit.
            (num_txs - 1) * tx_regular + tx_limit,
            # State dimension: cumulative worst-case must fit.
            num_txs * worst_state_per_tx,
        )
        if block_gas_limit >= minimum_block_gas_limit:
            break
        block_gas_limit += 1_000_000

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
        genesis_environment=env,
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
    new_account_state_gas = fork.gas_costs().NEW_ACCOUNT
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

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
            state_gas_reservoir=new_account_state_gas + sstore_state_gas,
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
            state_gas_reservoir=create_state_gas,
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


@pytest.mark.parametrize(
    "tx_gas_delta, expected_exception",
    [
        pytest.param(0, None, id="gas_equal"),
        pytest.param(
            1,
            TransactionException.GAS_ALLOWANCE_EXCEEDED,
            id="gas_one_above",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            2,
            TransactionException.GAS_ALLOWANCE_EXCEEDED,
            id="gas_two_above",
            marks=pytest.mark.exception_test,
        ),
    ],
)
@pytest.mark.parametrize(
    "block_gas_limit",
    [
        pytest.param(0x0FFFFFD, id="bgl_0x0fffffd"),
        pytest.param(0x01FFFFE, id="bgl_0x01ffffe"),
    ],
)
@pytest.mark.parametrize(
    "tx_type, contract_creation",
    [
        pytest.param(0, False, id="type_0_call"),
        pytest.param(0, True, id="type_0_create"),
        pytest.param(1, False, id="type_1_call"),
        pytest.param(1, True, id="type_1_create"),
        pytest.param(2, False, id="type_2_call"),
        pytest.param(2, True, id="type_2_create"),
        pytest.param(3, False, id="type_3_blob"),
        pytest.param(4, False, id="type_4_set_code"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_tx_gas_limit_block_boundary(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    tx_type: int,
    contract_creation: bool,
    block_gas_limit: int,
    tx_gas_delta: int,
    expected_exception: TransactionException | None,
) -> None:
    """
    Reject tx whose ``gas_limit`` exceeds the block ``gas_limit``.

    EIP-8037 inclusion rule: ``min(TX_MAX_GAS_LIMIT, tx.gas) <=
    regular_gas_available`` and ``tx.gas <= state_gas_available``.
    At block start both budgets equal ``block_gas_limit``.
    """
    gas_limit = block_gas_limit + tx_gas_delta
    gas_price = 10
    sender = pre.fund_eoa(amount=gas_limit * gas_price + 10**18)

    to = None if contract_creation else pre.fund_eoa(amount=0)
    access_list = None
    authorization_list = None
    blob_versioned_hashes = None
    extra_fee_args: dict = {}
    if tx_type == 1:
        access_list = [AccessList(address=Address(1), storage_keys=[Hash(0)])]
    elif tx_type == 2:
        access_list = []
    elif tx_type == 3:
        blob_versioned_hashes = add_kzg_version(
            [Hash(1)], EIP4844_Spec.BLOB_COMMITMENT_VERSION_KZG
        )
        extra_fee_args["max_fee_per_blob_gas"] = 1
    elif tx_type == 4:
        authorization_list = [
            AuthorizationTuple(
                signer=pre.fund_eoa(amount=0), address=Address(1)
            )
        ]

    if tx_type in (0, 1):
        fee_args: dict = {"gas_price": gas_price}
    else:
        fee_args = {
            "max_fee_per_gas": gas_price,
            "max_priority_fee_per_gas": 0,
        }
    fee_args.update(extra_fee_args)

    tx = Transaction(
        ty=tx_type,
        sender=sender,
        to=to,
        gas_limit=gas_limit,
        access_list=access_list,
        authorization_list=authorization_list,
        blob_versioned_hashes=blob_versioned_hashes,
        error=expected_exception,
        **fee_args,
    )

    blockchain_test(
        genesis_environment=Environment(gas_limit=block_gas_limit),
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                gas_limit=block_gas_limit,
                exception=expected_exception,
            )
        ],
        post={},
    )


@pytest.mark.parametrize(
    "delta",
    [
        pytest.param(0, id="exactly_fits"),
        pytest.param(1, id="exceeds", marks=pytest.mark.exception_test),
    ],
)
# Cumulative block-gas inclusion is a pre-existing rule, not an
# EIP-8037 novelty. Floor is Osaka only because the gas-cap guard
# below relies on EIP-7825's transaction_gas_limit_cap().
@pytest.mark.valid_from("Osaka")
def test_tx_inclusion_at_regular_gas_block_limit_small(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    delta: int,
) -> None:
    """
    Probe the regular-gas inclusion boundary with a small-gas tx.

    The second tx's ``gas_limit`` is the remaining regular budget
    plus ``delta``. The inclusion check uses strict ``>``, so
    ``delta=0`` must pass and ``delta=1`` must reject with
    ``GAS_ALLOWANCE_EXCEEDED``. Catches an off-by-one ``>=`` bug.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()

    filler_tx_count = (fork.minimum_block_gas_limit() // intrinsic_gas) + 1
    block_gas_limit = intrinsic_gas * (filler_tx_count + 1)

    dest_contract = pre.deploy_contract(code=Op.STOP)
    filler_sender = pre.fund_eoa()
    filler_txs = [
        Transaction(
            to=dest_contract,
            gas_limit=intrinsic_gas,
            sender=filler_sender,
        )
        for _ in range(filler_tx_count)
    ]

    excess_tx_gas_limit = intrinsic_gas + delta
    assert excess_tx_gas_limit < gas_limit_cap
    error = TransactionException.GAS_ALLOWANCE_EXCEEDED if delta else None
    excess_tx = Transaction(
        to=dest_contract,
        gas_limit=excess_tx_gas_limit,
        sender=pre.fund_eoa(),
        error=error,
    )

    blockchain_test(
        genesis_environment=Environment(gas_limit=block_gas_limit),
        pre=pre,
        blocks=[
            Block(
                txs=filler_txs + [excess_tx],
                gas_limit=block_gas_limit,
                exception=error,
                header_verify=Header(gas_used=block_gas_limit)
                if not error
                else None,
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

    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
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
                state_gas_reservoir=sstore_state_gas,
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


@pytest.mark.parametrize("dominant_dimension", ["state", "regular"])
@pytest.mark.valid_from("EIP8037")
def test_base_fee_per_gas_follows_dominant_dimension(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    dominant_dimension: str,
) -> None:
    """
    Verify the child block's base fee follows the bottleneck dimension.

    Block 1 exceeds the gas target on one dimension only: state, via
    SSTORE-set txs that spill, or regular, via STOP txs. Its header
    gas_used = max(regular, state) is then set by that dimension alone,
    which lifts empty block 2's base fee under the EIP-1559 update.
    """
    genesis_base_fee = 10**9
    max_fee_per_gas = 10**10
    gas_limit = 600_000
    target = gas_limit // fork.base_fee_elasticity_multiplier()

    txs: list[Transaction] = []
    post: dict = {}
    if dominant_dimension == "state":
        num_txs = 5
        tx_regular, tx_state = sstore_tx_gas(fork)
        block_regular = num_txs * tx_regular
        block_state = num_txs * tx_state
        tx_gas_limit = tx_regular + tx_state
        assert block_state > target > block_regular
    else:
        num_txs = 15
        tx_gas_limit = fork.transaction_intrinsic_cost_calculator()()
        block_regular = num_txs * tx_gas_limit
        block_state = 0
        stop_contract = pre.deploy_contract(code=Op.STOP)
        assert block_regular > target > block_state

    for _ in range(num_txs):
        if dominant_dimension == "state":
            storage = Storage()
            contract = pre.deploy_contract(
                code=Op.SSTORE(storage.store_next(1), 1) + Op.STOP,
            )
            post[contract] = Account(storage=storage)
        else:
            contract = stop_contract
        txs.append(
            Transaction(
                to=contract,
                gas_limit=tx_gas_limit,
                max_fee_per_gas=max_fee_per_gas,
                max_priority_fee_per_gas=0,
                sender=pre.fund_eoa(),
            )
        )

    block_1_gas_used = max(block_regular, block_state)
    base_fee_calc = fork.base_fee_per_gas_calculator()
    block_1_base_fee = base_fee_calc(
        parent_base_fee_per_gas=genesis_base_fee,
        parent_gas_used=0,
        parent_gas_limit=gas_limit,
    )
    block_2_base_fee = base_fee_calc(
        parent_base_fee_per_gas=block_1_base_fee,
        parent_gas_used=block_1_gas_used,
        parent_gas_limit=gas_limit,
    )
    assert block_2_base_fee > block_1_base_fee

    blockchain_test(
        genesis_environment=Environment(
            gas_limit=gas_limit,
            base_fee_per_gas=genesis_base_fee,
        ),
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                gas_limit=gas_limit,
                header_verify=Header(
                    gas_used=block_1_gas_used,
                    base_fee_per_gas=block_1_base_fee,
                ),
            ),
            Block(
                txs=[],
                gas_limit=gas_limit,
                header_verify=Header(
                    gas_used=0,
                    base_fee_per_gas=block_2_base_fee,
                ),
            ),
        ],
        post=post,
    )
