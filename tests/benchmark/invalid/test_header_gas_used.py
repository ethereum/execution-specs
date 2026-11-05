"""
Benchmarks whose block header understates the gas used.

Template for invalid-block benchmarks: the block executes a full load of
ether transfers, then its header ``gasUsed`` is rewritten to one less
than the value the transactions consumed, so a client must execute the
whole block before it can reject it.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BenchmarkTestFiller,
    Block,
    BlockException,
    Fork,
    Header,
    RecipientType,
    Transaction,
)


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
    """
    sender = pre.fund_eoa()
    receiver_balance = 1

    # Every receiver already exists, so no transaction pays new-account
    # state gas and the block gas is the plain sum of the transfer costs.
    transfer_cost = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True,
        recipient_type=RecipientType.EOA,
    ) + fork.transaction_top_frame_execution_gas(
        sends_value=True,
        recipient_type=RecipientType.EOA,
    )

    txs = []
    receivers = []
    gas_used = 0
    while gas_used + transfer_cost <= gas_benchmark_value:
        receiver = pre.fund_eoa(receiver_balance)
        receivers.append(receiver)
        txs.append(
            Transaction(
                to=receiver,
                value=1,
                gas_limit=transfer_cost,
                sender=sender,
            )
        )
        gas_used += transfer_cost

    benchmark_test(
        pre=pre,
        # The block is rejected, so no transfer lands.
        post={
            receiver: Account(balance=receiver_balance)
            for receiver in receivers
        },
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
