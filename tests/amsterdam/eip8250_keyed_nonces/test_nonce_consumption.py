"""
Nonce consumption tests for
[EIP-8250: Keyed Nonces for Frame Transactions](https://eips.ethereum.org/EIPS/eip-8250).

Payment approval consumes the transaction's nonce set once. The legacy
key set increments the sender's account nonce; any other key set writes
`nonce_seq + 1` to each selected slot of the nonce manager, charging
state gas for every slot used for the first time. The consumption is
part of the approval: it rolls back with the approving frame and
survives every later frame.
"""

from typing import List

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Conditional,
    Fork,
    Frame,
    FrameReceipt,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
)

from ..eip8141_frame_transactions.helpers import (
    default_code_frame_gas,
    default_frame,
    sender_frame,
    verify_frame,
)
from ..eip8141_frame_transactions.spec import Spec as Spec8141
from .helpers import (
    FULL_WIDTH_KEY,
    KEY_A,
    KEY_B,
    NULLIFIER_KEY,
    keyed_storage,
    nonce_manager,
    set_keyed_nonces,
)
from .spec import Spec, ref_spec_8250

REFERENCE_SPEC_GIT_PATH = ref_spec_8250.git_path
REFERENCE_SPEC_VERSION = ref_spec_8250.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT_EXECUTED = 0x01
"""Storage slot a worker contract writes to record that it ran."""

WORKER_FRAME_GAS = 100_000
"""Execution gas budget of the frames running worker contracts."""

MAX_KEY_SET = list(range(1, Spec.MAX_NONCE_KEYS + 1))
"""The largest nonce key set a transaction may select."""


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "nonce_keys",
    [
        pytest.param([KEY_A], id="one_key"),
        pytest.param([KEY_A, KEY_B], id="two_keys"),
        pytest.param([NULLIFIER_KEY], id="hash_derived_key"),
        pytest.param([FULL_WIDTH_KEY], id="full_width_key"),
        pytest.param(MAX_KEY_SET, id="max_keys"),
    ],
)
@pytest.mark.parametrize(
    "nonce_seq",
    [
        pytest.param(0, id="first_use"),
        pytest.param(5, id="reuse"),
    ],
)
def test_keyed_nonce_consumed(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    nonce_keys: List[int],
    nonce_seq: int,
) -> None:
    """
    Consume a keyed nonce set on payment approval.

    Every selected slot ends at `nonce_seq + 1` and the sender's account
    nonce stays unchanged. Each slot used for the first time charges one
    storage slot creation to the approving frame's state gas; a reused
    slot charges nothing. The bookkeeping draws no execution gas, so the
    frame reports only its target's access at entry.
    """
    sender = pre.fund_eoa()
    if nonce_seq:
        set_keyed_nonces(pre, [(sender, dict.fromkeys(nonce_keys, nonce_seq))])
    first_uses = 0 if nonce_seq else len(nonce_keys)
    nonce_state_gas = first_uses * Spec.KEYED_NONCE_FIRST_USE_STATE_GAS

    tx = Transaction(
        sender=sender,
        nonce=nonce_seq,
        nonce_keys=nonce_keys,
        frames=[verify_frame(state_gas_limit=nonce_state_gas)],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(
                    status=Spec8141.STATUS_SUCCESS,
                    gas_used=default_code_frame_gas(fork, target_warm=True),
                    state_gas_used=nonce_state_gas,
                ),
            ],
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=0),
            Spec.NONCE_MANAGER: nonce_manager(
                keyed_storage(sender, dict.fromkeys(nonce_keys, nonce_seq + 1))
            ),
        },
    )


