"""
abstract: Tests that benchmark EVMs in worst-case block scenarios.
    Tests that benchmark EVMs in worst-case block scenarios.

Tests running worst-case block scenarios for EVMs.
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
    StateTestFiller,
    Transaction,
)


@pytest.fixture
def iteration_count(intrinsic_cost: int, gas_benchmark_value: int):
    """Calculate the number of iterations based on the gas limit and intrinsic cost."""
    return gas_benchmark_value // intrinsic_cost


@pytest.fixture
def transfer_amount():
    """Ether to transfer in each transaction."""
    return 1


@pytest.fixture
def intrinsic_cost(fork: Fork):
    """Transaction intrinsic cost."""
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
    intrinsic_cost: int,
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
                gas_limit=intrinsic_cost,
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


@pytest.fixture
def total_cost_floor_per_token():
    """Total cost floor per token."""
    return 10


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("zero_byte", [True, False])
def test_block_full_data(
    state_test: StateTestFiller,
    pre: Alloc,
    zero_byte: bool,
    intrinsic_cost: int,
    total_cost_floor_per_token: int,
    gas_benchmark_value: int,
    env: Environment,
):
    """Test a block with empty payload."""
    # Gas cost calculation based on EIP-7683: (https://eips.ethereum.org/EIPS/eip-7683)
    #
    #   tx.gasUsed = 21000 + max(
    #       STANDARD_TOKEN_COST * tokens_in_calldata
    #       + execution_gas_used
    #       + isContractCreation * (32000 + INITCODE_WORD_COST * words(calldata)),
    #       TOTAL_COST_FLOOR_PER_TOKEN * tokens_in_calldata)
    #
    # Simplified in this test case:
    # - No execution gas used (no opcodes are executed)
    # - Not a contract creation (no initcode)
    #
    # Therefore:
    #   max_token_cost = max(STANDARD_TOKEN_COST, TOTAL_COST_FLOOR_PER_TOKEN)
    #   tx.gasUsed = 21000 + tokens_in_calldata * max_token_cost
    #
    # Since max(STANDARD_TOKEN_COST, TOTAL_COST_FLOOR_PER_TOKEN) = 10:
    #   tx.gasUsed = 21000 + tokens_in_calldata * 10
    #
    # Token accounting:
    #   tokens_in_calldata = zero_bytes + 4 * non_zero_bytes
    #
    # So we calculate how many bytes we can fit into calldata based on available gas.

    gas_available = gas_benchmark_value - intrinsic_cost

    # Calculate the token_in_calldata
    max_tokens_in_calldata = gas_available // total_cost_floor_per_token
    # Calculate the number of bytes that can be stored in the calldata
    num_of_bytes = max_tokens_in_calldata if zero_byte else max_tokens_in_calldata // 4
    byte_data = b"\x00" if zero_byte else b"\xff"

    tx = Transaction(
        to=pre.fund_eoa(),
        data=byte_data * num_of_bytes,
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )
