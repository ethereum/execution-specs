"""Tests EIP-7805 FOCIL inclusion-list interactions with block gas."""

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    Environment,
    Fork,
    Transaction,
)

from .spec import ref_spec_7805

REFERENCE_SPEC_GIT_PATH = ref_spec_7805.git_path
REFERENCE_SPEC_VERSION = ref_spec_7805.version

pytestmark = [
    pytest.mark.valid_from("Bogota"),
    pytest.mark.blockchain_test_engine_only,
]

# Body transfer count. Keeps the tx-derived block gas limit above the
# EIP-7928 BAL item budget (block_gas_limit // GAS_BLOCK_ACCESS_LIST_ITEM)
FILL_TX_COUNT = 20


@pytest.mark.parametrize(
    "scenario",
    [
        "empty_pending",
        "pending_does_not_fit",
        "pending_fits",
        "pending_exactly_fits",
    ],
)
@pytest.mark.parametrize("value", [0, 1])
def test_pending_il_appendability_by_remaining_execution_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    scenario: str,
    value: int,
) -> None:
    """
    A pending IL tx is appendable only if it fits the block's remaining
    execution gas (not taking into account state gas).

    The block body is two value-less transfers that consume exactly their
    intrinsic gas, leaving a bounded ``remaining_gas`` budget. Each scenario
    omits a pending IL tx with a different gas limit and asserts whether it
    could still be appended: it counts only when ``gas_limit <=
    remaining_gas``. The pending senders are otherwise valid and funded, so
    gas is the only variable.
    """
    calc = fork.transaction_intrinsic_cost_calculator()
    simple_zero_transfer_gas = calc()

    block_txs = [
        Transaction(
            sender=pre.fund_eoa(),
            to=pre.nonexistent_account(),
            gas_limit=simple_zero_transfer_gas,
        )
        for _ in range(FILL_TX_COUNT)
    ]

    pending_tx = Transaction(
        sender=pre.fund_eoa(),
        to=pre.nonexistent_account(),
        value=value,
        gas_limit=calc(sends_value=value > 0),
    )

    block_gas_limit = (
        sum(tx.gas_limit for tx in block_txs) + pending_tx.gas_limit
    )

    pending: list[Transaction] = []
    match scenario:
        case "empty_pending":
            expected_satisfied = True
        case "pending_does_not_fit":
            pending = [pending_tx]
            expected_satisfied = True
            block_gas_limit -= 1
        case "pending_fits":
            pending = [pending_tx]
            expected_satisfied = False
            block_gas_limit += 1
        case "pending_exactly_fits":
            pending = [pending_tx]
            expected_satisfied = False
        case _:
            raise ValueError(f"unknown scenario: {scenario}")

    # The IL view is the in-block IL tx plus every omitted (pending) tx.
    inclusion_list_txs = [block_txs[1], *pending]
    blockchain_test(
        genesis_environment=Environment(gas_limit=block_gas_limit),
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=block_txs,
                inclusion_list_txs=inclusion_list_txs,
                expected_inclusion_list_satisfied=expected_satisfied,
            )
        ],
    )


@pytest.mark.parametrize("value", [0, 1])
def test_block_with_intrinsic_gas_too_low_pending_il_tx_is_valid(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    value: int,
) -> None:
    """
    A pending IL tx with gas limit below intrinsic gas may be omitted.

    Even with enough remaining block gas, a transaction whose declared gas
    limit is below its intrinsic cost is invalid and therefore does not make
    the payload IL-unsatisfied.
    """
    simple_zero_transfer_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=value > 0
    )
    sender = pre.fund_eoa()
    recipient = pre.nonexistent_account()
    intrinsic_gas_too_low_tx = Transaction(
        sender=sender,
        to=recipient,
        value=value,
        gas_limit=simple_zero_transfer_gas - 1,
    )

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=[],
                inclusion_list_txs=[intrinsic_gas_too_low_tx],
                expected_inclusion_list_satisfied=True,
            )
        ],
    )
