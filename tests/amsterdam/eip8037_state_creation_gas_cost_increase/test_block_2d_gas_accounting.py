"""
Test block-level two-dimensional gas accounting under EIP-8037.

Verify that the block header gas_used equals
max(block_execution_gas_used, block_state_gas_used) across
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
    compute_create_address,
)

from ...cancun.eip4844_blobs.spec import Spec as EIP4844_Spec
from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


def sstore_tx_gas(fork: Fork, num_sstores: int = 1) -> tuple[int, int]:
    """Return (execution, state) gas for a tx with N cold SSTOREs."""
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()
    evm_total = num_sstores * Op.SSTORE(0, 1).execution_cost(fork)
    state = num_sstores * Op.SSTORE(new_value=1).state_cost(fork)
    return intrinsic_gas + evm_total, state


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
    Verify block.gas_used = block_state_gas when state > execution.

    Each tx performs zero-to-nonzero SSTOREs. Since state gas per
    SSTORE exceeds execution gas, block_state_gas exceeds
    block_execution_gas and becomes the header gas_used.

    The spillover variant provides reservoir for only one SSTORE
    per tx; the remaining state gas spills into gas_left.
    Block-level accounting must still separate the two dimensions.
    """
    tx_execution, tx_state = sstore_tx_gas(fork, num_sstores)
    block_execution = num_txs * tx_execution
    block_state = num_txs * tx_state
    assert block_state > block_execution

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
def test_block_gas_used_execution_dominates(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify block.gas_used = block_execution_gas when state gas is zero.

    A block containing only STOP transactions to existing contracts
    produces no state gas. The block header gas_used must equal the
    sum of execution gas across all transactions, since
    max(execution, 0) = execution.
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

    STOP txs contribute only execution gas; SSTORE txs contribute both.
    The interleaved variant alternates SSTORE/STOP to test that
    non-contiguous state gas contributions accumulate correctly.
    """
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()
    tx_execution_sstore, tx_state_sstore = sstore_tx_gas(fork)

    block_execution = (
        num_stop * intrinsic_gas + num_sstore * tx_execution_sstore
    )
    block_state = num_sstore * tx_state_sstore
    expected = max(block_execution, block_state)

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

    Execution gas refund via `refund_counter` does NOT reduce block gas
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
    tx_execution = intrinsic_gas + code.gas_cost(fork) - sstore_state_gas
    expected = num_txs * tx_execution
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
    Verify a block is valid when state gas dominates execution gas.

    Clients that sum execution + state will reject this valid block.
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
        tx_execution, tx_state = sstore_tx_gas(fork, num_sstores)
        intrinsic_execution = fork.transaction_intrinsic_cost_calculator()()

        tx_limit = tx_execution + tx_state + tx_execution // 10

        # Per-tx worst-case state contribution: tx.gas - intrinsic_execution.
        # The block_gas_limit must leave enough state budget for every tx.
        worst_state_per_tx = tx_limit - intrinsic_execution
        minimum_block_gas_limit = max(
            # Execution dimension: last tx must fit.
            (num_txs - 1) * tx_execution + tx_limit,
            # State dimension: cumulative worst-case must fit.
            num_txs * worst_state_per_tx,
        )
        if block_gas_limit >= minimum_block_gas_limit:
            break
        block_gas_limit += 1_000_000

    block_execution = num_txs * tx_execution
    block_state = num_txs * tx_state
    expected_gas_used = max(block_execution, block_state)

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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    target = pre.fund_eoa(amount=0)

    call = Op.CALL(
        gas=100_000,
        address=target,
        value=1,
        value_transfer=True,
        account_new=True,
    )
    parent_storage = Storage()
    parent = pre.deploy_contract(
        code=(call + Op.SSTORE(parent_storage.store_next(1), 1)),
        balance=10**18,
    )

    txs = [
        Transaction(
            to=parent,
            state_gas_reservoir=call.state_cost(fork) + sstore_state_gas,
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
    create_execution = (
        intrinsic_calc(
            calldata=init_code,
            contract_creation=True,
        )
        - create_state_gas
    )
    stop_execution = intrinsic_calc()

    expected = max(create_execution + stop_execution, create_state_gas)

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

    Block 1: STOP txs only (execution dominates).
    Block 2: SSTORE txs only (state dominates).
    Each block independently computes its own 2D max.
    """
    n = 3
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()
    tx_execution, tx_state = sstore_tx_gas(fork)

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
                    gas_used=max(n * tx_execution, n * tx_state),
                ),
            ),
        ],
        post=post_2,
    )


@pytest.mark.inclusion_test
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
    execution_gas_available`` and ``tx.gas <= state_gas_available``.
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


