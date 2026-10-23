"""
State gas pool tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Each frame's state gas pool is seeded from its declared budget and
shared by every call depth within the frame. An `SSTORE` returning a
slot created earlier in the transaction to its transaction-start value
refills the charge to the frame that paid it: the executing frame's
pool when the owner is still executing, the owner's receipt otherwise.
A charge exceeding the pool halts exceptionally, and `APPROVE` charges
the sender's account creation to the approving frame's pool.
"""

from typing import Any, Dict, List, Tuple

import pytest
from execution_testing import (
    DEFAULT_FRAME_STATE_GAS_LIMIT,
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Conditional,
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
    Outcome,
    default_frame,
    sender_frame,
    verify_frame,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT_CREATED = 0x01
"""Storage slot created — and possibly cleared again — under test."""

SLOT_USED_BEFORE = 0x02
"""Slot recording the owner frame's attributed state gas pre-refill."""

SLOT_USED_AFTER = 0x03
"""Slot recording the owner frame's attributed state gas post-refill."""

SLOT_POOL = 0x04
"""Slot recording the executing frame's remaining state gas pool."""

SLOT_OWNER_USED = 0x06
"""Probe slot recording the creating frame's attributed state gas."""

SLOT_EDITOR_USED = 0x07
"""
Probe slot recording the refilling frame's attributed state gas, plus
one so the expected zero readback is distinguishable from a slot never
written.
"""

SLOT_STATUS = 0x08
"""
Probe slot recording a frame's receipt status, plus one so the
expected `FAILURE` readback is distinguishable from a slot never
written.
"""

SLOT_SECOND = 0x09
"""Second storage slot a frame creates from its own state gas pool."""

SPENT_SENDER_BALANCE = 10**15
"""Balance a sender transfers away before its payment is approved."""

UNFUNDED_SENDERS = pytest.mark.parametrize(
    "sender_state",
    [
        pytest.param("absent", id="sender_absent"),
        pytest.param("emptied", id="sender_emptied_by_earlier_frame"),
    ],
)
"""
The two ways a sender has no account when its payment is approved:
none in the pre-state, or one an earlier frame spent down to empty —
present in the state but empty, so `APPROVE` still creates it.
"""


def unfunded_sender(
    pre: Alloc, sender_state: str
) -> Tuple[EOA, List[FrameCase], Address | None]:
    """
    Return the sender, the frames that run between its execution and
    payment approvals, and the account those frames pay, if any.
    """
    if sender_state == "absent":
        return pre.fund_eoa(amount=0), [], None
    elif sender_state == "emptied":
        sender = pre.fund_eoa(amount=SPENT_SENDER_BALANCE)
        recipient = pre.fund_eoa(amount=1)
        spend = sender_frame(target=recipient, value=SPENT_SENDER_BALANCE)
        return sender, [spend], recipient
    else:
        raise ValueError(f"unknown sender state: {sender_state}")


def test_same_frame_refill(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Refill a state charge within the frame that paid it.

    The frame creates a slot, clears it back to its transaction-start
    value, and then records its pool: the refill credits the pool, so
    the recording — itself a fresh write — reads the full budget back,
    and the frame's receipt attributes only the recording's charge.
    """
    sender = pre.fund_eoa()
    create = Op.SSTORE(SLOT_CREATED, 1)
    clear = Op.SSTORE(
        SLOT_CREATED,
        0,
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )
    observe_pool = Op.SSTORE(
        SLOT_POOL, Op.TXPARAM(Spec.TXPARAM_STATE_GAS_LEFT)
    )
    worker_code = create + clear + observe_pool + Op.STOP
    worker = pre.deploy_contract(code=worker_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        # The clearing write refunds execution gas this test does not
        # price, so the transaction total is left unpinned.
        settle=False,
        frames=[
            verify_frame(),
            default_frame(
                target=worker,
                code=worker_code,
                state_gas_used=observe_pool.state_cost(fork),
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            worker: Account(
                storage={
                    SLOT_CREATED: 0,
                    SLOT_POOL: DEFAULT_FRAME_STATE_GAS_LIMIT,
                }
            ),
        },
    )


def test_cross_frame_refill(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Refill a state charge from a later frame than the one that paid it.

    A first frame creates a slot; a second frame clears it back to its
    transaction-start value. The refill lowers the owner frame's
    receipt — observed live through `FRAMEPARAM` before and after —
    and credits nothing to the executing frame's pool.
    """
    sender = pre.fund_eoa()
    fresh_write_state_cost = Op.SSTORE(SLOT_CREATED, 1).state_cost(fork)

    observe_before = Op.SSTORE(
        SLOT_USED_BEFORE,
        Op.FRAMEPARAM(1, Spec.FRAMEPARAM_STATE_GAS_USED),
    )
    refill = Op.SSTORE(
        SLOT_CREATED,
        0,
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )
    # Recorded with one added, so the expected zero readback is
    # distinguishable from a slot never written.
    observe_after = Op.SSTORE(
        SLOT_USED_AFTER,
        Op.ADD(1, Op.FRAMEPARAM(1, Spec.FRAMEPARAM_STATE_GAS_USED)),
    )
    observe_pool = Op.SSTORE(
        SLOT_POOL, Op.TXPARAM(Spec.TXPARAM_STATE_GAS_LEFT)
    )
    worker_code = Conditional(
        condition=Op.ISZERO(Op.CALLDATALOAD(0)),
        if_true=Op.SSTORE(SLOT_CREATED, 1) + Op.STOP,
        if_false=observe_before
        + refill
        + observe_after
        + observe_pool
        + Op.STOP,
    )
    worker = pre.deploy_contract(code=worker_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            # The owner's attribution is gone: the refill returned its
            # charge at settlement.
            default_frame(
                target=worker,
                pin_gas=False,
                state_gas_used=0,
            ),
            # The refilling frame pays only for its three fresh
            # recording slots; the refill credits it nothing.
            default_frame(
                target=worker,
                data=b"\x01",
                pin_gas=False,
                state_gas_used=3 * fresh_write_state_cost,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            worker: Account(
                storage={
                    SLOT_CREATED: 0,
                    SLOT_USED_BEFORE: fresh_write_state_cost,
                    SLOT_USED_AFTER: 1,
                    SLOT_POOL: DEFAULT_FRAME_STATE_GAS_LIMIT
                    - 2 * fresh_write_state_cost,
                }
            ),
        },
    )


@pytest.mark.parametrize(
    "state_gas_limit_delta",
    [
        pytest.param(0, id="exact_budget"),
        pytest.param(-1, id="one_below"),
    ],
)
def test_state_gas_exhaustion(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    state_gas_limit_delta: int,
) -> None:
    """
    Drive a frame's state gas budget across the exact cost of its one
    storage creation.

    The exact budget succeeds and consumes the whole pool; one unit
    below halts the frame exceptionally — the write is rolled back,
    the receipt reports the whole execution budget and zero state gas,
    and the transaction stays valid.
    """
    sender = pre.fund_eoa()
    worker_code = Op.SSTORE(SLOT_CREATED, 1) + Op.STOP
    worker = pre.deploy_contract(code=worker_code)

    succeeds = state_gas_limit_delta >= 0

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=worker,
                code=worker_code,
                state_gas_limit_delta=state_gas_limit_delta,
                outcome=Outcome.SUCCESS if succeeds else Outcome.HALT,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            worker: Account(storage={SLOT_CREATED: 1 if succeeds else 0}),
        },
    )


