"""
Payer balance tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

A frame approving payment collects the transaction's `max_cost` from its
resolved target on the spot (§APPROVE Behavior: "Increment the sender's
nonce, set `payer = resolved_target`, and collect the transaction's
`max_cost` from `payer`."). Before that, the approval is refused when
the target cannot cover it:

- `APPROVE_PAYMENT`: "If `resolved_target` has insufficient balance,
  revert the current call frame."
- `APPROVE_EXECUTION_AND_PAYMENT`: "If `resolved_target` has
  insufficient balance, revert the current call frame."

The amount the balance must cover is `max_cost`, the amount then
collected (§Fee budget: "the amount `max_cost` collected from the payer
on approval"), not the `max_fee` budget, which the transaction checks
against the base fees alone (§Fee budget: "The transaction is invalid if
`tx.fees.max_fee < required_max_fee`. This check depends only on the
transaction and the including block's base fees and is performed before
any frame executes."). `APPROVE` reads the balance when it runs, so
frames before it that move value change the verdict.

Every approval here goes through the default code of an EOA, whose
`VERIFY` frame reverts when its `APPROVE` is refused, and a reverting
`VERIFY` frame makes the transaction invalid.
"""

from typing import List

import pytest
from execution_testing import (
    EOA,
    SECP256K1_SIGNATURE_LENGTH,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Fork,
    FrameSignature,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
)