@pytest.mark.inclusion_test
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
def test_tx_inclusion_at_execution_gas_block_limit_small(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    delta: int,
) -> None:
    """
    Probe the execution-gas inclusion boundary with a small-gas tx.

    The second tx's ``gas_limit`` is the remaining execution budget
    plus ``delta``. The inclusion check uses strict ``>``, so
    ``delta=0`` must pass and ``delta=1`` must reject with
    ``GAS_ALLOWANCE_EXCEEDED``. Catches an off-by-one ``>=`` bug.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True,
    )

    filler_tx_count = (fork.minimum_block_gas_limit() // intrinsic_gas) + 1
    block_gas_limit = intrinsic_gas * (filler_tx_count + 1)

    dest_contract = pre.deploy_contract(code=Op.STOP)
    filler_sender = pre.fund_eoa()
    filler_txs = [
        Transaction(
            to=dest_contract,
            gas_limit=intrinsic_gas,
            value=1,
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
        value=1,
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
def test_block_2d_gas_tx_gas_limit_exceeds_execution_remaining(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    tx2_gas_limit_equals_block_gas_limit: bool,
) -> None:
    """
    Verify a block is valid when a later tx's gas_limit exceeds the
    execution budget remaining but its capped execution contribution fits.
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

    tx1_execution = intrinsic_gas
    tx2_execution, tx2_state = sstore_tx_gas(fork)
    expected_gas_used = max(tx1_execution + tx2_execution, tx2_state)

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
    tx_execution, tx_state = sstore_tx_gas(fork)
    num_txs = 3

    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    per_tx_gas_used = tx_execution + tx_state

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

    block_execution = num_txs * tx_execution
    block_state = num_txs * tx_state
    header_gas_used = max(block_execution, block_state)

    assert block_state > block_execution
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


