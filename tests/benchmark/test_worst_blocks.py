"""
Tests that benchmark EVMs in worst-case block scenarios.
"""

import math
import random
from typing import Generator, Tuple

import pytest
from ethereum_test_base_types import Account
from ethereum_test_forks import Fork
from ethereum_test_tools import (
    AccessList,
    Address,
    Alloc,
    AuthorizationTuple,
    BenchmarkTestFiller,
    Block,
    BlockchainTestFiller,
    Hash,
    Transaction,
)
from ethereum_test_vm import Opcodes as Op


@pytest.fixture
def iteration_count(intrinsic_cost: int, gas_benchmark_value: int) -> int:
    """
    Calculate the number of iterations based on the gas limit and intrinsic
    cost.
    """
    return gas_benchmark_value // intrinsic_cost


@pytest.fixture
def transfer_amount() -> int:
    """Ether to transfer in each transaction."""
    return 1


@pytest.fixture
def intrinsic_cost(fork: Fork) -> int:
    """Transaction intrinsic cost."""
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    return intrinsic_cost()


def get_distinct_sender_list(pre: Alloc) -> Generator[Address, None, None]:
    """Get a list of distinct sender accounts."""
    while True:
        yield pre.fund_eoa()


def get_distinct_receiver_list(pre: Alloc) -> Generator[Address, None, None]:
    """Get a list of distinct receiver accounts."""
    while True:
        yield pre.fund_eoa(0)


def get_single_sender_list(pre: Alloc) -> Generator[Address, None, None]:
    """Get a list of single sender accounts."""
    sender = pre.fund_eoa()
    while True:
        yield sender


def get_single_receiver_list(pre: Alloc) -> Generator[Address, None, None]:
    """Get a list of single receiver accounts."""
    receiver = pre.fund_eoa(0)
    while True:
        yield receiver


@pytest.fixture
def ether_transfer_case(
    case_id: str,
    pre: Alloc,
) -> Tuple[Generator[Address, None, None], Generator[Address, None, None]]:
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


@pytest.mark.parametrize(
    "case_id",
    [
        "a_to_a",
        "a_to_b",
        "diff_acc_to_b",
        "a_to_diff_acc",
        "diff_acc_to_diff_acc",
    ],
)
def test_block_full_of_ether_transfers(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    case_id: str,
    ether_transfer_case: Tuple[
        Generator[Address, None, None], Generator[Address, None, None]
    ],
    iteration_count: int,
    transfer_amount: int,
    intrinsic_cost: int,
) -> None:
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
        else {
            receiver: Account(balance=balance)
            for receiver, balance in balances.items()
        }
    )

    benchmark_test(
        pre=pre,
        post=post_state,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=iteration_count * intrinsic_cost,
    )


@pytest.fixture
def total_cost_floor_per_token() -> int:
    """Total cost floor per token."""
    return 10


@pytest.fixture
def total_cost_standard_per_token() -> int:
    """Total cost floor per token."""
    return 4


def calldata_generator(
    gas_amount: int,
    zero_byte: int,
    total_cost_floor_per_token: int,
) -> bytes:
    """Calculate the calldata based on the gas amount and zero byte."""
    # Gas cost calculation based on EIP-7683: (https://eips.ethereum.org/EIPS/eip-7683)
    #
    #   tx.gasUsed = 21000 + max(
    #       STANDARD_TOKEN_COST * tokens_in_calldata
    #       + execution_gas_used
    #       + isContractCreation * (32000 +
    #                                 INITCODE_WORD_COST * words(calldata)),
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
    # So we calculate how many bytes we can fit into calldata based on
    # available gas.
    max_tokens_in_calldata = gas_amount // total_cost_floor_per_token
    num_of_bytes = (
        max_tokens_in_calldata if zero_byte else max_tokens_in_calldata // 4
    )
    byte_data = b"\x00" if zero_byte else b"\xff"
    return byte_data * num_of_bytes


