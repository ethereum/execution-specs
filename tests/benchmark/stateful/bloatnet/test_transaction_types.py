"""Benchmark ether transfers to receivers that exist on-chain."""

import itertools
from typing import Generator

import pytest
from execution_testing import (
    Address,
    Alloc,
    BenchmarkTestFiller,
    Block,
    Fork,
    Transaction,
    compute_create_address,
)


def yield_distinct_sender(pre: Alloc) -> Generator[Address, None, None]:
    """Get a list of distinct sender accounts."""
    while True:
        yield pre.fund_eoa()


# Bittrex controller mainnet address
# Creates 1.5M contracts with deterministic address via CREATE
# It is guaranteed no contract is destructed
# Used for existing contract targets in benchmark
BITTREX_CONTROLLER_ADDRESS = Address(
    0xA3C1E324CA1CE40DB73ED6026C4A177F099B5770
)


# Ether reception cost for Bittrex-created contracts
RECEIVER_CONTRACT_EXECUTION_GAS = 51


def yield_distinct_contract_receiver() -> Generator[Address, None, None]:
    """Yield contract account created by Bittrex controller via CREATE."""
    for nonce in itertools.count(2):
        yield compute_create_address(
            address=BITTREX_CONTROLLER_ADDRESS, nonce=nonce
        )


def yield_distinct_existent_receiver() -> Generator[Address, None, None]:
    """
    Yield existing balance-only EOA on bloatnet. pre-funded by Spamoor
    (https://github.com/CPerezz/spamoor/pull/12).
    """
    for address in itertools.count(0x1000):
        yield Address(address)


def yield_distinct_nonexistent_receiver() -> Generator[Address, None, None]:
    """Yield non-existent accounts starting from keccak256('random')."""
    for address in itertools.count(0xF3CF193BB4AF1022AF7D2089F37D8BAE7157B85F):
        yield Address(address)


@pytest.mark.repricing
@pytest.mark.parametrize(
    "case_id",
    [
        "diff_to_nonexistent",
        "diff_to_existent",
        "diff_to_contract",
    ],
)
@pytest.mark.parametrize("transfer_amount", [0, 1])
def test_ether_transfers_onchain_receivers(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    case_id: str,
    transfer_amount: int,
    fork: Fork,
    gas_benchmark_value: int,
) -> None:
    """
    Ether transfers to receivers that exist on-chain at run time.

    Scenarios:
    - diff_to_nonexistent: distinct nonexistent receivers
      (matches AccountMode.NON_EXISTING_ACCOUNT)
    - diff_to_existent: distinct existent EOA receivers
      (matches AccountMode.EXISTING_EOA)
    - diff_to_contract: distinct contract receivers
      (matches AccountMode.EXISTING_CONTRACT)
    """
    senders = yield_distinct_sender(pre)
    receiver_execution_gas = 0
    if case_id == "diff_to_nonexistent":
        receivers = yield_distinct_nonexistent_receiver()
    elif case_id == "diff_to_existent":
        receivers = yield_distinct_existent_receiver()
    elif case_id == "diff_to_contract":
        receivers = yield_distinct_contract_receiver()
        receiver_execution_gas = RECEIVER_CONTRACT_EXECUTION_GAS
    else:
        raise ValueError(f"Unknown case: {case_id}")

    iteration_cost = (
        fork.transaction_intrinsic_cost_calculator()() + receiver_execution_gas
    )
    iteration_count = gas_benchmark_value // iteration_cost

    txs = [
        Transaction(
            to=next(receivers),
            value=transfer_amount,
            gas_limit=iteration_cost,
            sender=next(senders),
        )
        for _ in range(iteration_count)
    ]

    benchmark_test(
        pre=pre,
        post={},
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=iteration_count * iteration_cost,
        expected_receipt_status=1,
    )
