"""
Test [EIP-7623: Increase calldata cost](https://eips.ethereum.org/EIPS/eip-7623)
interaction with the block gas limit.
"""

from typing import Dict, List, Tuple

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytes,
    Environment,
    Fork,
    GasConsumer,
    Header,
    Op,
    RecipientType,
    Transaction,
    TransactionException,
    TransitionFork,
)

from .spec import ref_spec_7623

REFERENCE_SPEC_GIT_PATH = ref_spec_7623.git_path
REFERENCE_SPEC_VERSION = ref_spec_7623.version

FLOOR_TX_COUNT = 2
FLOOR_TX_DATA = Bytes(b"\xff" * 100_000)

with_probe_gas_delta = pytest.mark.parametrize(
    "probe_gas_delta",
    [
        pytest.param(0, id="fits_floor_inclusive_gas_used"),
        pytest.param(
            1,
            id="exceeds_floor_inclusive_gas_used",
            marks=pytest.mark.exception_test,
        ),
    ],
)


def probe_gas_used(fork: Fork) -> Tuple[int, int]:
    """
    Return the execution gas and the total gas used by a probe transaction
    sending value to an empty account.
    """
    probe_execution_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True, return_cost_deducted_prior_execution=True
    ) + fork.transaction_top_frame_execution_gas(
        sends_value=True, recipient_type=RecipientType.EMPTY_ACCOUNT
    )
    probe_gas = probe_execution_gas + fork.transaction_top_frame_state_gas(
        sends_value=True, recipient_type=RecipientType.EMPTY_ACCOUNT
    )
    return probe_execution_gas, probe_gas


def probe_after_preceding_txs(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    preceding_txs: List[Transaction],
    preceding_gas_used: int,
    wrong_gas_used: List[int],
    probe_gas_delta: int,
    post: Dict[Address, Account] | None = None,
) -> None:
    """
    Fill a block whose block gas limit leaves exactly the probe transaction's
    gas after `preceding_gas_used`, and whose probe asks for
    `probe_gas_delta` more than that.

    Each value in `wrong_gas_used` is the block gas used under a rule the
    test tells apart from the correct one; the probe must fit after each, so
    only the correct rule rejects it.
    """
    probe_execution_gas, probe_gas = probe_gas_used(fork)
    block_gas_limit = preceding_gas_used + probe_gas
    probe_gas_limit = probe_gas + probe_gas_delta
    for gas_used in wrong_gas_used:
        assert probe_gas_limit <= block_gas_limit - gas_used

    probe_receiver = pre.fund_eoa(amount=0)
    exceeds = probe_gas_delta > 0
    probe_tx = Transaction(
        to=probe_receiver,
        value=1,
        gas_limit=probe_gas_limit,
        sender=pre.fund_eoa(),
        error=TransactionException.GAS_ALLOWANCE_EXCEEDED if exceeds else None,
    )

    blockchain_test(
        genesis_environment=Environment(gas_limit=block_gas_limit),
        pre=pre,
        post={}
        if exceeds
        else {probe_receiver: Account(balance=1), **(post or {})},
        blocks=[
            Block(
                txs=[*preceding_txs, probe_tx],
                exception=TransactionException.GAS_ALLOWANCE_EXCEEDED
                if exceeds
                else None,
                # The header reports the larger of the execution and state
                # gas used; only the probe uses state gas.
                header_verify=None
                if exceeds
                else Header(
                    gas_used=max(
                        preceding_gas_used + probe_execution_gas,
                        probe_gas - probe_execution_gas,
                    )
                ),
            )
        ],
    )