@pytest.mark.parametrize("zero_byte", [True, False])
def test_block_full_data(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    zero_byte: bool,
    intrinsic_cost: int,
    total_cost_floor_per_token: int,
    gas_benchmark_value: int,
    tx_gas_limit_cap: int,
    total_cost_standard_per_token: int,
    fork: Fork,
) -> None:
    """Test a block with empty payload."""
    iteration_count = math.ceil(gas_benchmark_value / tx_gas_limit_cap)

    gas_remaining = gas_benchmark_value
    total_gas_used = 0
    txs = []
    for _ in range(iteration_count):
        gas_available = min(tx_gas_limit_cap, gas_remaining) - intrinsic_cost
        data = calldata_generator(
            gas_available,
            zero_byte,
            total_cost_floor_per_token,
        )

        total_gas_used += fork.transaction_intrinsic_cost_calculator()(
            calldata=data
        )
        gas_remaining -= gas_available + intrinsic_cost

        txs.append(
            Transaction(
                to=pre.fund_eoa(),
                data=data,
                gas_limit=gas_available + intrinsic_cost,
                sender=pre.fund_eoa(),
            )
        )

    benchmark_test(
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=total_gas_used,
    )


def test_block_full_access_list_and_data(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    intrinsic_cost: int,
    total_cost_standard_per_token: int,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit_cap: int,
) -> None:
    """
    Test a block with access lists (60% gas) and calldata (40% gas) using
    random mixed bytes.
    """
    iteration_count = math.ceil(gas_benchmark_value / tx_gas_limit_cap)

    gas_remaining = gas_benchmark_value
    total_gas_used = 0

    txs = []
    for _ in range(iteration_count):
        gas_available = min(tx_gas_limit_cap, gas_remaining) - intrinsic_cost

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

        # Calculate calldata with 29% of gas for zero bytes and 71% for
        # non-zero bytes
        # Token accounting: tokens_in_calldata = zero_bytes + 4 *
        # non_zero_bytes
        # We want to split the gas budget:
        # - 29% of gas_for_calldata for zero bytes
        # - 71% of gas_for_calldata for non-zero bytes

        max_tokens_in_calldata = (
            gas_for_calldata // total_cost_standard_per_token
        )

        # Calculate how many tokens to allocate to each type
        tokens_for_zero_bytes = int(max_tokens_in_calldata * 0.29)
        tokens_for_non_zero_bytes = (
            max_tokens_in_calldata - tokens_for_zero_bytes
        )

        # Convert tokens to actual byte counts
        # Zero bytes: 1 token per byte
        # Non-zero bytes: 4 tokens per byte
        num_zero_bytes = tokens_for_zero_bytes  # 1 token = 1 zero byte
        num_non_zero_bytes = (
            tokens_for_non_zero_bytes // 4
        )  # 4 tokens = 1 non-zero byte

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

        txs.append(
            Transaction(
                to=pre.fund_eoa(amount=0),
                data=shuffled_calldata,
                gas_limit=gas_available + intrinsic_cost,
                sender=pre.fund_eoa(),
                access_list=access_list,
            )
        )

        gas_remaining -= gas_for_access_list + intrinsic_cost
        total_gas_used += fork.transaction_intrinsic_cost_calculator()(
            calldata=shuffled_calldata,
            access_list=access_list,
        )

    benchmark_test(
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=total_gas_used,
    )


@pytest.mark.parametrize("empty_authority", [True, False])
@pytest.mark.parametrize("zero_delegation", [True, False])
def test_worst_case_auth_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    intrinsic_cost: int,
    gas_benchmark_value: int,
    fork: Fork,
    empty_authority: bool,
    zero_delegation: bool,
) -> None:
    """Test an auth block."""
    gas_costs = fork.gas_costs()

    iteration_count = (
        gas_benchmark_value - intrinsic_cost
    ) // gas_costs.G_AUTHORIZATION

    code = Op.STOP * fork.max_code_size()
    auth_target = (
        Address(0) if zero_delegation else pre.deploy_contract(code=code)
    )

    auth_tuples = []
    for _ in range(iteration_count):
        signer = (
            pre.fund_eoa(amount=0, delegation=None)
            if empty_authority
            else pre.fund_eoa(amount=0, delegation=auth_target)
        )
        auth_tuple = AuthorizationTuple(
            address=auth_target, nonce=signer.nonce, signer=signer
        )
        auth_tuples.append(auth_tuple)

    tx = Transaction(
        to=pre.empty_account(),
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
        authorization_list=auth_tuples,
    )

    gas_used = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=auth_tuples
    )

    refund = 0
    if not empty_authority:
        refund = min(
            gas_used // 5,
            (
                gas_costs.G_AUTHORIZATION
                - gas_costs.R_AUTHORIZATION_EXISTING_AUTHORITY
            )
            * iteration_count,
        )

    blockchain_test(
        pre=pre,
        post={},
        blocks=[Block(txs=[tx])],
        expected_benchmark_gas_used=gas_used - refund,
    )