from .helpers import (
    FrameCase,
    FrameTransaction,
    default_frame,
    sender_frame,
    verify_frame,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

BASE_FEE = 7
"""Base fee of the block every transaction lands in."""

PRIORITY_FEE = 5
"""Tip per gas of the cases that ask for one."""

EXEC_ERROR = TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
"""A `VERIFY` frame failed, which invalidates the transaction."""

TRANSFER_VALUE = 10**6
"""Value a `SENDER` frame moves out of the payer before it approves."""

DONOR_FUNDS = 10**18
"""Balance of the contract that tops the payer up."""


def entry(account: EOA) -> FrameSignature:
    """
    Return the canonical secp256k1 entry of `account`, which the default
    code of a frame targeting `account` accepts.
    """
    return FrameSignature(
        scheme=Spec.SCHEME_SECP256K1,
        signer=Bytes(account),
        secret_key=account.key,
    )


def worst_case_gas(
    fork: Fork,
    sender: Address,
    frames: List[FrameCase],
    signatures: List[FrameSignature],
) -> int:
    """
    Return the transaction's `max_gas`.

    Every entry has an empty `msg`, so only the length of its raw bytes
    enters the cost, and the entries can be priced before they are
    signed. The sender prices a value-bearing frame's transfer cost.
    """
    priced = [
        signature.model_copy(
            update={"signature": Bytes(bytes(SECP256K1_SIGNATURE_LENGTH))}
        )
        for signature in signatures
    ]
    return fork.frame_transaction_intrinsic_cost_calculator()(
        frames=frames, signatures=priced, sender=sender
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
@pytest.mark.parametrize(
    "fee_budget",
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
    fee_budget: str,
    balance_delta: int,
) -> None:
    """
    Fund an EOA sender with exactly the transaction's `max_cost`, or one
    wei less, and approve execution and payment through its default
    code.

    EIP-8141 §APPROVE Behavior, `APPROVE_EXECUTION_AND_PAYMENT`: "If
    `resolved_target` has insufficient balance, revert the current call
    frame." The balance is compared with `max_cost` (§Fee budget:
    "`max_cost = required_max_fee + max_priority_fee`"), so a `max_fee`
    above the sender's balance does not matter on its own (§Fee budget:
    "It guarantees `max_cost <= tx.fees.max_fee`").
    """
    frames = [verify_frame()]
    sender = pre.fund_eoa(amount=0)
    max_gas = worst_case_gas(fork, sender, frames, [entry(sender)])
    required_max_fee = max_gas * BASE_FEE
    priority_fee = PRIORITY_FEE if fee_budget == "surplus_with_tip" else 0
    full_tip = PRIORITY_FEE * max_gas
    max_fee = {
        "exact_budget": required_max_fee,
        "surplus_without_tip": required_max_fee + full_tip,
        "surplus_with_tip": required_max_fee + 2 * full_tip,
    }[fee_budget]
    max_cost = required_max_fee + min(
        priority_fee * max_gas, max_fee - required_max_fee
    )
    assert (max_cost < max_fee) == (fee_budget != "exact_budget")
    pre.fund_address(sender, max_cost + balance_delta)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=frames,
        signatures=[entry(sender)],
        max_fee=max_fee,
        max_priority_fee_per_gas=priority_fee,
        error=EXEC_ERROR if balance_delta else None,
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
    Fund an EOA payer with exactly the transaction's `max_cost`, or one
    wei less, and approve payment through its default code after the
    sender approved execution. The sender's own balance covers
    `max_cost`, so only the payer's balance can refuse the approval.

    EIP-8141 §APPROVE Behavior, `APPROVE_PAYMENT`: "If `resolved_target`
    has insufficient balance, revert the current call frame."
    """
    sender = pre.fund_eoa()
    payer = pre.fund_eoa(amount=0)
    frames = [
        verify_frame(flags=Spec.APPROVE_EXECUTION),
        verify_frame(flags=Spec.APPROVE_PAYMENT, target=payer),
    ]
    signatures = [entry(sender), entry(payer)]
    max_cost = worst_case_gas(fork, sender, frames, signatures) * BASE_FEE
    pre.fund_address(payer, max_cost + balance_delta)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        payer=payer,
        frames=frames,
        signatures=signatures,
        error=EXEC_ERROR if balance_delta else None,
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
    Approve execution, transfer value out of the sender in a `SENDER`
    frame, then approve payment by the sender in a later frame. The
    sender's balance before the transaction covers both, but what is
    left after the transfer is exactly `max_cost`, or one wei less.

    The payment-only frame reads the entry at index 1, so the sender's
    entry is given twice.

    EIP-8141 §APPROVE Behavior, `APPROVE_PAYMENT`: "If `resolved_target`
    has insufficient balance, revert the current call frame." The check
    is part of the `APPROVE` instruction, so it reads the balance the
    target holds when `APPROVE` runs, after the earlier frames.
    """
    sender = pre.fund_eoa(amount=0)
    recipient = pre.deploy_contract(code=Op.STOP)
    frames = [
        verify_frame(flags=Spec.APPROVE_EXECUTION),
        sender_frame(target=recipient, value=TRANSFER_VALUE, code=Op.STOP),
        verify_frame(flags=Spec.APPROVE_PAYMENT),
    ]
    signatures = [entry(sender), entry(sender)]
    max_cost = worst_case_gas(fork, sender, frames, signatures) * BASE_FEE
    pre.fund_address(sender, TRANSFER_VALUE + max_cost + balance_delta)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=frames,
        signatures=signatures,
        error=EXEC_ERROR if balance_delta else None,
    )

    if balance_delta:
        post = {
            sender: Account(
                nonce=0, balance=TRANSFER_VALUE + max_cost + balance_delta
            ),
            recipient: Account(balance=0),
        }
    else:
        post = {
            sender: Account(
                nonce=1, balance=max_cost - tx.payer_gas_used() * BASE_FEE
            ),
            recipient: Account(balance=TRANSFER_VALUE),
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
    Fund an EOA payer with one wei less than `max_cost`, and let a
    `DEFAULT` frame running before the payer's approval send it one wei,
    or nothing.

    EIP-8141 §APPROVE Behavior, `APPROVE_PAYMENT`: "If `resolved_target`
    has insufficient balance, revert the current call frame." The check
    is part of the `APPROVE` instruction, so it reads the balance the
    target holds when `APPROVE` runs, after the earlier frames.
    """
    sender = pre.fund_eoa()
    payer = pre.fund_eoa(amount=0)
    donor = pre.deploy_contract(
        code=Op.CALL(address=payer, value=top_up) + Op.STOP,
        balance=DONOR_FUNDS,
    )
    frames = [
        verify_frame(flags=Spec.APPROVE_EXECUTION),
        default_frame(target=donor),
        verify_frame(flags=Spec.APPROVE_PAYMENT, target=payer),
    ]
    signatures = [entry(sender), entry(payer)]
    max_cost = worst_case_gas(fork, sender, frames, signatures) * BASE_FEE
    pre.fund_address(payer, max_cost - 1)

    tx = Transaction(
        sender=sender,
        frames=frames,
        signatures=signatures,
        error=None if top_up else EXEC_ERROR,
    )

    state_test(
        env=Environment(base_fee_per_gas=BASE_FEE),
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1 if top_up else 0),
            payer: Account(nonce=0),
            donor: Account(balance=DONOR_FUNDS - top_up),
        },
    )


@pytest.mark.exception_test
def test_max_fee_checked_before_frames(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Send a transaction whose `max_fee` is one wei below its base fee cost
    and whose only `VERIFY` frame would revert, and check it is rejected
    for its fee budget rather than for the failed frame.

    EIP-8141 §Fee budget: "The transaction is invalid if
    `tx.fees.max_fee < required_max_fee`. This check depends only on the
    transaction and the including block's base fees and is performed
    before any frame executes."
    """
    sender = pre.deploy_contract(code=Op.REVERT(0, 0), balance=10**18)
    frames = [verify_frame()]
    max_gas = fork.frame_transaction_intrinsic_cost_calculator()(frames=frames)

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=frames,
        max_fee=max_gas * BASE_FEE - 1,
        error=TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS,
    )

    state_test(
        env=Environment(base_fee_per_gas=BASE_FEE),
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=1, balance=10**18)},
    )