@pytest.mark.parametrize("dominant_dimension", ["state", "execution"])
@pytest.mark.parametrize(
    "single_tx",
    [
        pytest.param(True, id="single_tx"),
        pytest.param(False, id="multiple_txs"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_base_fee_per_gas_follows_dominant_dimension(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    dominant_dimension: str,
    single_tx: bool,
) -> None:
    """
    Verify the child block's base fee follows the bottleneck dimension.

    Block 1 exceeds the gas target on one dimension only: state, via
    SSTORE-set txs that spill, or execution, via STOP/MSTORE txs. Its header
    gas_used = max(execution, state) is then set by that dimension alone,
    which lifts empty block 2's base fee under the EIP-1559 update.
    """
    genesis_base_fee = 10**9
    max_fee_per_gas = 10**10
    gas_limit = 600_000
    target = gas_limit // fork.base_fee_elasticity_multiplier()

    txs: list[Transaction] = []
    post: dict = {}
    num_sstores = 0
    if dominant_dimension == "state":
        if single_tx:
            num_txs = 1
            num_sstores = target // sstore_tx_gas(fork, num_sstores=1)[1] + 1
            tx_execution, tx_state = sstore_tx_gas(
                fork, num_sstores=num_sstores
            )
        else:
            num_sstores = 1
            tx_execution, tx_state = sstore_tx_gas(
                fork, num_sstores=num_sstores
            )
            while tx_execution >= tx_state:
                num_sstores += 1
                tx_execution, tx_state = sstore_tx_gas(
                    fork, num_sstores=num_sstores
                )
            num_txs = target // tx_state + 1
        block_execution = num_txs * tx_execution
        block_state = num_txs * tx_state
        tx_gas_limit = tx_execution + tx_state
        assert block_state > target > block_execution
    else:
        if single_tx:
            num_txs = 1
            # Just consume all gas
            execution_contract = pre.deploy_contract(
                code=Op.MSTORE(offset=2**256 - 1, value=1) + Op.STOP
            )
            tx_gas_limit = target + 1
        else:
            tx_gas_limit = fork.transaction_intrinsic_cost_calculator()()
            # Enough STOP txs that execution gas alone clears the target.
            execution_contract = pre.deploy_contract(code=Op.STOP)
            num_txs = target // tx_gas_limit + 1
        block_execution = num_txs * tx_gas_limit
        block_state = 0
        assert block_execution > target > block_state

    for _ in range(num_txs):
        if dominant_dimension == "state":
            storage = Storage()
            code = Bytecode()
            for _ in range(num_sstores):
                code += Op.SSTORE(storage.store_next(1), 1)
            code += Op.STOP
            contract = pre.deploy_contract(code=code)
            post[contract] = Account(storage=storage)
        else:
            contract = execution_contract
        txs.append(
            Transaction(
                to=contract,
                gas_limit=tx_gas_limit,
                max_fee_per_gas=max_fee_per_gas,
                max_priority_fee_per_gas=0,
                sender=pre.fund_eoa(),
            )
        )

    block_1_gas_used = max(block_execution, block_state)
    assert block_1_gas_used < gas_limit, (
        "test needs update: gas_limit reached by usage, simply raise the "
        "anchored gas_limit value"
    )
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


@pytest.mark.inclusion_test
@pytest.mark.parametrize(
    "delta",
    [
        pytest.param(0, id="exact_fit"),
        pytest.param(1, id="exceeded", marks=pytest.mark.exception_test),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_cumulative_block_state_gas_boundary(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    delta: int,
) -> None:
    """
    Probe the block state-gas inclusion gate with spill-funded usage.

    tx1 gets no state-gas reservoir (small gas_limit), so its SSTORE-set
    state gas reaches block_state_gas_used only via spillover, and its
    gas_limit exactly fills the block. tx2's gas_limit is the remaining
    state budget plus delta, below both the per-tx cap and the remaining
    execution budget, so only the state gate can reject it: delta=0 must
    be accepted (strict >) and delta=1 rejected.
    test_block_state_gas_limit_boundary covers this gate with a
    reservoir-funded tx1 and an above-cap tx2.
    """
    n = 6
    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    sstore_code = (
        sum((Op.SSTORE(i, 1) for i in range(n)), Bytecode()) + Op.STOP
    )
    tx1_execution = intrinsic + sstore_code.execution_cost(fork)
    tx1_state = sstore_code.state_cost(fork)
    # tx1 exactly fills the block; the leftover state budget is tx1_execution.
    block_gas_limit = tx1_execution + tx1_state
    # tx2 stays within the remaining execution budget, so only the state
    # dimension can reject it.
    assert tx1_execution + 1 <= block_gas_limit - tx1_execution

    sstore_contract = pre.deploy_contract(code=sstore_code)
    stop_contract = pre.deploy_contract(code=Op.STOP)

    error = TransactionException.GAS_ALLOWANCE_EXCEEDED if delta else None
    tx1 = Transaction(
        to=sstore_contract, gas_limit=block_gas_limit, sender=pre.fund_eoa()
    )
    tx2 = Transaction(
        to=stop_contract,
        gas_limit=tx1_execution + delta,
        sender=pre.fund_eoa(),
        error=error,
    )

    post: dict = {}
    header_verify: Header | None = None
    if not delta:
        post = {sstore_contract: Account(storage=dict.fromkeys(range(n), 1))}
        header_verify = Header(
            gas_used=max(tx1_execution + intrinsic, tx1_state)
        )

    blockchain_test(
        genesis_environment=Environment(gas_limit=block_gas_limit),
        pre=pre,
        blocks=[
            Block(
                txs=[tx1, tx2],
                exception=error,
                header_verify=header_verify,
            )
        ],
        post=post,
    )


@pytest.mark.inclusion_test
@pytest.mark.parametrize(
    "over_by",
    [
        pytest.param(0, id="exact_fit"),
        pytest.param(1, id="one_above", marks=pytest.mark.exception_test),
        pytest.param(
            None,
            id="state_charge_above",
            marks=pytest.mark.exception_test,
        ),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_block_2d_inclusion_execution_gate_full_gas_reservation(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    over_by: int | None,
) -> None:
    """
    Pin the flat execution-gas inclusion gate on a contract creation.

    EIP-8037 measures ``min(TX_MAX_GAS_LIMIT, tx.gas)`` against
    ``execution_gas_available`` in full, with no credit for the
    ``NEW_ACCOUNT`` state gas the creation charges at its top frame.
    Filler STOP txs spend execution gas only, so the state budget
    stays full and only the execution gate can reject the creation.

    Its ``gas_limit`` is the leftover execution budget plus
    ``over_by``, where ``None`` means the state charge itself. A
    client crediting that charge would accept ``over_by=1`` with
    slack and ``over_by=None`` exactly under strict ``>``; the flat
    gate rejects both. ``over_by=0`` is the control, valid either way.
    """
    init_code = bytes(Op.STOP)
    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas = intrinsic_calc()

    create_execution = intrinsic_calc(
        calldata=init_code,
        contract_creation=True,
    )
    create_state_charge = fork.transaction_top_frame_state_gas(
        contract_creation=True
    )

    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    delta = create_state_charge if over_by is None else over_by

    # The CREATE tx draws its state charge from gas_left, so it needs
    # both dimensions' gas within the leftover execution budget.
    create_gas = create_execution + create_state_charge
    num_fillers = create_state_charge // intrinsic_gas + 1
    filler_execution = num_fillers * intrinsic_gas
    block_gas_limit = max(
        filler_execution + create_gas,
        fork.minimum_block_gas_limit(),
    )
    execution_available = block_gas_limit - filler_execution
    tx_gas_limit = execution_available + delta

    assert execution_available >= create_gas
    assert tx_gas_limit <= gas_limit_cap and tx_gas_limit <= block_gas_limit

    assert tx_gas_limit - create_state_charge <= execution_available
    assert (tx_gas_limit > execution_available) == (delta > 0)

    error = TransactionException.GAS_ALLOWANCE_EXCEEDED if delta else None
    create_sender = pre.fund_eoa()
    create_tx = Transaction(
        to=None,
        data=init_code,
        gas_limit=tx_gas_limit,
        sender=create_sender,
        error=error,
    )

    post: dict = {}
    header_verify: Header | None = None
    if not delta:
        post = {
            compute_create_address(address=create_sender, nonce=0): Account(
                nonce=1
            ),
        }
        header_verify = Header(
            gas_used=max(
                filler_execution + create_execution,
                create_state_charge,
            ),
        )

    blockchain_test(
        genesis_environment=Environment(gas_limit=block_gas_limit),
        pre=pre,
        blocks=[
            Block(
                txs=stop_txs(pre, fork, num_fillers) + [create_tx],
                gas_limit=block_gas_limit,
                exception=error,
                header_verify=header_verify,
            )
        ],
        post=post,
    )
