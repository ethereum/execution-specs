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
)

# Deterministic sender pool of 15K accounts.
# Funded via system contract withdrawals (funding.txt) in payload generation.
# Placed outside pre-allocation to ensure accounts remain uncached.
SENDER_BASE_KEY = (
    0x1111111111111111111111111111111111111111111111111111111111111111
)


def yield_distinct_sender() -> Generator[EOA, None, None]:
    """Yield deterministic sender EOAs pre-funded on-chain."""
    for i in itertools.count(0):
        yield EOA(key=SENDER_BASE_KEY + i)


def build_unique_contract_initcode() -> bytes:
    """
    Deployed runtime contract layout.

        offset    size   contents
        ------    ----   --------------------------------
        0x0000       4   PUSH2 0x5FFF; JUMP   <- entry
        0x0004      28   JUMPDEST padding
        0x0020      12   JUMPDEST padding
        0x002C      20   contract ADDRESS     <- unique
        0x0040   24512   JUMPDEST             <- 0x5FFF lands here
        0x6000           STOP

    Embedded ADDRESS makes runtime unique per contract;
    initcode and its CREATE2 hash is shared across all salts.
    """
    max_code_size = 0x6000  # EIP-170 contract code size limit

    # MCOPY fills MEM[0:0x8000] with JUMPDEST.
    # Runtime only uses MEM[0:0x6000].
    code = Op.MSTORE(0, bytes(Op.JUMPDEST * 32))
    for size in (1 << s for s in range(5, 15)):
        code += Op.MCOPY(size, 0, size)

    # Runtime entry: JUMP to final JUMPDEST, then STOP.
    entry = Op.JUMP(max_code_size - 1)
    entry += Op.JUMPDEST * (32 - len(entry))  # Padding

    code += Op.MSTORE(0, bytes(entry))

    # Mask ADDRESS into a JUMPDEST template via OR:
    #                  bytes 0..12   bytes 12..32
    #                  -----------   ------------
    #     ADDRESS      00 .. 00      <20-byte address>
    #     addr_slot    5b .. 5b      00 .. 00
    #     OR result    5b .. 5b      <20-byte address>
    addr_slot = Op.JUMPDEST * 12 + Op.STOP * 20
    code += Op.MSTORE(0x20, Op.OR(Op.ADDRESS, bytes(addr_slot)))

    code += Op.RETURN(0, max_code_size)

    return bytes(code)


JOCHEMNET_UNIQUE_CONTRACT_INITCODE = build_unique_contract_initcode()


def yield_distinct_unique_code_jumpdest_receiver() -> Generator[
    Address, None, None
]:
    """
    Yield contract addresses deployed by the deterministic CREATE2 factory.
    """
    for salt in itertools.count(0):
        yield compute_create2_address(
            address=DETERMINISTIC_FACTORY_ADDRESS,
            salt=salt,
            initcode=JOCHEMNET_UNIQUE_CONTRACT_INITCODE,
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
        "diff_to_nonexistent",
        "diff_to_existent",
        "diff_to_contract",
        "diff_to_unique_code_jumpdest_contract",
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
    - diff_to_unique_code_jumpdest_contract: distinct CREATE2 contract
      receivers each holding unique deployed code
    """
    senders = yield_distinct_sender()
    receiver_execution_gas = 0
    if case_id == "diff_to_nonexistent":
        receivers = yield_distinct_nonexistent_receiver()
    elif case_id == "diff_to_existent":
        receivers = yield_distinct_existent_receiver()
    elif case_id == "diff_to_contract":
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
    elif case_id == "diff_to_unique_code_jumpdest_contract":
        receivers = yield_distinct_unique_code_jumpdest_receiver()
        # Runtime code aligns entry code path.
        runtime = Op.JUMP(Op.PUSH2(0x5FFF)) + Op.JUMPDEST
        receiver_execution_gas = runtime.gas_cost(fork)
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