@pytest.mark.pre_alloc_mutable
def test_keyed_nonce_independent_of_account_nonce(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Accept a keyed transaction whose sequence differs from the sender's
    account nonce, and leave the account nonce as it was.
    """
    sender = pre.fund_eoa(nonce=7)

    tx = Transaction(
        sender=sender,
        nonce=0,
        nonce_keys=[KEY_A],
        frames=[verify_frame()],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=7),
            Spec.NONCE_MANAGER: nonce_manager(
                keyed_storage(sender, {KEY_A: 1})
            ),
        },
    )


@pytest.mark.pre_alloc_mutable
def test_legacy_nonce_keys(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Consume the legacy key set: the sender's account nonce increments,
    the nonce manager is not written, and an existing sender pays no
    state gas.
    """
    sender = pre.fund_eoa(nonce=1)

    tx = Transaction(
        sender=sender,
        nonce=1,
        nonce_keys=list(Spec.LEGACY_NONCE_KEYS),
        frames=[verify_frame()],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(
                    status=Spec8141.STATUS_SUCCESS,
                    gas_used=default_code_frame_gas(fork, target_warm=True),
                    state_gas_used=0,
                ),
            ],
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=2),
            Spec.NONCE_MANAGER: nonce_manager(),
        },
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "state_gas_shortfall",
    [
        pytest.param(0, id="exact"),
        pytest.param(1, id="one_short", marks=pytest.mark.exception_test),
    ],
)
def test_first_use_state_gas_budget(
    state_test: StateTestFiller,
    pre: Alloc,
    state_gas_shortfall: int,
) -> None:
    """
    Halt payment approval when the approving frame's state gas cannot
    cover every first-use slot.

    Two fresh keys cost two slot creations. A budget of exactly that is
    accepted; one unit less halts the `APPROVE` with no approval effects,
    and a failing `VERIFY` frame invalidates the transaction.
    """
    sender = pre.fund_eoa()
    budget = 2 * Spec.KEYED_NONCE_FIRST_USE_STATE_GAS - state_gas_shortfall

    tx = Transaction(
        sender=sender,
        nonce_keys=[KEY_A, KEY_B],
        frames=[verify_frame(state_gas_limit=budget)],
        error=(
            TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
            if state_gas_shortfall
            else None
        ),
    )

    consumed = {} if state_gas_shortfall else {KEY_A: 1, KEY_B: 1}
    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=0),
            Spec.NONCE_MANAGER: nonce_manager(keyed_storage(sender, consumed)),
        },
    )


