"""
Payer settlement tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

The payer escrows `max_cost` when it approves payment, before any later
frame runs, and gets back only what settlement leaves of it: the gas
used at the base fee and the blob gas at the blob base fee are burned,
the tip goes to the coinbase. A sponsor pays all of it, the sender none;
a sender paying for itself has only what the escrow left to send as
value.
"""

from typing import List

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Fork,
    Hash,
    Op,
    StateTestFiller,
    add_kzg_version,
)

from ...cancun.eip4844_blobs.spec import SpecHelpers as BlobSpecHelpers
from .helpers import (
    BASE_FEE,
    PRIORITY_FEE,
    FrameCase,
    FrameTransaction,
    Outcome,
    default_frame,
    fee_budget,
    sender_frame,
    sponsored_signatures,
    verify_frame,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

TRANSFER_VALUE = 10**6
"""Value a `SENDER` frame sends."""


def sponsored_frames(fork: Fork, payer: Address, last: FrameCase) -> list:
    """
    Return frames where the sender approves execution, `payer` approves
    payment through its default code, and `last` runs; both approving
    frames are budgeted exactly their entry access.
    """
    entry = fork.frame_entry_gas_calculator()
    return [
        verify_frame(
            flags=Spec.APPROVE_EXECUTION,
            gas_limit=entry(target_warm=True),
            state_gas_limit=0,
        ),
        verify_frame(
            flags=Spec.APPROVE_PAYMENT,
            target=payer,
            gas_limit=entry(target_warm=False),
            state_gas_limit=0,
        ),
        last,
    ]


def test_sponsor_pays_its_whole_escrow(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Charge a sponsor its whole escrow when every frame spends its whole
    budget.

    EIP-8141 `APPROVE` (`APPROVE_PAYMENT`): "Increment the sender's
    nonce, set `payer = resolved_target`, and collect the transaction's
    `max_cost` from `payer`"; "Transaction settlement": "`payer_refund =
    max_cost - base_fee_paid - priority_fee_paid`", returned to "the
    `resolved_target` that called `APPROVE(APPROVE_PAYMENT)`".

    The sponsor holds `max_cost` plus one wei; the transaction asks for
    no tip, and its last frame halts, so the gas used is `max_gas` and
    the refund is zero. The sponsor ends with exactly one wei and its
    nonce untouched, and the sender's balance is untouched. With no
    spare wei the sponsor would end with nonce 0, no balance and no
    code, an empty account the EIP does not say whether to remove, so
    that case is not tested.
    """
    sender = pre.fund_eoa()
    payer = pre.fund_eoa(amount=0)
    halting = pre.deploy_contract(code=Op.INVALID)
    frames = sponsored_frames(
        fork,
        payer,
        default_frame(
            target=halting,
            gas_limit=5_000,
            state_gas_limit=0,
            outcome=Outcome.HALT,
        ),
    )
    fees = fee_budget(
        fork, sender, frames, sponsored_signatures(sender, payer)
    )
    max_cost = fees.max_cost
    pre.fund_address(payer, max_cost + 1)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        payer=payer,
        frames=frames,
        signatures=sponsored_signatures(sender, payer),
        max_fee=max_cost,
        max_priority_fee_per_gas=0,
    )
    # The premise: every unit of `max_gas` is used.
    assert tx.payer_gas_used() == fees.max_gas

    state_test(
        env=Environment(base_fee_per_gas=BASE_FEE),
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1, balance_change=0),
            payer: Account(nonce=0, balance=1),
        },
    )


@pytest.mark.parametrize(
    "shortfall",
    [
        pytest.param(0, id="balance_covers_escrow_and_value"),
        pytest.param(1, id="balance_one_wei_short"),
    ],
)
def test_value_after_escrow(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    shortfall: int,
) -> None:
    """
    Check a self-paying sender's frame value against what its escrow
    left.

    EIP-8141 `APPROVE` (`APPROVE_EXECUTION_AND_PAYMENT`): "Set
    `sender_approved = true`, increment the sender's nonce, set `payer
    = resolved_target`, and collect the transaction's `max_cost` from
    `payer`", in the `VERIFY` frame, before the `SENDER` frame runs;
    "Behavior": "if the caller does not have sufficient balance to
    transfer `frame.value`, the frame reverts, consuming the gas
    charged so far".

    The sender holds its `max_cost` plus the value its `SENDER` frame
    sends, or one wei less. With the full amount the transfer succeeds;
    one wei short, the frame reverts after its target's cold access
    and the transaction stays valid. A client checking the value
    against the balance before the escrow sends it in both cases.
    """
    sender = pre.fund_eoa(amount=0)
    recipient = pre.fund_eoa(amount=1)
    entry = fork.frame_entry_gas_calculator()
    frames = [
        verify_frame(gas_limit=entry(target_warm=True), state_gas_limit=0),
        sender_frame(
            target=recipient,
            value=TRANSFER_VALUE,
            gas_limit=entry(target_warm=False),
            state_gas_limit=0,
            outcome=Outcome.REVERT if shortfall else Outcome.SUCCESS,
        ),
    ]
    max_cost = fee_budget(fork, sender, frames).max_cost
    pre.fund_address(sender, max_cost + TRANSFER_VALUE - shortfall)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=frames,
        max_fee=max_cost,
        max_priority_fee_per_gas=0,
    )
    refund = max_cost - tx.payer_gas_used() * BASE_FEE
    sent = 0 if shortfall else TRANSFER_VALUE

    state_test(
        env=Environment(base_fee_per_gas=BASE_FEE),
        pre=pre,
        tx=tx,
        post={
            sender: Account(
                nonce=1,
                balance=refund + TRANSFER_VALUE - shortfall - sent,
            ),
            recipient: Account(balance=1 + sent),
        },
    )


@pytest.mark.parametrize(
    "blob_count",
    [
        pytest.param(1, id="one_blob"),
        pytest.param(2, id="two_blobs"),
    ],
)
def test_sponsor_pays_blob_fee(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    blob_count: int,
) -> None:
    """
    Charge a sponsor, not the sender, the blob fee of a blob-carrying
    transaction, along with the gas and the tip.

    EIP-8141 "Blob handling": "the payer is also the blob-fee payer ...
    The payer is charged `blob_gas * blob_base_fee`, which is burned";
    "Transaction settlement": "`base_fee_paid = gas_used *
    base_fee_per_gas + blob_gas * blob_base_fee`", "`priority_fee_paid
    = min(tx.fees.max_priority_fee_per_gas * gas_used, max_cost -
    base_fee_paid)`", credited to the coinbase.

    The blob base fee is well above one wei, and the budget pays the
    full tip. The sponsor's balance drops by the gas used at the base
    fee, the blob gas at the blob base fee and the tip; the sender's
    balance does not move; the coinbase receives the tip alone.
    """
    sender = pre.fund_eoa()
    payer = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.STOP)
    frames = sponsored_frames(
        fork, payer, default_frame(target=target, state_gas_limit=0)
    )
    blob_gas = blob_count * fork.blob_gas_per_blob()
    excess_blob_gas = (
        BlobSpecHelpers.get_min_excess_blob_gas_for_blob_gas_price(
            fork=fork, blob_gas_price=1_000
        )
    )
    blob_base_fee = fork.blob_gas_price_calculator()(
        excess_blob_gas=excess_blob_gas
    )
    assert blob_base_fee > 1
    max_fee = fee_budget(
        fork,
        sender,
        frames,
        sponsored_signatures(sender, payer),
        max_priority_fee_per_gas=PRIORITY_FEE,
        blob_count=blob_count,
        excess_blob_gas=excess_blob_gas,
    ).max_cost
    blob_hashes: List[Hash] = add_kzg_version(
        list(range(1, blob_count + 1)), 1
    )

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        payer=payer,
        frames=frames,
        signatures=sponsored_signatures(sender, payer),
        max_fee=max_fee,
        max_priority_fee_per_gas=PRIORITY_FEE,
        blob_versioned_hashes=blob_hashes,
    )
    gas_used = tx.payer_gas_used()
    tip = PRIORITY_FEE * gas_used
    paid = gas_used * BASE_FEE + blob_gas * blob_base_fee + tip

    env = Environment(
        base_fee_per_gas=BASE_FEE, excess_blob_gas=excess_blob_gas
    )
    state_test(
        env=env,
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1, balance_change=0),
            payer: Account(nonce=0, balance_change=-paid),
            env.fee_recipient: Account(balance=tip),
        },
    )