@pytest.mark.parametrize(
    "preceding_txs_order",
    [
        pytest.param("only_floor", id="only_floor"),
        pytest.param("floor_before_execution", id="floor_before_execution"),
        pytest.param("floor_after_execution", id="floor_after_execution"),
    ],
)
@pytest.mark.with_all_typed_transactions(selector=lambda tx_type: tx_type != 6)
@with_probe_gas_delta
@pytest.mark.valid_from("Prague")
def test_tx_gas_limit_after_floor_priced_txs(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    typed_transaction: Transaction,
    preceding_txs_order: str,
    probe_gas_delta: int,
) -> None:
    """
    Test that the gas available to a transaction is the block gas limit minus
    the block gas used so far, including the calldata floor charged to the
    preceding transactions.

    The floor-bound transactions pay the data floor, so their execution gas
    is well below their gas used. The probe transaction's gas limit fits into
    the gas left after execution gas but must be checked against the gas left
    after the floor-inclusive gas used. Mixing in an execution-bound
    transaction checks that the larger of execution gas and the floor is
    taken per transaction, not across the summed totals.
    """
    access_list = typed_transaction.access_list
    authorization_list = typed_transaction.authorization_list
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    floor_cost_calculator = fork.transaction_data_floor_cost_calculator()
    floor_cost = floor_cost_calculator(
        data=FLOOR_TX_DATA, access_list=access_list
    )
    execution_cost = intrinsic_cost(
        calldata=FLOOR_TX_DATA,
        access_list=access_list,
        authorization_list_or_count=authorization_list,
        return_cost_deducted_prior_execution=True,
    )
    floor_tx_gas_limit = intrinsic_cost(
        calldata=FLOOR_TX_DATA,
        access_list=access_list,
        authorization_list_or_count=authorization_list,
    )
    # The floor, not the standard intrinsic cost, sets the gas used.
    assert floor_tx_gas_limit == floor_cost > execution_cost

    receiver = pre.fund_eoa(amount=0)

    def floor_tx() -> Transaction:
        return typed_transaction.copy(
            to=receiver,
            data=FLOOR_TX_DATA,
            gas_limit=floor_tx_gas_limit,
            sender=pre.fund_eoa(),
            secret_key=None,
        )

    # The execution-bound transaction runs out of gas, so its gas used is its
    # gas limit, well above the floor of its empty calldata.
    execution_tx_gas_used = floor_cost
    execution_tx_floor_cost = floor_cost_calculator(data=b"")
    assert execution_tx_gas_used > execution_tx_floor_cost

    def execution_tx() -> Transaction:
        return Transaction(
            to=pre.deploy_contract(code=GasConsumer.out_of_gas(fork)),
            gas_limit=execution_tx_gas_used,
            sender=pre.fund_eoa(),
        )

    if preceding_txs_order == "only_floor":
        preceding_txs = [floor_tx() for _ in range(FLOOR_TX_COUNT)]
        preceding_gas_used = FLOOR_TX_COUNT * floor_cost
        # Execution gas only.
        wrong_gas_used = [FLOOR_TX_COUNT * execution_cost]
    elif preceding_txs_order in (
        "floor_before_execution",
        "floor_after_execution",
    ):
        if preceding_txs_order == "floor_before_execution":
            preceding_txs = [floor_tx(), execution_tx()]
        else:
            preceding_txs = [execution_tx(), floor_tx()]
        preceding_gas_used = floor_cost + execution_tx_gas_used
        wrong_gas_used = [
            # Execution gas only.
            execution_cost + execution_tx_gas_used,
            # The larger of the summed execution gas and the summed floors.
            max(
                execution_cost + execution_tx_gas_used,
                floor_cost + execution_tx_floor_cost,
            ),
        ]
    else:
        raise ValueError(f"Unknown order: {preceding_txs_order}")

    probe_after_preceding_txs(
        blockchain_test,
        pre,
        fork,
        preceding_txs=preceding_txs,
        preceding_gas_used=preceding_gas_used,
        wrong_gas_used=wrong_gas_used,
        probe_gas_delta=probe_gas_delta,
    )


