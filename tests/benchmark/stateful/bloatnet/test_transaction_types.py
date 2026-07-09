"""Benchmark ether transfers to receivers that exist on-chain."""

from typing import Generator

import pytest
from execution_testing import (
    Address,
    Alloc,
    BenchmarkTestFiller,
    Block,
    Fork,
    Op,
    RecipientType,
    Transaction,
)

from tests.benchmark.helper.account_creator import (
    AccountCreator,
    AccountMode,
)
from tests.benchmark.helper.account_sender_receiver import (
    yield_distinct_contract_receiver,
    yield_distinct_create2_receiver,
    yield_distinct_delegate_receiver,
    yield_distinct_existent_receiver,
    yield_distinct_nonexistent_receiver,
    yield_distinct_sender,
)


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
        "diff_to_delegated_contract_diff",
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
    recipient_type = RecipientType.CONTRACT
    receivers: Generator[Address, None, None]
    match case_id:
        case "diff_to_self":
            receivers = senders
            recipient_type = RecipientType.SELF
        case "diff_to_nonexistent":
            receivers = yield_distinct_nonexistent_receiver()
            recipient_type = RecipientType.EMPTY_ACCOUNT
        case "diff_to_existent":
            receivers = yield_distinct_existent_receiver()
            recipient_type = RecipientType.EOA
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
        case "diff_to_delegated_contract_diff":
            receivers = yield_distinct_delegate_receiver()
            recipient_type = RecipientType.DELEGATION_7702
        case _:
            raise ValueError(f"Unknown case: {case_id}")

    sends_value = transfer_amount > 0
    iteration_cost = (
        fork.transaction_intrinsic_cost_calculator()(
            sends_value=sends_value,
            recipient_type=recipient_type,
        )
        + fork.transaction_top_frame_gas_calculator()(
            sends_value=sends_value,
            recipient_type=recipient_type,
        )
        + fork.transaction_top_frame_state_gas(
            sends_value=sends_value,
            recipient_type=recipient_type,
        )
        + receiver_execution_gas
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
