"""Witness state collection scenarios for structural invariants."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    ExecutionWitnessStateExpectation,
    Transaction,
)

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def test_witness_state_structural_invariants(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    A simple transfer is enough to validate the shared state invariants.

    The expectation object always checks for duplicate entries and sorted
    order even when no explicit state nodes are listed.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=1)
    tx = Transaction(sender=sender, to=recipient, value=1, gas_limit=21_000)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_state=(
                    ExecutionWitnessStateExpectation()
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
            recipient: Account(balance=2),
        },
    )
