"""
abstract: Tests zkEVMs worst-case block scenarios.
    Tests zkEVMs worst-case block scenarios.

Tests running worst-case block scenarios for zkEVMs.
"""

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Environment,
    Transaction,
)


@pytest.fixture
def iteration_count(eth_transfer_cost: int):
    """Calculate the number of iterations based on the gas limit and intrinsic cost."""
    return Environment().gas_limit // eth_transfer_cost


@pytest.fixture
def transfer_amount():
    """Ether to transfer in each transaction."""
    return 1


@pytest.fixture
def eth_transfer_cost(fork: Fork):
    """Transaction gas limit."""
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    return intrinsic_cost()


def get_distinct_sender_list(pre: Alloc):
    """Get a list of distinct sender accounts."""
    while True:
        yield pre.fund_eoa()


def get_distinct_receiver_list(pre: Alloc):
    """Get a list of distinct receiver accounts."""
    while True:
        yield pre.fund_eoa(0)


def get_single_sender_list(pre: Alloc):
    """Get a list of single sender accounts."""
    sender = pre.fund_eoa()
    while True:
        yield sender


def get_single_receiver_list(pre: Alloc):
    """Get a list of single receiver accounts."""
    receiver = pre.fund_eoa(0)
    while True:
        yield receiver


@pytest.fixture
def ether_transfer_case(
    case_id: str,
    pre: Alloc,
):
    """Generate the test parameters based on the case ID."""
    if case_id == "a_to_a":
        """Sending to self."""
        senders = get_single_sender_list(pre)
        receivers = senders

    elif case_id == "a_to_b":
        """One sender → one receiver."""
        senders = get_single_sender_list(pre)
        receivers = get_single_receiver_list(pre)

    elif case_id == "diff_acc_to_b":
        """Multiple senders → one receiver."""
        senders = get_distinct_sender_list(pre)
        receivers = get_single_receiver_list(pre)

    elif case_id == "a_to_diff_acc":
        """One sender → multiple receivers."""
        senders = get_single_sender_list(pre)
        receivers = get_distinct_receiver_list(pre)

    elif case_id == "diff_acc_to_diff_acc":
        """Multiple senders → multiple receivers."""
        senders = get_distinct_sender_list(pre)
        receivers = get_distinct_receiver_list(pre)

    else:
        raise ValueError(f"Unknown case: {case_id}")

    return senders, receivers


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "case_id",
    ["a_to_a", "a_to_b", "diff_acc_to_b", "a_to_diff_acc", "diff_acc_to_diff_acc"],
)
def test_block_full_of_ether_transfers(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    case_id: str,
    ether_transfer_case,
    iteration_count: int,
    transfer_amount: int,
    eth_transfer_cost: int,
):
    """
    Single test for ether transfer scenarios.

    Scenarios:
    - a_to_a: one sender → one sender
    - a_to_b: one sender → one receiver
    - diff_acc_to_b: multiple senders → one receiver
    - a_to_diff_acc: one sender → multiple receivers
    - diff_acc_to_diff_acc: multiple senders → multiple receivers
    """
    senders, receivers = ether_transfer_case

    # Create a single block with all transactions
    txs = []
    balances: dict[Address, int] = {}
    for _ in range(iteration_count):
        receiver = next(receivers)
        balances[receiver] = balances.get(receiver, 0) + transfer_amount
        txs.append(
            Transaction(
                to=receiver,
                value=transfer_amount,
                gas_limit=eth_transfer_cost,
                sender=next(senders),
            )
        )

    # Only include post state for non a_to_a cases
    post_state = (
        {}
        if case_id == "a_to_a"
        else {receiver: Account(balance=balance) for receiver, balance in balances.items()}
    )

    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        post=post_state,
        blocks=[Block(txs=txs)],
        exclude_full_post_state_in_output=True,
    )
