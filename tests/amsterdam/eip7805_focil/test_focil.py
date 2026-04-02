"""Tests EIP-7805 FOCIL execution-layer inclusion-list handling."""

from typing import Literal, TypedDict

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    Environment,
    Fork,
    Op,
    Transaction,
)
from execution_testing.test_types.transaction_types import (
    TransactionDefaults,
)

from .helpers import (
    IncludedBlockTx,
    PendingInclusionListTx,
    build_block,
)
from .spec import Spec, ref_spec_7805

REFERENCE_SPEC_GIT_PATH = ref_spec_7805.git_path
REFERENCE_SPEC_VERSION = ref_spec_7805.version

pytestmark = [
    pytest.mark.valid_from("Amsterdam"),
    pytest.mark.blockchain_test_engine_only,
]

# Number of zero-byte calldata bytes used to differentiate the
# second tx's gas cost from a simple transfer.
SECOND_TX_ZERO_BYTES = 50
# Remaining block gas headroom in the same-sender test.
SAME_SENDER_BLOCK_HEADROOM = 7_500

PendingSpecValueKey = Literal[
    "simple_transfer_gas",
    "one_nonzero_byte_gas",
    "remaining_gas_plus_zero_byte_gas",
    "simple_transfer_gas_times_gas_price",
]


class PendingSpecDataRequired(TypedDict):
    """Required fields for a pending IL tx parametrization entry."""

    actual_gas_used: int | PendingSpecValueKey


class PendingSpecData(PendingSpecDataRequired, total=False):
    """Optional fields for a pending IL tx parametrization entry."""

    nonce: int
    sender_label: str
    sender_balance: int | PendingSpecValueKey


def test_block_with_same_sender_included_il_txs_is_valid(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Including two IL txs from one sender keeps the payload valid."""
    calc = fork.transaction_intrinsic_cost_calculator()
    simple_transfer_gas = calc()
    second_tx_gas = calc(
        calldata=b"\x00" * SECOND_TX_ZERO_BYTES,
    )
    block_gas_limit = (
        simple_transfer_gas + second_tx_gas + SAME_SENDER_BLOCK_HEADROOM
    )
    built_block = build_block(
        pre,
        fork=fork,
        block_gas_limit=block_gas_limit,
        included_block_tx_specs=(
            IncludedBlockTx(
                actual_gas_used=simple_transfer_gas,
                nonce=0,
                is_inclusion_list_tx=True,
                sender_label="alice",
            ),
            IncludedBlockTx(
                actual_gas_used=second_tx_gas,
                nonce=1,
                is_inclusion_list_tx=True,
                sender_label="alice",
            ),
        ),
        pending_inclusion_list_tx_specs=(),
    )
    assert built_block.remaining_gas == SAME_SENDER_BLOCK_HEADROOM
    blockchain_test(
        genesis_environment=Environment(gas_limit=block_gas_limit),
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=built_block.block_txs,
                inclusion_list_txs=(built_block.inclusion_list_txs),
            )
        ],
    )


def test_block_with_reverting_included_il_tx_is_valid(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Include an IL tx that calls a reverting contract.

    The tx reverts during execution but is present in the block body,
    so the inclusion list check is satisfied.
    """
    reverting_contract = pre.deploy_contract(
        code=Op.REVERT(0, 0),
    )
    sender = pre.fund_eoa(amount=10**18)
    revert_tx = Transaction(
        sender=sender,
        to=reverting_contract,
        gas_limit=100_000,
    )
    blockchain_test(
        genesis_environment=Environment(gas_limit=200_000),
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=[revert_tx],
                inclusion_list_txs=[revert_tx],
            )
        ],
    )