@UNFUNDED_SENDERS
def test_approve_creates_sender(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    sender_state: str,
) -> None:
    """
    Approve payment for a sender whose account does not exist.

    Incrementing the nonce creates the sender account, and `APPROVE`
    charges the account creation to the approving frame's state gas
    pool — here inside the payer's protocol default code, whose only
    execution charge is the payer's cold access at frame entry. The
    pool holds exactly the charge; the unaffordable test below is the
    same transaction one unit short.
    """
    sender, spend_frames, recipient = unfunded_sender(pre, sender_state)
    payer = pre.fund_eoa()
    sender_creation = fork.gas_costs().NEW_ACCOUNT

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        payer=payer,
        frames=[
            verify_frame(flags=Spec.APPROVE_EXECUTION),
            *spend_frames,
            verify_frame(
                flags=Spec.APPROVE_PAYMENT,
                target=payer,
                state_gas_limit=sender_creation,
                state_gas_used=sender_creation,
            ),
        ],
        signatures=[
            FrameSignature(scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)),
            FrameSignature(
                scheme=Spec.SCHEME_SECP256K1,
                signer=Bytes(payer),
                secret_key=payer.key,
            ),
        ],
    )

    post: Dict[Address, Account] = {sender: Account(nonce=1, balance=0)}
    if recipient is not None:
        post[recipient] = Account(balance=1 + SPENT_SENDER_BALANCE)
    state_test(pre=pre, tx=tx, post=post)


