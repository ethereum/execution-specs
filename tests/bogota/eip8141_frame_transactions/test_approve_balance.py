"""
Payer balance tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

A payment approval is refused when its target's balance is below
`max_cost`, the amount it then collects. The EIP does not say when the
balance is read; these tests read it when `APPROVE` runs, so earlier
frames that move value change the verdict. Every approval goes through
EOA default code, so a refusal invalidates the transaction.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    TransactionException,
)

from .helpers import (
    BASE_FEE,
    PRIORITY_FEE,
    FrameTransaction,
    default_frame,
    fee_budget,
    sender_frame,
    verify_frame,
)
from .signature_helpers import canonical_entry
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")


@pytest.mark.parametrize(
    "balance_delta",
    [
        pytest.param(0, id="balance_at_max_cost"),
        pytest.param(
            -1, id="balance_below_max_cost", marks=pytest.mark.exception_test
        ),
    ],
)
@pytest.mark.parametrize(
    "budget",
    [
        # `max_fee` is exactly the base fee cost, so `max_cost` equals
        # `max_fee`.
        pytest.param("exact_budget", id="exact_budget"),
        # `max_fee` exceeds the base fee cost but no tip is asked for,
        # so `max_cost` stays the base fee cost, below `max_fee`.
        pytest.param("surplus_without_tip", id="surplus_without_tip"),
        # The full tip fits in the budget, so `max_cost` is the base fee
        # cost plus the tip on `max_gas`, still below `max_fee`.
        pytest.param("surplus_with_tip", id="surplus_with_tip"),
    ],
)
def test_sender_balance_covers_max_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    budget: str,
    balance_delta: int,
) -> None:
    """
    Test that an EOA sender's balance is checked against `max_cost`,
    not `max_fee`: exactly `max_cost` approves, one wei less
    invalidates the transaction.
    """
    frames = [verify_frame()]
    sender = pre.fund_eoa(amount=0)
    fees = fee_budget(fork, sender, frames)
    max_gas, required_max_fee = fees.max_gas, fees.required_max_fee
    priority_fee = PRIORITY_FEE if budget == "surplus_with_tip" else 0
    full_tip = PRIORITY_FEE * max_gas
    max_fee = {
        "exact_budget": required_max_fee,
        "surplus_without_tip": required_max_fee + full_tip,
        "surplus_with_tip": required_max_fee + 2 * full_tip,
    }[budget]
    max_cost = fee_budget(
        fork,
        sender,
        frames,
        max_priority_fee_per_gas=priority_fee,
        max_fee=max_fee,
    ).max_cost
    assert (max_cost < max_fee) == (budget != "exact_budget")
    pre.fund_address(sender, max_cost + balance_delta)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=frames,
        signatures=[canonical_entry(sender)],
        max_fee=max_fee,
        max_priority_fee_per_gas=priority_fee,
        error=(
            TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
            if balance_delta
            else None
        ),
    )

    if balance_delta:
        post = Account(nonce=0, balance=max_cost + balance_delta)
    else:
        # With the full tip in the budget, the payer pays the base fee
        # and the tip on every unit of gas used.
        post = Account(
            nonce=1,
            balance=max_cost - tx.payer_gas_used() * (BASE_FEE + priority_fee),
        )
    state_test(
        env=Environment(base_fee_per_gas=BASE_FEE),
        pre=pre,
        tx=tx,
        post={sender: post},
    )


@pytest.mark.parametrize(
    "balance_delta",
    [
        pytest.param(0, id="balance_at_max_cost"),
        pytest.param(
            -1, id="balance_below_max_cost", marks=pytest.mark.exception_test
        ),
    ],
)
def test_payer_balance_covers_max_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    balance_delta: int,
) -> None:
    """
    Test that an EOA payer's balance must cover `max_cost`: exactly
    `max_cost` approves payment, one wei less invalidates the
    transaction.
    """
    sender = pre.fund_eoa()
    payer = pre.fund_eoa(amount=0)
    frames = [
        verify_frame(flags=Spec.APPROVE_EXECUTION),
        verify_frame(flags=Spec.APPROVE_PAYMENT, target=payer),
    ]
    signatures = [canonical_entry(sender), canonical_entry(payer)]
    max_cost = fee_budget(fork, sender, frames, signatures).max_cost
    pre.fund_address(payer, max_cost + balance_delta)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        payer=payer,
        frames=frames,
        signatures=signatures,
        error=(
            TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
            if balance_delta
            else None
        ),
    )

    if balance_delta:
        payer_post = Account(nonce=0, balance=max_cost + balance_delta)
    else:
        payer_post = Account(
            nonce=0, balance=max_cost - tx.payer_gas_used() * BASE_FEE
        )
    state_test(
        env=Environment(base_fee_per_gas=BASE_FEE),
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=0 if balance_delta else 1, balance_change=0),
            payer: payer_post,
        },
    )


@pytest.mark.parametrize(
    "balance_delta",
    [
        pytest.param(0, id="balance_after_transfer_at_max_cost"),
        pytest.param(
            -1,
            id="balance_after_transfer_below_max_cost",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_payment_approval_reads_balance_after_transfer(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    balance_delta: int,
) -> None:
    """
    Test that a payment approval reads the sender's balance after an
    earlier `SENDER` frame's transfer: what is left must cover
    `max_cost`. The sender's entry is given twice, since the
    payment-only frame reads index 1.
    """
    sender = pre.fund_eoa(amount=0)
    recipient = pre.deploy_contract(code=Op.STOP)
    transfer_value = 10**6
    frames = [
        verify_frame(flags=Spec.APPROVE_EXECUTION),
        sender_frame(target=recipient, value=transfer_value, code=Op.STOP),
        verify_frame(flags=Spec.APPROVE_PAYMENT),
    ]
    signatures = [canonical_entry(sender), canonical_entry(sender)]
    max_cost = fee_budget(fork, sender, frames, signatures).max_cost
    pre.fund_address(sender, transfer_value + max_cost + balance_delta)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=frames,
        signatures=signatures,
        error=(
            TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
            if balance_delta
            else None
        ),
    )

    if balance_delta:
        post = {
            sender: Account(
                nonce=0, balance=transfer_value + max_cost + balance_delta
            ),
            recipient: Account(balance=0),
        }
    else:
        post = {
            sender: Account(
                nonce=1, balance=max_cost - tx.payer_gas_used() * BASE_FEE
            ),
            recipient: Account(balance=transfer_value),
        }
    state_test(
        env=Environment(base_fee_per_gas=BASE_FEE),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "top_up",
    [
        pytest.param(1, id="topped_up_to_max_cost"),
        pytest.param(0, id="not_topped_up", marks=pytest.mark.exception_test),
    ],
)
def test_payment_approval_reads_balance_after_top_up(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    top_up: int,
) -> None:
    """
    Test that a payment approval reads the payer's balance after an
    earlier frame tops it up by one wei to exactly `max_cost`; without
    the top-up the approval is refused.
    """
    sender = pre.fund_eoa()
    payer = pre.fund_eoa(amount=0)
    donor_code = (
        Op.CALL(address=payer, value=top_up, value_transfer=top_up > 0)
        + Op.STOP
    )
    donor_funds = 10**18
    donor = pre.deploy_contract(code=donor_code, balance=donor_funds)
    # A `CALL` with value adds the stipend to the gas it forwards. The
    # payer has no code, so all of it comes back to the donor's frame,
    # which therefore spends the stipend less than the `CALL` charges.
    stipend = fork.call_value_stipend() if top_up else 0
    frames = [
        verify_frame(flags=Spec.APPROVE_EXECUTION),
        default_frame(
            target=donor,
            execution_gas=donor_code.execution_cost(fork) - stipend,
        ),
        # The donor's `CALL` has already accessed the payer.
        verify_frame(flags=Spec.APPROVE_PAYMENT, target=payer, warm=True),
    ]
    signatures = [canonical_entry(sender), canonical_entry(payer)]
    max_cost = fee_budget(fork, sender, frames, signatures).max_cost
    pre.fund_address(payer, max_cost - 1)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        payer=payer,
        frames=frames,
        signatures=signatures,
        error=(
            None
            if top_up
            else TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
        ),
    )

    if top_up:
        payer_post = Account(
            nonce=0, balance=max_cost - tx.payer_gas_used() * BASE_FEE
        )
    else:
        payer_post = Account(nonce=0, balance=max_cost - 1)
    state_test(
        env=Environment(base_fee_per_gas=BASE_FEE),
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1 if top_up else 0, balance_change=0),
            payer: payer_post,
            donor: Account(balance=donor_funds - top_up),
        },
    )