@pytest.mark.pre_alloc_mutable
def test_reused_keys_need_no_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Approve payment for a keyed set of used slots from a frame that
    declares no state gas: advancing an existing slot creates nothing.
    """
    sender = pre.fund_eoa()
    set_keyed_nonces(pre, [(sender, {KEY_A: 3, KEY_B: 3})])

    tx = Transaction(
        sender=sender,
        nonce=3,
        nonce_keys=[KEY_A, KEY_B],
        frames=[verify_frame(state_gas_limit=0)],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            Spec.NONCE_MANAGER: nonce_manager(
                keyed_storage(sender, {KEY_A: 4, KEY_B: 4})
            ),
        },
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "atomic_batch",
    [
        pytest.param(False, id="frame_reverts"),
        pytest.param(True, id="atomic_batch_rolls_back"),
    ],
)
def test_consumption_survives_later_failure(
    state_test: StateTestFiller,
    pre: Alloc,
    atomic_batch: bool,
) -> None:
    """
    Keep the nonce consumption when a frame after the approval fails.

    The keyed slot is written by the approving `VERIFY` frame. A later
    reverting frame, or an atomic batch that rolls back, discards its own
    effects but not the approval's.
    """
    sender = pre.fund_eoa()
    worker = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)
    reverter = pre.deploy_contract(code=Op.REVERT(0, 0))

    frames: List[Frame] = [verify_frame()]
    receipts = [FrameReceipt(status=Spec8141.STATUS_SUCCESS)]
    if atomic_batch:
        frames.append(
            sender_frame(
                target=worker,
                gas_limit=WORKER_FRAME_GAS,
                flags=Spec8141.ATOMIC_BATCH_FLAG,
            )
        )
        receipts.append(FrameReceipt(status=Spec8141.STATUS_SUCCESS))
    frames.append(sender_frame(target=reverter, gas_limit=WORKER_FRAME_GAS))
    receipts.append(FrameReceipt(status=Spec8141.STATUS_FAILURE))

    tx = Transaction(
        sender=sender,
        nonce_keys=[KEY_A],
        frames=frames,
        expected_receipt=TransactionReceipt(
            payer=sender, frame_receipts=receipts
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            worker: Account(storage={SLOT_EXECUTED: 0}),
            Spec.NONCE_MANAGER: nonce_manager(
                keyed_storage(sender, {KEY_A: 1})
            ),
        },
    )


@pytest.mark.pre_alloc_mutable
def test_reverted_approval_discards_consumption(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Roll the nonce consumption back with the frame that approved it.

    The first frame approves from a nested call into the sender and then
    reverts, discarding the approval with the keyed slot write and its
    state gas. The second frame approves again: it still sees the key
    unused, so it pays the first-use charge and writes the slot itself.
    """
    outer = Op.CALL(gas=Op.GAS, address=Op.ADDRESS) + Op.REVERT(0, 0)
    sender_code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=outer,
        if_false=Op.APPROVE(0, 0, Spec8141.APPROVE_EXECUTION_AND_PAYMENT),
    )
    sender = pre.deploy_contract(code=sender_code, balance=10**18)

    tx = Transaction(
        sender=sender,
        nonce=0,
        nonce_keys=[KEY_A],
        frames=[
            default_frame(
                flags=Spec8141.APPROVE_EXECUTION_AND_PAYMENT,
                target=sender,
                gas_limit=400_000,
                data=Bytes(b"\x01"),
            ),
            verify_frame(target=sender),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec8141.STATUS_FAILURE, state_gas_used=0),
                FrameReceipt(
                    status=Spec8141.STATUS_SUCCESS,
                    state_gas_used=Spec.KEYED_NONCE_FIRST_USE_STATE_GAS,
                ),
            ],
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            Spec.NONCE_MANAGER: nonce_manager(
                keyed_storage(sender, {KEY_A: 1})
            ),
        },
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "approve_scope",
    [
        pytest.param(Spec8141.APPROVE_PAYMENT, id="payment"),
        pytest.param(
            Spec8141.APPROVE_EXECUTION_AND_PAYMENT, id="execution_and_payment"
        ),
    ],
)
def test_payment_scopes_consume(
    state_test: StateTestFiller,
    pre: Alloc,
    approve_scope: int,
) -> None:
    """
    Consume the nonce set on either payment-scoped `APPROVE`, and not
    on an execution-only one.

    The sender contract approves execution alone in the first frame and
    then the scope under test in the second. When the second scope also
    carries execution, the first frame approves nothing.
    """
    first_scope = (
        Spec8141.APPROVE_EXECUTION
        if approve_scope == Spec8141.APPROVE_PAYMENT
        else Spec8141.APPROVE_NONE
    )
    sender_code = Conditional(
        condition=Op.EQ(Op.TXPARAM(Spec8141.TXPARAM_FRAME_INDEX), 0),
        if_true=Op.APPROVE(0, 0, first_scope) if first_scope else Op.STOP,
        if_false=Op.APPROVE(0, 0, approve_scope),
    )
    sender = pre.deploy_contract(code=sender_code, balance=10**18)

    tx = Transaction(
        sender=sender,
        nonce=0,
        nonce_keys=[KEY_A],
        frames=[
            verify_frame(target=sender, flags=first_scope),
            verify_frame(target=sender, flags=approve_scope),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec8141.STATUS_SUCCESS, state_gas_used=0),
                FrameReceipt(
                    status=Spec8141.STATUS_SUCCESS,
                    state_gas_used=Spec.KEYED_NONCE_FIRST_USE_STATE_GAS,
                ),
            ],
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            Spec.NONCE_MANAGER: nonce_manager(
                keyed_storage(sender, {KEY_A: 1})
            ),
        },
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "start_nonce",
    [
        pytest.param(5, id="increments_current_nonce"),
        pytest.param(2**64 - 3, id="reaches_max_nonce"),
        pytest.param(
            2**64 - 2,
            id="overflows_max_nonce",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_legacy_increment_after_sender_create(
    state_test: StateTestFiller,
    pre: Alloc,
    start_nonce: int,
) -> None:
    """
    Increment the sender's current account nonce on legacy payment
    approval, after a `SENDER` frame already moved it with `CREATE`.

    The sender approves execution, then its `SENDER` frame runs `CREATE`
    and raises the account nonce by one, then it approves payment. The
    approval increments the nonce it finds rather than writing
    `nonce_seq + 1`, so the account ends two above `nonce_seq`. When the
    `CREATE` already left the nonce at `2**64 - 1`, the increment would
    pass `MAX_NONCE_SEQ`: the `APPROVE` halts, the `VERIFY` frame fails
    and the transaction is invalid.
    """
    sender_code = Conditional(
        condition=Op.EQ(Op.TXPARAM(Spec8141.TXPARAM_FRAME_INDEX), 1),
        if_true=Op.POP(Op.CREATE(0, 0, 0)) + Op.STOP,
        if_false=Conditional(
            condition=Op.TXPARAM(Spec8141.TXPARAM_FRAME_INDEX),
            if_true=Op.APPROVE(0, 0, Spec8141.APPROVE_PAYMENT),
            if_false=Op.APPROVE(0, 0, Spec8141.APPROVE_EXECUTION),
        ),
    )
    sender = pre.deploy_contract(
        code=sender_code, balance=10**18, nonce=start_nonce
    )
    overflows = start_nonce + 2 > Spec.MAX_NONCE_SEQ

    tx = Transaction(
        sender=sender,
        nonce=start_nonce,
        frames=[
            verify_frame(target=sender, flags=Spec8141.APPROVE_EXECUTION),
            sender_frame(target=sender, gas_limit=WORKER_FRAME_GAS),
            verify_frame(target=sender, flags=Spec8141.APPROVE_PAYMENT),
        ],
        error=(
            TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
            if overflows
            else None
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(
                nonce=start_nonce if overflows else start_nonce + 2
            ),
        },
    )