@UNFUNDED_SENDERS
@pytest.mark.exception_test
def test_approve_sender_creation_unaffordable(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    sender_state: str,
) -> None:
    """
    Reject a frame transaction whose payment approval cannot cover the
    sender's account creation.

    The approving `VERIFY` frame declares one unit of state gas less
    than the account creation, so the `APPROVE` inside the payer's
    protocol default code halts the frame exceptionally, with no
    approval effects — and a failing `VERIFY` frame invalidates the
    transaction.
    """
    sender, spend_frames, recipient = unfunded_sender(pre, sender_state)
    payer = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(flags=Spec.APPROVE_EXECUTION),
            *spend_frames,
            verify_frame(
                flags=Spec.APPROVE_PAYMENT,
                target=payer,
                state_gas_limit=fork.gas_costs().NEW_ACCOUNT - 1,
            ),
        ],
        signatures=[
            FrameSignature(scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)),
            FrameSignature(
                scheme=Spec.SCHEME_SECP256K1,
                signer=Bytes(payer),
                secret_key=payer.key,
            ),
        ],
        error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
    )

    post: Dict[Address, Account] = {}
    if recipient is not None:
        post = {
            sender: Account(nonce=0, balance=SPENT_SENDER_BALANCE),
            recipient: Account(balance=1),
        }
    state_test(pre=pre, tx=tx, post=post)


