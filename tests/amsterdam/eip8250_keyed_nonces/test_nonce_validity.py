"""
Nonce validity tests for
[EIP-8250: Keyed Nonces for Frame Transactions](https://eips.ethereum.org/EIPS/eip-8250).

A frame transaction selects between one and `MAX_NONCE_KEYS` nonce keys
in strictly increasing order, the zero key only alone, and a
`nonce_seq` below `MAX_NONCE_SEQ`. Before any frame executes, every
selected key must hold `nonce_seq`: the zero key in the sender's account
nonce, any other key in the nonce manager, where an absent slot holds
zero.
"""

from typing import Dict, List

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
    TransactionException,
)

from ..eip8141_frame_transactions.helpers import verify_frame
from .helpers import (
    KEY_A,
    KEY_B,
    keyed_storage,
    nonce_manager,
    set_keyed_nonces,
)
from .spec import Spec, ref_spec_8250

REFERENCE_SPEC_GIT_PATH = ref_spec_8250.git_path
REFERENCE_SPEC_VERSION = ref_spec_8250.version

pytestmark = pytest.mark.valid_from("Bogota")


@pytest.mark.exception_test
@pytest.mark.parametrize(
    "nonce_keys",
    [
        pytest.param([], id="no_keys"),
        pytest.param(
            list(range(1, Spec.MAX_NONCE_KEYS + 2)), id="too_many_keys"
        ),
        pytest.param([KEY_B, KEY_A], id="decreasing"),
        pytest.param([KEY_A, KEY_A], id="duplicate"),
        pytest.param([0, KEY_A], id="zero_key_with_other_key"),
        pytest.param([0, 0], id="zero_key_twice"),
    ],
)
def test_invalid_nonce_key_set(
    state_test: StateTestFiller,
    pre: Alloc,
    nonce_keys: List[int],
) -> None:
    """
    Reject a frame transaction whose nonce key set is malformed.
    """
    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        nonce_keys=nonce_keys,
        frames=[verify_frame()],
        error=TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=0),
            Spec.NONCE_MANAGER: nonce_manager(),
        },
    )


@pytest.mark.exception_test
@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "stored,nonce_keys,nonce_seq,error",
    [
        pytest.param(
            {KEY_A: 3},
            [KEY_A],
            2,
            TransactionException.NONCE_MISMATCH_TOO_LOW,
            id="seq_too_low",
        ),
        pytest.param(
            {KEY_A: 3},
            [KEY_A],
            4,
            TransactionException.NONCE_MISMATCH_TOO_HIGH,
            id="seq_too_high",
        ),
        pytest.param(
            {},
            [KEY_A],
            1,
            TransactionException.NONCE_MISMATCH_TOO_HIGH,
            id="unused_key_reads_zero",
        ),
        pytest.param(
            {KEY_A: 3, KEY_B: 4},
            [KEY_A, KEY_B],
            3,
            TransactionException.NONCE_MISMATCH_TOO_LOW,
            id="one_key_ahead",
        ),
        pytest.param(
            {KEY_A: 3},
            [KEY_A, KEY_B],
            3,
            TransactionException.NONCE_MISMATCH_TOO_HIGH,
            id="one_key_unused",
        ),
    ],
)
def test_nonce_seq_mismatch(
    state_test: StateTestFiller,
    pre: Alloc,
    stored: Dict[int, int],
    nonce_keys: List[int],
    nonce_seq: int,
    error: TransactionException,
) -> None:
    """
    Reject a keyed transaction unless every selected key holds its
    `nonce_seq`.

    `one_key_unused` selects a used key and an unused one: the unused key
    holds zero, below `nonce_seq`, so the set cannot match.
    """
    sender = pre.fund_eoa()
    if stored:
        set_keyed_nonces(pre, [(sender, stored)])

    tx = Transaction(
        sender=sender,
        nonce=nonce_seq,
        nonce_keys=nonce_keys,
        frames=[verify_frame()],
        error=error,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            Spec.NONCE_MANAGER: nonce_manager(keyed_storage(sender, stored)),
        },
    )


@pytest.mark.pre_alloc_mutable
def test_sequences_are_per_sender(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Read a key's sequence under the transaction's own sender: another
    sender's use of the same key does not advance it.
    """
    other = pre.fund_eoa()
    sender = pre.fund_eoa()
    set_keyed_nonces(pre, [(other, {KEY_A: 9})])

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
            Spec.NONCE_MANAGER: nonce_manager(
                keyed_storage(other, {KEY_A: 9})
                | keyed_storage(sender, {KEY_A: 1})
            ),
        },
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "nonce_seq",
    [
        pytest.param(Spec.MAX_NONCE_SEQ - 1, id="last_usable_seq"),
        pytest.param(
            Spec.MAX_NONCE_SEQ,
            id="exhausted_key",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_keyed_nonce_seq_bound(
    state_test: StateTestFiller,
    pre: Alloc,
    nonce_seq: int,
) -> None:
    """
    Accept a keyed sequence of `MAX_NONCE_SEQ - 1`, which exhausts the
    key, and reject `MAX_NONCE_SEQ` even when the key holds it.
    """
    sender = pre.fund_eoa()
    set_keyed_nonces(pre, [(sender, {KEY_A: nonce_seq})])
    exhausted = nonce_seq == Spec.MAX_NONCE_SEQ

    tx = Transaction(
        sender=sender,
        nonce=nonce_seq,
        nonce_keys=[KEY_A],
        frames=[verify_frame()],
        error=TransactionException.NONCE_IS_MAX if exhausted else None,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            Spec.NONCE_MANAGER: nonce_manager(
                keyed_storage(
                    sender,
                    {KEY_A: nonce_seq if exhausted else nonce_seq + 1},
                )
            ),
        },
    )
