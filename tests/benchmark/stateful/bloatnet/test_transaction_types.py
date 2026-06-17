"""Benchmark ether transfers to receivers that exist on-chain."""

import itertools
from typing import Generator

import pytest
from execution_testing import (
    DETERMINISTIC_FACTORY_ADDRESS,
    EOA,
    Address,
    Alloc,
    BenchmarkTestFiller,
    Block,
    Fork,
    Op,
    Transaction,
    compute_create2_address,
    compute_create_address,
    keccak256,
)

from tests.benchmark.helper.account_creator import (
    AccountCreator,
    AccountMode,
)

# Deterministic sender pool of 15K accounts.
# Funded via system contract withdrawals (funding.txt) in payload generation.
# Placed outside pre-allocation to ensure accounts remain uncached.
SENDER_BASE_KEY = int.from_bytes(
    keccak256(b"gas-repricings-private-key"), "big"
)


def yield_distinct_sender() -> Generator[EOA, None, None]:
    """Yield deterministic sender EOAs pre-funded on-chain."""
    for i in itertools.count(0):
        yield EOA(key=SENDER_BASE_KEY + i)


def yield_distinct_create2_receiver(
    initcode: bytes,
) -> Generator[Address, None, None]:
    """
    Yield contract addresses deployed by the deterministic CREATE2 factory.
    """
    for salt in itertools.count(0):
        yield compute_create2_address(
            address=DETERMINISTIC_FACTORY_ADDRESS,
            salt=salt,
            initcode=initcode,
        )


# Bittrex controller mainnet address
# Creates 1.5M contracts with deterministic address via CREATE
# It is guaranteed no contract is destructed
# Used for existing contract targets in benchmark
BITTREX_CONTROLLER_ADDRESS = Address(
    0xA3C1E324CA1CE40DB73ED6026C4A177F099B5770
)


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
        "diff_to_self",
        "diff_to_nonexistent",
        "diff_to_existent",
        "diff_to_contract",
        "diff_to_unique_code_jumpdest_contract",
        "diff_to_contract_minimal",
        "diff_to_contract_same",
        "diff_to_contract_diff",
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
    """Benchmark ether transfers across different receiver account types."""
    senders = yield_distinct_sender()
    receiver_execution_gas = 0
    receivers: Generator[Address, None, None]
    match case_id:
        case "diff_to_self":
            receivers = senders
        case "diff_to_nonexistent":
            receivers = yield_distinct_nonexistent_receiver()
        case "diff_to_existent":
            receivers = yield_distinct_existent_receiver()
        case "diff_to_contract":
            receivers = yield_distinct_contract_receiver()
            # Runtime code is the same across all the receivers
            # Example contract: https://etherscan.io/address/0xa888df3ef62286dde06a79395760b9bce6c83c83#code
            runtime = (
                Op.MSTORE(0x40, 0x60, new_memory_size=0x60)
                + Op.JUMPI(Op.PUSH2(0x49), Op.ISZERO(Op.CALLDATASIZE))
                + Op.JUMPDEST * 3
                + Op.JUMP(Op.PUSH2(0x50))
                + Op.JUMPDEST
            )
            receiver_execution_gas = runtime.gas_cost(fork)
        case "diff_to_unique_code_jumpdest_contract":
            creator = AccountCreator(AccountMode.EXISTING_CONTRACT_JUMPDEST)
            receivers = yield_distinct_create2_receiver(creator.initcode)
            receiver_execution_gas = creator.runtime_code.gas_cost(fork)
        case "diff_to_contract_minimal":
            receivers = yield_distinct_create2_receiver(
                AccountCreator(AccountMode.EXISTING_CONTRACT_MINIMAL).initcode
            )
        case "diff_to_contract_same":
            receivers = yield_distinct_create2_receiver(
                AccountCreator(AccountMode.EXISTING_CONTRACT_SAME).initcode
            )
        case "diff_to_contract_diff":
            receivers = yield_distinct_create2_receiver(
                AccountCreator(AccountMode.EXISTING_CONTRACT_DIFF).initcode
            )
        case _:
            raise ValueError(f"Unknown case: {case_id}")

    iteration_cost = (
        fork.transaction_intrinsic_cost_calculator()() + receiver_execution_gas
    )
    iteration_count = gas_benchmark_value // iteration_cost

    txs = []
    for _ in range(iteration_count):
        sender = next(senders)
        txs.append(
            Transaction(
                to=sender if case_id == "diff_to_self" else next(receivers),
                value=transfer_amount,
                gas_limit=iteration_cost,
                sender=sender,
            )
        )

    benchmark_test(
        pre=pre,
        post={},
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=iteration_count * iteration_cost,
        expected_receipt_status=1,
    )