def test_refill_after_intermediate_modification(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Return a slot to its transaction-start value after an intermediate
    modification by another frame.

    The second frame's write changes an already-dirty slot: it charges
    no state gas and leaves the outstanding charge's owner untouched.
    The third frame's return to the transaction-start value therefore
    still refills the creating frame, although the third frame never
    observed the value that frame wrote.
    """
    sender = pre.fund_eoa()
    fresh_write_state_cost = Op.SSTORE(SLOT_CREATED, 1).state_cost(fork)

    modify = Op.SSTORE(
        SLOT_CREATED,
        2,
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=2,
    )
    clear = Op.SSTORE(
        SLOT_CREATED,
        0,
        key_warm=True,
        original_value=0,
        current_value=2,
        new_value=0,
    )
    observe_owner = Op.SSTORE(
        SLOT_USED_AFTER,
        Op.ADD(1, Op.FRAMEPARAM(1, Spec.FRAMEPARAM_STATE_GAS_USED)),
    )
    worker_code = Conditional(
        condition=Op.ISZERO(Op.CALLDATALOAD(0)),
        if_true=Op.SSTORE(SLOT_CREATED, 1) + Op.STOP,
        if_false=Conditional(
            condition=Op.EQ(Op.CALLDATALOAD(0), 1),
            if_true=modify + Op.STOP,
            if_false=clear + observe_owner + Op.STOP,
        ),
    )
    worker = pre.deploy_contract(code=worker_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            # Frame 0: approve execution and payment.
            verify_frame(),
            # Frame 1: create the slot (0 -> 1). The creation's
            # attribution is gone: the third frame's refill returned it
            # at settlement.
            default_frame(
                target=worker,
                pin_gas=False,
                state_gas_used=0,
            ),
            # Frame 2: modify the dirty slot (1 -> 2), which charges no
            # state gas.
            default_frame(
                target=worker,
                data=(1).to_bytes(32, "big"),
                pin_gas=False,
                state_gas_used=0,
            ),
            # Frame 3: return the slot to its start value (2 -> 0) and
            # record frame 1's attribution. Only the recording write is
            # charged; the refill credits the owner, not this frame.
            default_frame(
                target=worker,
                data=(2).to_bytes(32, "big"),
                pin_gas=False,
                state_gas_used=fresh_write_state_cost,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            worker: Account(storage={SLOT_CREATED: 0, SLOT_USED_AFTER: 1}),
        },
    )


def test_batch_unroll_restores_refilled_receipt(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Unroll an atomic batch whose frame refilled a pre-batch receipt.

    A batch frame returns a slot created before the batch to its
    transaction-start value, lowering the creating frame's receipt.
    The batch's terminating frame reverts, and the unroll restores the
    receipt edit together with the state: a later frame reads the
    creating frame's full attribution back, while the unrolled frame's
    re-appended receipt keeps its status with its state gas zeroed.
    """
    sender = pre.fund_eoa()
    fresh_write_state_cost = Op.SSTORE(SLOT_CREATED, 1).state_cost(fork)

    modify = Op.SSTORE(
        SLOT_CREATED,
        2,
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=2,
    )
    clear = Op.SSTORE(
        SLOT_CREATED,
        0,
        key_warm=True,
        original_value=0,
        current_value=2,
        new_value=0,
    )
    worker_code = Conditional(
        condition=Op.ISZERO(Op.CALLDATALOAD(0)),
        if_true=Op.SSTORE(SLOT_CREATED, 1) + Op.STOP,
        if_false=Conditional(
            condition=Op.EQ(Op.CALLDATALOAD(0), 1),
            if_true=modify + Op.STOP,
            if_false=clear + Op.STOP,
        ),
    )
    worker = pre.deploy_contract(code=worker_code)
    reverter = pre.deploy_contract(code=Op.REVERT(0, 0))
    probe = pre.deploy_contract(
        code=Op.SSTORE(
            SLOT_OWNER_USED,
            Op.FRAMEPARAM(1, Spec.FRAMEPARAM_STATE_GAS_USED),
        )
        + Op.SSTORE(
            SLOT_EDITOR_USED,
            Op.ADD(1, Op.FRAMEPARAM(3, Spec.FRAMEPARAM_STATE_GAS_USED)),
        )
        + Op.SSTORE(
            SLOT_STATUS,
            Op.ADD(1, Op.FRAMEPARAM(4, Spec.FRAMEPARAM_STATUS)),
        )
        + Op.STOP
    )

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            # Frame 0: approve execution and payment.
            verify_frame(),
            # Frame 1: create the slot (0 -> 1). The unroll restored
            # the refill the batch frame applied to this receipt.
            default_frame(
                target=worker,
                pin_gas=False,
                state_gas_used=fresh_write_state_cost,
            ),
            # Frame 2: modify the dirty slot (1 -> 2).
            default_frame(
                target=worker,
                data=(1).to_bytes(32, "big"),
                pin_gas=False,
                state_gas_used=0,
            ),
            # Frame 3: open the batch and return the slot to its
            # start value (2 -> 0), refilling frame 1's receipt.
            default_frame(
                flags=Spec.ATOMIC_BATCH_FLAG,
                target=worker,
                data=(2).to_bytes(32, "big"),
                outcome=Outcome.UNROLLED,
                pin_gas=False,
            ),
            # Frame 4: terminate the batch with a revert, unrolling it.
            default_frame(
                target=reverter,
                outcome=Outcome.REVERT,
                pin_gas=False,
            ),
            # Frame 5: record frame 1's and frame 3's attributions and
            # frame 4's status after the unroll.
            default_frame(
                target=probe,
                pin_gas=False,
                state_gas_used=3 * fresh_write_state_cost,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            # The unroll undid the batch frame's clearing write, so
            # the intermediate modification survives.
            worker: Account(storage={SLOT_CREATED: 2}),
            probe: Account(
                storage={
                    SLOT_OWNER_USED: fresh_write_state_cost,
                    SLOT_EDITOR_USED: 1,
                    SLOT_STATUS: 1,
                }
            ),
        },
    )


