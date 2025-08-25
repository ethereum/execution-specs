"""
abstract: Tests that benchmark EVMs in worst-case block scenarios.
    Tests that benchmark EVMs in worst-case block scenarios.

Tests running worst-case block scenarios for EVMs.
"""

import random

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    AccessList,
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Hash,
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
        pre=pre,
        post=post_state,
        blocks=[Block(txs=txs)],
        exclude_full_post_state_in_output=True,
        expected_benchmark_gas_used=iteration_count * intrinsic_cost,
    )


@pytest.fixture
def total_cost_floor_per_token():
    """Total cost floor per token."""
    return 10


@pytest.fixture
def total_cost_standard_per_token():
    """Total cost floor per token."""
    return 4


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("zero_byte", [True, False])
def test_block_full_data(
    state_test: StateTestFiller,
    pre: Alloc,
    zero_byte: bool,
    intrinsic_cost: int,
    total_cost_floor_per_token: int,
    gas_benchmark_value: int,
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
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Prague")
def test_block_full_access_list_and_data(
    state_test: StateTestFiller,
    pre: Alloc,
    intrinsic_cost: int,
    total_cost_standard_per_token: int,
    fork: Fork,
    gas_benchmark_value: int,
):
    """Test a block with access lists (60% gas) and calldata (40% gas) using random mixed bytes."""
    attack_gas_limit = gas_benchmark_value
    gas_available = attack_gas_limit - intrinsic_cost

    # Split available gas: 60% for access lists, 40% for calldata
    gas_for_access_list = int(gas_available * 0.6)
    gas_for_calldata = int(gas_available * 0.4)

    # Access list gas costs from fork's gas_costs
    gas_costs = fork.gas_costs()
    gas_per_address = gas_costs.G_ACCESS_LIST_ADDRESS
    gas_per_storage_key = gas_costs.G_ACCESS_LIST_STORAGE

    # Calculate number of storage keys we can fit
    gas_after_address = gas_for_access_list - gas_per_address
    num_storage_keys = gas_after_address // gas_per_storage_key

    # Create access list with 1 address and many storage keys
    access_address = Address("0x1234567890123456789012345678901234567890")
    storage_keys = []
    for i in range(num_storage_keys):
        # Generate random-looking storage keys
        storage_keys.append(Hash(i))

    access_list = [
        AccessList(
            address=access_address,
            storage_keys=storage_keys,
        )
    ]

    # Calculate calldata with 29% of gas for zero bytes and 71% for non-zero bytes
    # Token accounting: tokens_in_calldata = zero_bytes + 4 * non_zero_bytes
    # We want to split the gas budget:
    # - 29% of gas_for_calldata for zero bytes
    # - 71% of gas_for_calldata for non-zero bytes

    max_tokens_in_calldata = gas_for_calldata // total_cost_standard_per_token

    # Calculate how many tokens to allocate to each type
    tokens_for_zero_bytes = int(max_tokens_in_calldata * 0.29)
    tokens_for_non_zero_bytes = max_tokens_in_calldata - tokens_for_zero_bytes

    # Convert tokens to actual byte counts
    # Zero bytes: 1 token per byte
    # Non-zero bytes: 4 tokens per byte
    num_zero_bytes = tokens_for_zero_bytes  # 1 token = 1 zero byte
    num_non_zero_bytes = tokens_for_non_zero_bytes // 4  # 4 tokens = 1 non-zero byte

    # Create calldata with mixed bytes
    calldata = bytearray()

    # Add zero bytes
    calldata.extend(b"\x00" * num_zero_bytes)

    # Add non-zero bytes (random values from 0x01 to 0xff)
    rng = random.Random(42)  # For reproducibility
    for _ in range(num_non_zero_bytes):
        calldata.append(rng.randint(1, 255))

    # Shuffle the bytes to mix zero and non-zero bytes
    calldata_list = list(calldata)
    rng.shuffle(calldata_list)
    shuffled_calldata = bytes(calldata_list)

    tx = Transaction(
        to=pre.fund_eoa(amount=0),
        data=shuffled_calldata,
        gas_limit=attack_gas_limit,
        sender=pre.fund_eoa(),
        access_list=access_list,
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
        expected_benchmark_gas_used=fork.transaction_intrinsic_cost_calculator()(
            calldata=shuffled_calldata,
            access_list=access_list,
        ),
    )
