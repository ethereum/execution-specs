"""
Benchmarks whose block misstates what its transactions did.

Templates for invalid-block benchmarks: the block executes a full load of
ether transfers, then the header or the block access list is rewritten,
so a client must execute the whole block before it can reject it.
"""

from typing import Dict, List, Tuple

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BenchmarkTestFiller,
    Block,
    BlockAccessListExpectation,
    BlockException,
    Fork,
    Hash,
    Header,
    RecipientType,
    Transaction,
)
from execution_testing.test_types.block_access_list.modifiers import (
    modify_balance,
)

RECEIVER_BALANCE = 1
TRANSFER_VALUE = 1


def ether_transfers(
    pre: Alloc, fork: Fork, gas_benchmark_value: int
) -> Tuple[List[Transaction], Dict[Address, Account], int]:
    """
    Return transfers to existing accounts that fill the block, the
    post-state of a block that rejects them, and the gas they use.
    """
    sender = pre.fund_eoa()

    # Every receiver already exists, so no transaction pays new-account
    # state gas and the block gas is the plain sum of the transfer costs.
    transfer_cost = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True,
        recipient_type=RecipientType.EOA,
    ) + fork.transaction_top_frame_execution_gas(
        sends_value=True,
        recipient_type=RecipientType.EOA,
    )
    transfer_count = gas_benchmark_value // transfer_cost

    receivers = [pre.fund_eoa(RECEIVER_BALANCE) for _ in range(transfer_count)]
    txs = [
        Transaction(
            to=receiver,
            value=TRANSFER_VALUE,
            gas_limit=transfer_cost,
            sender=sender,
        )
        for receiver in receivers
    ]
    # The block is rejected, so no transfer lands.
    post: Dict[Address, Account] = {
        receiver: Account(balance=RECEIVER_BALANCE) for receiver in receivers
    }
    return txs, post, transfer_count * transfer_cost


@pytest.mark.exception_test
def test_ether_transfers_gas_used_minus_one(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
) -> None:
    """
    Fill a block with one-wei transfers to existing accounts and declare
    one gas less than they used in the header.

    Clients order their post-execution checks differently, so some reject
    this block before computing the state root and others after it.
    """
    txs, post, gas_used = ether_transfers(pre, fork, gas_benchmark_value)

    benchmark_test(
        pre=pre,
        post=post,
        blocks=[
            Block(
                txs=txs,
                # Pin the premise: the transactions really used this much.
                header_verify=Header(gas_used=gas_used),
                rlp_modifier=Header(gas_used=gas_used - 1),
                exception=BlockException.INVALID_GAS_USED,
            )
        ],
        expected_benchmark_gas_used=gas_used,
    )


@pytest.mark.exception_test
def test_ether_transfers_wrong_state_root(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
) -> None:
    """
    Fill a block with one-wei transfers to existing accounts and declare
    a wrong state root in the header.

    Every client has to execute the block and compute the state root
    before it can reject it.
    """
    txs, post, gas_used = ether_transfers(pre, fork, gas_benchmark_value)

    benchmark_test(
        pre=pre,
        post=post,
        blocks=[
            Block(
                txs=txs,
                rlp_modifier=Header(state_root=Hash(0)),
                exception=BlockException.INVALID_STATE_ROOT,
            )
        ],
        expected_benchmark_gas_used=gas_used,
    )


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.exception_test
def test_ether_transfers_wrong_block_access_list(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
) -> None:
    """
    Fill a block with one-wei transfers to existing accounts and give the
    last receiver a wrong balance in the block access list.

    The entry belongs to the last transaction, so the list only disagrees
    with execution once the whole block has run.
    """
    txs, post, gas_used = ether_transfers(pre, fork, gas_benchmark_value)
    receiver = txs[-1].to
    assert receiver is not None
    last_index = len(txs)
    received_balance = RECEIVER_BALANCE + TRANSFER_VALUE

    benchmark_test(
        pre=pre,
        post=post,
        blocks=[
            Block(
                txs=txs,
                header_verify=Header(gas_used=gas_used),
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        receiver: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=last_index,
                                    post_balance=received_balance,
                                )
                            ],
                        ),
                    }
                ).modify(
                    modify_balance(
                        receiver,
                        block_access_index=last_index,
                        balance=received_balance + 1,
                    )
                ),
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
            )
        ],
        expected_benchmark_gas_used=gas_used,
    )