def test_frame_revert_restores_refilled_receipt(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Revert a frame that refilled an earlier frame's receipt.

    A reverting frame's rollback extends over the edits it made to
    earlier receipts: the creating frame's attribution is restored,
    and the reverting frame's own receipt reports zero state gas.
    """
    sender = pre.fund_eoa()
    fresh_write_state_cost = Op.SSTORE(SLOT_CREATED, 1).state_cost(fork)

    clear = Op.SSTORE(
        SLOT_CREATED,
        0,
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )
    worker_code = Conditional(
        condition=Op.ISZERO(Op.CALLDATALOAD(0)),
        if_true=Op.SSTORE(SLOT_CREATED, 1) + Op.STOP,
        if_false=clear + Op.REVERT(0, 0),
    )
    worker = pre.deploy_contract(code=worker_code)
    probe = pre.deploy_contract(
        code=Op.SSTORE(
            SLOT_OWNER_USED,
            Op.FRAMEPARAM(1, Spec.FRAMEPARAM_STATE_GAS_USED),
        )
        + Op.SSTORE(
            SLOT_EDITOR_USED,
            Op.ADD(1, Op.FRAMEPARAM(2, Spec.FRAMEPARAM_STATE_GAS_USED)),
        )
        + Op.SSTORE(
            SLOT_STATUS,
            Op.ADD(1, Op.FRAMEPARAM(2, Spec.FRAMEPARAM_STATUS)),
        )
        + Op.STOP
    )

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            # Frame 0: approve execution and payment.
            verify_frame(),
            # Frame 1: create the slot (0 -> 1). The revert restored
            # the refill the failing frame applied to this receipt.
            default_frame(
                target=worker,
                pin_gas=False,
                state_gas_used=fresh_write_state_cost,
            ),
            # Frame 2: return the slot to its start value (1 -> 0),
            # refilling frame 1's receipt, then revert.
            default_frame(
                target=worker,
                data=b"\x01",
                outcome=Outcome.REVERT,
                pin_gas=False,
            ),
            # Frame 3: record frame 1's and frame 2's attributions and
            # frame 2's status after the revert.
            default_frame(
                target=probe,
                pin_gas=False,
                state_gas_used=3 * fresh_write_state_cost,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            # The revert undid the clearing write.
            worker: Account(storage={SLOT_CREATED: 1}),
            probe: Account(
                storage={
                    SLOT_OWNER_USED: fresh_write_state_cost,
                    SLOT_EDITOR_USED: 1,
                    SLOT_STATUS: 1,
                }
            ),
        },
    )


def test_call_revert_restores_refilled_receipt(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Revert a call that refilled an earlier frame's receipt, inside a
    frame that succeeds.

    A call's rollback extends over the edits it made to earlier
    receipts, as a frame's does: the creating frame's attribution is
    restored. The refill never reached the executing frame's pool, so
    the rollback leaves that pool whole, and the frame can still create
    a slot from a budget of exactly one slot creation.
    """
    sender = pre.fund_eoa()
    fresh_write_state_cost = Op.SSTORE(SLOT_CREATED, 1).state_cost(fork)

    clear = Op.SSTORE(
        SLOT_CREATED,
        0,
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )
    worker_code = Conditional(
        condition=Op.ISZERO(Op.CALLDATALOAD(0)),
        if_true=Op.SSTORE(SLOT_CREATED, 1) + Op.STOP,
        if_false=Conditional(
            condition=Op.EQ(Op.CALLDATALOAD(0), 1),
            # Call this contract to clear the slot and revert, then
            # create a second slot.
            if_true=Op.MSTORE(0, 2)
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=Op.ADDRESS,
                    args_offset=0,
                    args_size=32,
                )
            )
            + Op.SSTORE(SLOT_SECOND, 1)
            + Op.STOP,
            if_false=clear + Op.REVERT(0, 0),
        ),
    )
    worker = pre.deploy_contract(code=worker_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            # Frame 0: approve execution and payment.
            verify_frame(),
            # Frame 1: create the slot (0 -> 1). The call's revert
            # restored the refill it applied to this receipt.
            default_frame(
                target=worker,
                pin_gas=False,
                state_gas_used=fresh_write_state_cost,
            ),
            # Frame 2: a call returns the slot to its start value
            # (1 -> 0), refilling frame 1's receipt, and reverts; the
            # frame then creates a second slot from its own pool.
            default_frame(
                target=worker,
                state_gas_limit=fresh_write_state_cost,
                data=(1).to_bytes(32, "big"),
                pin_gas=False,
                state_gas_used=fresh_write_state_cost,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            # The revert undid the clearing write.
            worker: Account(storage={SLOT_CREATED: 1, SLOT_SECOND: 1}),
        },
    )


