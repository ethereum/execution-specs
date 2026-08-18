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

import pytest
from execution_testing import (
    DEFAULT_FRAME_STATE_GAS_LIMIT,
    Account,
    Alloc,
    Bytes,
    Conditional,
    Fork,
    FrameReceipt,
    FrameSignature,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
)

from .helpers import default_frame, verify_frame
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

WORKER_FRAME_GAS = 100_000
"""Execution gas budget of the frames running the worker contracts."""


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

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(target=worker, gas_limit=WORKER_FRAME_GAS),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(
                    status=Spec.STATUS_SUCCESS, gas_used=0, state_gas_used=0
                ),
                FrameReceipt(
                    status=Spec.STATUS_SUCCESS,
                    gas_used=fork.frame_entry_gas_calculator()()
                    + worker_code.execution_cost(fork),
                    state_gas_used=observe_pool.state_cost(fork),
                ),
            ],
        ),
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

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(target=worker, gas_limit=WORKER_FRAME_GAS),
            default_frame(
                target=worker,
                gas_limit=WORKER_FRAME_GAS,
                data=b"\x01",
            ),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(
                    status=Spec.STATUS_SUCCESS, gas_used=0, state_gas_used=0
                ),
                # The owner's attribution is gone: the refill returned
                # its charge at settlement.
                FrameReceipt(status=Spec.STATUS_SUCCESS, state_gas_used=0),
                # The refilling frame pays only for its three fresh
                # recording slots; the refill credits it nothing.
                FrameReceipt(
                    status=Spec.STATUS_SUCCESS,
                    state_gas_used=3 * fresh_write_state_cost,
                ),
            ],
        ),
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
    "shortfall",
    [
        pytest.param(0, id="exact_budget"),
        pytest.param(1, id="one_below"),
    ],
)
def test_state_gas_exhaustion(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    shortfall: int,
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
    write = Op.SSTORE(SLOT_CREATED, 1)
    worker_code = write + Op.STOP
    worker = pre.deploy_contract(code=worker_code)

    state_budget = write.state_cost(fork) - shortfall
    succeeds = shortfall == 0

    if succeeds:
        receipt = FrameReceipt(
            status=Spec.STATUS_SUCCESS,
            gas_used=fork.frame_entry_gas_calculator()()
            + worker_code.execution_cost(fork),
            state_gas_used=state_budget,
        )
    else:
        receipt = FrameReceipt(
            status=Spec.STATUS_FAILURE,
            gas_used=WORKER_FRAME_GAS,
            state_gas_used=0,
        )

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=worker,
                gas_limit=WORKER_FRAME_GAS,
                state_gas_limit=state_budget,
            ),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(
                    status=Spec.STATUS_SUCCESS, gas_used=0, state_gas_used=0
                ),
                receipt,
            ],
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            worker: Account(storage={SLOT_CREATED: 1 if succeeds else 0}),
        },
    )


def test_approve_creates_sender(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Approve payment for a sender whose account does not exist.

    Incrementing the nonce creates the sender account, and `APPROVE`
    charges the account creation to the approving frame's state gas
    pool — here inside the payer's protocol default code, which
    consumes no execution gas at all.
    """
    sender = pre.fund_eoa(amount=0)
    payer = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(flags=Spec.APPROVE_EXECUTION),
            verify_frame(flags=Spec.APPROVE_PAYMENT, target=payer),
        ],
        signatures=[
            FrameSignature(scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)),
            FrameSignature(
                scheme=Spec.SCHEME_SECP256K1,
                signer=Bytes(payer),
                secret_key=payer.key,
            ),
        ],
        expected_receipt=TransactionReceipt(
            payer=payer,
            frame_receipts=[
                FrameReceipt(
                    status=Spec.STATUS_SUCCESS, gas_used=0, state_gas_used=0
                ),
                FrameReceipt(
                    status=Spec.STATUS_SUCCESS,
                    gas_used=0,
                    state_gas_used=fork.gas_costs().NEW_ACCOUNT,
                ),
            ],
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=1)},
    )


@pytest.mark.exception_test
def test_approve_sender_creation_unaffordable(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a frame transaction whose payment approval cannot cover the
    sender's account creation.

    The approving `VERIFY` frame declares no state gas, so the
    `APPROVE` inside the payer's protocol default code halts the frame
    exceptionally, with no approval effects — and a failing `VERIFY`
    frame invalidates the transaction.
    """
    sender = pre.fund_eoa(amount=0)
    payer = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(flags=Spec.APPROVE_EXECUTION),
            verify_frame(
                flags=Spec.APPROVE_PAYMENT,
                target=payer,
                state_gas_limit=0,
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

    state_test(pre=pre, tx=tx, post={})