@with_probe_gas_delta
@pytest.mark.valid_from("Prague")
def test_tx_gas_limit_after_refunded_floor_bound_tx(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    probe_gas_delta: int,
) -> None:
    """
    Test the block gas used by a preceding transaction whose calldata floor
    lies between its gas used before and after the refund.

    Before EIP-7778 the floor applies after the refund, so the floor is the
    block gas used. With EIP-7778 the block counts gas before the refund,
    which exceeds the floor.
    """
    refunded_key = 0
    code = Op.SSTORE(
        refunded_key, 0, key_warm=False, original_value=1, new_value=0
    )
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    floor_cost_calculator = fork.transaction_data_floor_cost_calculator()

    def costs(data: Bytes) -> Tuple[int, int, int]:
        gas_before_refund = intrinsic_cost(
            calldata=data, return_cost_deducted_prior_execution=True
        ) + code.gas_cost(fork)
        refund = min(
            gas_before_refund // fork.max_refund_quotient(),
            code.refund(fork),
        )
        return gas_before_refund, refund, floor_cost_calculator(data=data)

    # Pick the calldata size in the middle of the range whose floor lies
    # strictly between the gas used after and before the refund.
    sizes = []
    for size in range(4096):
        gas_before_refund, refund, floor_cost = costs(Bytes(b"\xff" * size))
        if gas_before_refund - refund < floor_cost < gas_before_refund:
            sizes.append(size)
    assert sizes
    data = Bytes(b"\xff" * sizes[len(sizes) // 2])
    gas_before_refund, refund, floor_cost = costs(data)

    if fork.is_eip_enabled(7778):
        gas_used = gas_before_refund
        # Gas used after the refund, raised to the floor.
        wrong_gas_used = floor_cost
    else:
        gas_used = floor_cost
        # Floor applied before the refund is subtracted.
        wrong_gas_used = gas_before_refund - refund

    contract = pre.deploy_contract(code=code, storage={refunded_key: 1})
    refunded_tx = Transaction(
        to=contract,
        data=data,
        gas_limit=gas_before_refund,
        sender=pre.fund_eoa(),
    )

    probe_after_preceding_txs(
        blockchain_test,
        pre,
        fork,
        preceding_txs=[refunded_tx],
        preceding_gas_used=gas_used,
        wrong_gas_used=[wrong_gas_used],
        probe_gas_delta=probe_gas_delta,
        post={contract: Account(storage={refunded_key: 0})},
    )


@pytest.mark.parametrize(
    "probe_block_offset",
    [
        pytest.param(-1, id="last_pre_fork_block"),
        pytest.param(0, id="fork_block"),
    ],
)
@with_probe_gas_delta
@pytest.mark.valid_at_transition_to("Osaka", subsequent_forks=True)
def test_tx_gas_limit_after_floor_priced_txs_at_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    probe_block_offset: int,
    probe_gas_delta: int,
) -> None:
    """
    Test the floor-inclusive gas available to a transaction on both sides of
    a fork, which can reprice the calldata floor or change how the block gas
    used is accounted.

    The block gas limit is fixed across the fork, so the probe's gas limit is
    the gas left after the floor priced by the probe block's fork.
    """
    first_block_timestamp = fork.at_timestamp - 1
    probe_block_timestamp = fork.at_timestamp + probe_block_offset
    pre_fork = fork.transitions_from()
    post_fork = fork.transitions_to()
    probe_fork = fork.fork_at(timestamp=probe_block_timestamp)

    def floor_gas_used(block_fork: Fork) -> int:
        return (
            FLOOR_TX_COUNT
            * block_fork.transaction_data_floor_cost_calculator()(
                data=FLOOR_TX_DATA
            )
        )

    block_gas_limit = max(
        floor_gas_used(f) + probe_gas_used(f)[1] for f in (pre_fork, post_fork)
    )
    floor_block_gas_used = floor_gas_used(probe_fork)
    probe_execution_gas, probe_gas = probe_gas_used(probe_fork)
    probe_gas_limit = block_gas_limit - floor_block_gas_used + probe_gas_delta
    assert probe_gas_limit >= probe_gas + probe_gas_delta

    execution_cost = probe_fork.transaction_intrinsic_cost_calculator()(
        calldata=FLOOR_TX_DATA, return_cost_deducted_prior_execution=True
    )
    assert probe_gas_limit <= block_gas_limit - FLOOR_TX_COUNT * execution_cost
    # In the fork block, when the fork raises the floor, the probe also fits
    # after the floor priced by the previous fork.
    if probe_fork == post_fork and floor_gas_used(pre_fork) < (
        floor_block_gas_used
    ):
        assert probe_gas_limit <= block_gas_limit - floor_gas_used(pre_fork)

    receiver = pre.fund_eoa(amount=0)
    floor_txs = [
        Transaction(
            to=receiver,
            data=FLOOR_TX_DATA,
            gas_limit=probe_fork.transaction_data_floor_cost_calculator()(
                data=FLOOR_TX_DATA
            ),
            sender=pre.fund_eoa(),
        )
        for _ in range(FLOOR_TX_COUNT)
    ]
    exceeds = probe_gas_delta > 0
    probe_tx = Transaction(
        to=receiver,
        value=1,
        gas_limit=probe_gas_limit,
        sender=pre.fund_eoa(),
        error=TransactionException.GAS_ALLOWANCE_EXCEEDED if exceeds else None,
    )

    blocks = [
        Block(timestamp=timestamp)
        for timestamp in range(first_block_timestamp, probe_block_timestamp)
    ]
    blocks.append(
        Block(
            timestamp=probe_block_timestamp,
            txs=[*floor_txs, probe_tx],
            exception=TransactionException.GAS_ALLOWANCE_EXCEEDED
            if exceeds
            else None,
            header_verify=None
            if exceeds
            else Header(gas_used=floor_block_gas_used + probe_execution_gas),
        )
    )

    blockchain_test(
        genesis_environment=Environment(gas_limit=block_gas_limit),
        pre=pre,
        post={} if exceeds else {receiver: Account(balance=1)},
        blocks=blocks,
    )