@pytest.mark.parametrize(
    "reversion",
    ["reverted_call", "reverted_frame", "unrolled_batch"],
)
def test_reversion_restores_charge_ownership(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    reversion: str,
) -> None:
    """
    Restore a slot's charge ownership record that a reverted clearing
    write consumed.

    Returning a slot to its transaction-start value consumes the record
    of the frame that paid for its creation. When the clearing write is
    reverted, by its call, its frame or its atomic batch, the record
    comes back with it, so a later frame that clears the slot for good
    refills the frame that paid, not its own pool. That later frame
    then creates a second slot from a budget of exactly one slot
    creation, which its pool covers only if the refill went to the
    owner.
    """
    sender = pre.fund_eoa()
    fresh_write_state_cost = Op.SSTORE(SLOT_CREATED, 1).state_cost(fork)

    clear = Op.SSTORE(
        SLOT_CREATED,
        0,
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )
    worker_code = Conditional(
        condition=Op.ISZERO(Op.CALLDATALOAD(0)),
        if_true=Op.SSTORE(SLOT_CREATED, 1) + Op.STOP,
        if_false=Conditional(
            condition=Op.EQ(Op.CALLDATALOAD(0), 1),
            # Clear the slot for good and create a second one.
            if_true=clear + Op.SSTORE(SLOT_SECOND, 1) + Op.STOP,
            if_false=Conditional(
                condition=Op.EQ(Op.CALLDATALOAD(0), 2),
                # Clear the slot and revert.
                if_true=clear + Op.REVERT(0, 0),
                if_false=Conditional(
                    condition=Op.EQ(Op.CALLDATALOAD(0), 3),
                    # Clear the slot and return.
                    if_true=clear + Op.STOP,
                    # Call this contract to clear the slot and revert.
                    if_false=Op.MSTORE(0, 2)
                    + Op.POP(
                        Op.CALL(
                            gas=Op.GAS,
                            address=Op.ADDRESS,
                            args_offset=0,
                            args_size=32,
                        )
                    )
                    + Op.STOP,
                ),
            ),
        ),
    )
    worker = pre.deploy_contract(code=worker_code)
    reverter = pre.deploy_contract(code=Op.REVERT(0, 0))

    def worker_frame(selector: int, **overrides: Any) -> FrameCase:
        return default_frame(
            target=worker,
            data=selector.to_bytes(32, "big"),
            pin_gas=False,
            **overrides,
        )

    if reversion == "reverted_call":
        reverting_frames = [
            worker_frame(4, state_gas_limit=0, state_gas_used=0)
        ]
    elif reversion == "reverted_frame":
        reverting_frames = [
            worker_frame(2, state_gas_limit=0, outcome=Outcome.REVERT)
        ]
    else:
        reverting_frames = [
            worker_frame(
                3,
                flags=Spec.ATOMIC_BATCH_FLAG,
                state_gas_limit=0,
                outcome=Outcome.UNROLLED,
            ),
            # Terminate the batch with a revert, unrolling it.
            default_frame(
                target=reverter,
                outcome=Outcome.REVERT,
                pin_gas=False,
            ),
        ]

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            # Frame 0: approve execution and payment.
            verify_frame(),
            # Frame 1: create the slot (0 -> 1). The final clear
            # refilled this receipt.
            worker_frame(0, state_gas_used=0),
            # The reverted clearing write.
            *reverting_frames,
            # Clear the slot for good, refilling frame 1, and create a
            # second slot from exactly one slot creation of budget.
            worker_frame(
                1,
                state_gas_limit=fresh_write_state_cost,
                state_gas_used=fresh_write_state_cost,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            worker: Account(storage={SLOT_CREATED: 0, SLOT_SECOND: 1}),
        },
    )