@pytest.mark.parametrize(
    ("pending_specs_data", "expected_status"),
    [
        pytest.param(
            (),
            None,
            id="valid_with_empty_pending_il",
        ),
        pytest.param(
            ({"actual_gas_used": "remaining_gas_plus_zero_byte_gas"},),
            None,
            id="valid_with_pending_il_txs_that_do_not_fit",
        ),
        pytest.param(
            (
                {
                    "actual_gas_used": "simple_transfer_gas",
                    "nonce": 1,
                    "sender_label": "bob",
                },
            ),
            None,
            id="valid_with_pending_il_txs_that_are_invalid",
        ),
        pytest.param(
            (
                {
                    "actual_gas_used": "simple_transfer_gas",
                    "sender_label": "poor",
                    "sender_balance": 0,
                },
            ),
            None,
            id="valid_with_pending_il_txs_that_fit_but_sender_cannot_afford",
        ),
        pytest.param(
            (
                {
                    "actual_gas_used": "one_nonzero_byte_gas",
                    "sender_balance": "simple_transfer_gas_times_gas_price",
                },
            ),
            None,
            id="valid_with_pending_il_tx_unaffordable_due_to_calldata",
        ),
        pytest.param(
            ({"actual_gas_used": "simple_transfer_gas"},),
            Spec.INCLUSION_LIST_UNSATISFIED_STATUS,
            id="unsatisfied_with_appendable_pending_il_tx",
        ),
    ],
)
def test_block_status_depends_on_pending_inclusion_list(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    pending_specs_data: tuple[PendingSpecData, ...],
    expected_status: str | None,
) -> None:
    """
    A block is valid unless a pending IL tx is still appendable.

    All scenarios share the same block body (one non-IL tx and one
    IL tx, both simple transfers). The pending IL set varies: empty,
    too large, invalid nonce, unaffordable, calldata-unaffordable,
    or appendable. Only the appendable scenario should produce
    INCLUSION_LIST_UNSATISFIED.
    """
    calc = fork.transaction_intrinsic_cost_calculator()
    simple_transfer_gas = calc()
    one_nonzero_byte_gas = calc(calldata=b"\x01")
    zero_byte_gas = calc(calldata=b"\x00") - simple_transfer_gas
    gas_price = TransactionDefaults.gas_price

    # Block fits 2 included simple transfers plus room for a
    # calldata-bearing pending tx and a small buffer.
    remaining_headroom = zero_byte_gas
    block_gas_limit = (
        2 * simple_transfer_gas + one_nonzero_byte_gas + remaining_headroom
    )
    remaining_gas = one_nonzero_byte_gas + remaining_headroom

    included_block_tx_specs = (
        IncludedBlockTx(
            actual_gas_used=simple_transfer_gas,
            is_inclusion_list_tx=False,
        ),
        IncludedBlockTx(
            actual_gas_used=simple_transfer_gas,
            is_inclusion_list_tx=True,
        ),
    )

    resolved_values: dict[PendingSpecValueKey, int] = {
        "simple_transfer_gas": simple_transfer_gas,
        "one_nonzero_byte_gas": one_nonzero_byte_gas,
        "remaining_gas_plus_zero_byte_gas": remaining_gas + zero_byte_gas,
        "simple_transfer_gas_times_gas_price": (
            simple_transfer_gas * gas_price
        ),
    }
    pending_specs_list: list[PendingInclusionListTx] = []
    for pending_spec_data in pending_specs_data:
        actual_gas_used = pending_spec_data["actual_gas_used"]
        sender_balance = pending_spec_data.get("sender_balance", 10**18)
        pending_specs_list.append(
            PendingInclusionListTx(
                actual_gas_used=(
                    resolved_values[actual_gas_used]
                    if isinstance(actual_gas_used, str)
                    else actual_gas_used
                ),
                nonce=pending_spec_data.get("nonce", 0),
                sender_label=pending_spec_data.get("sender_label"),
                sender_balance=(
                    resolved_values[sender_balance]
                    if isinstance(sender_balance, str)
                    else sender_balance
                ),
            )
        )
    pending_specs = tuple(pending_specs_list)

    built_block = build_block(
        pre,
        fork=fork,
        block_gas_limit=block_gas_limit,
        included_block_tx_specs=included_block_tx_specs,
        pending_inclusion_list_tx_specs=pending_specs,
    )
    assert built_block.remaining_gas == remaining_gas
    assert expected_status in (
        None,
        Spec.INCLUSION_LIST_UNSATISFIED_STATUS,
    )
    blockchain_test(
        genesis_environment=Environment(
            gas_limit=block_gas_limit,
        ),
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=built_block.block_txs,
                inclusion_list_txs=(built_block.inclusion_list_txs),
            )
        ],
    )


def test_unsatisfied_when_block_tx_funds_pending_il_sender(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A preceding block tx funds the pending IL tx's sender.

    Verify that FOCIL validates pending IL txs against the
    post-execution state. A value transfer in the block gives the
    pending IL tx's sender enough balance to afford its tx, so the
    block is unsatisfied.
    """
    calc = fork.transaction_intrinsic_cost_calculator()
    simple_transfer_gas = calc()
    gas_price = TransactionDefaults.gas_price

    value_to_fund_bob = simple_transfer_gas * gas_price
    alice = pre.fund_eoa(
        amount=simple_transfer_gas * gas_price + value_to_fund_bob,
    )
    bob = pre.fund_eoa(amount=0)
    recipient = pre.fund_eoa()

    alice_tx = Transaction(
        sender=alice,
        to=bob,
        gas_limit=simple_transfer_gas,
        value=value_to_fund_bob,
    )
    bob_il_tx = Transaction(
        sender=bob,
        to=recipient,
        gas_limit=simple_transfer_gas,
    )

    block_gas_limit = simple_transfer_gas * 5
    blockchain_test(
        genesis_environment=Environment(
            gas_limit=block_gas_limit,
        ),
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=[alice_tx],
                inclusion_list_txs=[bob_il_tx],
            )
        ],
    )
