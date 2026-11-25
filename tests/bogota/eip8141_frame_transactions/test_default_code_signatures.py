"""
Default code signature tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

An account with neither code nor an EIP-7702 delegation runs the
protocol's default code. In a `VERIFY` frame the default code approves
only on the strength of one specific signature entry (§Default code):

- "Let `sig_index = 0` if `allowed_scope & APPROVE_EXECUTION != 0`,
  else `sig_index = 1`."
- "If there is not a `SECP256K1` signature `sig` at index `sig_index`
  such that `resolved_signer == resolved_target` and
  `sig.msg == Bytes()`, revert."
- "Call `APPROVE(allowed_scope)`."

A reverting `VERIFY` frame makes the whole transaction invalid
(§Behavior: "If the frame fails by reverting or halting exceptionally,
the transaction is invalid."). Every signature entry in these cases is
itself valid, so only the default code's choice of entry decides the
verdict.
"""

from typing import Callable, Dict, List, Optional, Tuple

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytecode,
    Bytes,
    Fork,
    Frame,
    FrameSignature,
    GasFee,
    P256Signer,
    StateTestFiller,
    Transaction,
    TransactionException,
)

from .helpers import APPROVE_ALL
from .signature_helpers import canonical_entry
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")


ENTRY_SELECTION_CASES = [
    pytest.param(
        lambda a: (
            [
                Frame.verify(flags=Spec.APPROVE_EXECUTION),
                Frame.verify(flags=Spec.APPROVE_PAYMENT, target=a["payer"]),
            ],
            [canonical_entry(a["sender"]), canonical_entry(a["payer"])],
        ),
        "payer",
        id="payer_entry_at_index_1",
    ),
    pytest.param(
        # §Default code: "If there is not a `SECP256K1` signature `sig`
        # at index `sig_index` [...] revert." A payment-only frame reads
        # index 1 even when its target is the sender, whose entry sits
        # at index 0.
        lambda a: (
            [
                Frame.verify(flags=Spec.APPROVE_EXECUTION),
                Frame.verify(flags=Spec.APPROVE_PAYMENT),
            ],
            [canonical_entry(a["sender"])],
        ),
        None,
        id="sender_pays_separately_without_index_1",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The same entry twice gives the payment frame its index 1.
        lambda a: (
            [
                Frame.verify(flags=Spec.APPROVE_EXECUTION),
                Frame.verify(flags=Spec.APPROVE_PAYMENT),
            ],
            [canonical_entry(a["sender"]), canonical_entry(a["sender"])],
        ),
        "sender",
        id="sender_pays_separately_duplicate_entry",
    ),
    pytest.param(
        # A missing entry at index 0, read by a frame that may approve
        # execution: no entry at all.
        lambda _: ([Frame.verify()], []),
        None,
        id="no_entry_at_index_0",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # §Default code: "a `SECP256K1` signature". An `ARBITRARY` entry
        # has an empty signer, which a client skipping the scheme check
        # could resolve to the sender, the frame's resolved target.
        lambda a: (
            [
                Frame.verify(flags=Spec.APPROVE_EXECUTION),
                Frame.verify(flags=Spec.APPROVE_PAYMENT),
            ],
            [
                canonical_entry(a["sender"]),
                FrameSignature(
                    scheme=Spec.SCHEME_ARBITRARY, signature=Bytes(b"\x01")
                ),
            ],
        ),
        None,
        id="arbitrary_entry_at_index_1",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The same at index 0, read by a frame that may approve execution.
        lambda _: (
            [Frame.verify()],
            [
                FrameSignature(
                    scheme=Spec.SCHEME_ARBITRARY, signature=Bytes(b"\x01")
                )
            ],
        ),
        None,
        id="arbitrary_entry_at_index_0",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # §Default code: "`resolved_signer == resolved_target`". A valid
        # entry from an account other than the payer.
        lambda a: (
            [
                Frame.verify(flags=Spec.APPROVE_EXECUTION),
                Frame.verify(flags=Spec.APPROVE_PAYMENT, target=a["payer"]),
            ],
            [canonical_entry(a["sender"]), canonical_entry(a["third"])],
        ),
        None,
        id="index_1_signed_by_third_account",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The same at index 0: a valid entry from an account other than
        # the sender.
        lambda a: ([Frame.verify()], [canonical_entry(a["third"])]),
        None,
        id="index_0_signed_by_third_account",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # §Transaction Signatures: "If absent, `tx.sender` is used". The
        # entry's empty signer resolves to the sender.
        lambda a: (
            [Frame.verify()],
            [
                FrameSignature(
                    scheme=Spec.SCHEME_SECP256K1,
                    signed_by=a["sender"],
                    signer=Bytes(),
                )
            ],
        ),
        "sender",
        id="sender_entry_with_empty_signer",
    ),
    pytest.param(
        # The payment frame names the sender explicitly, and its entry
        # at index 1 leaves the signer empty: both resolve to the sender.
        lambda a: (
            [
                Frame.verify(flags=Spec.APPROVE_EXECUTION),
                Frame.verify(flags=Spec.APPROVE_PAYMENT, target=a["sender"]),
            ],
            [
                canonical_entry(a["sender"]),
                FrameSignature(
                    scheme=Spec.SCHEME_SECP256K1,
                    signed_by=a["sender"],
                    signer=Bytes(),
                ),
            ],
        ),
        "sender",
        id="explicit_sender_target_empty_signer_entry",
    ),
]
"""
Frames and signature entries of a transaction whose approvals all go
through the default code, built from the funded `sender`, `payer` and
`third` accounts, each with the account expected to pay, or `None`
where the default code must revert.
"""


@pytest.mark.parametrize("case,expected_payer", ENTRY_SELECTION_CASES)
def test_default_code_entry_selection(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    case: Callable[[Dict[str, EOA]], Tuple[List[Frame], List[FrameSignature]]],
    expected_payer: Optional[str],
) -> None:
    """
    Approve through the default code with the authorizing entry missing,
    of the wrong scheme or signed by the wrong account, and check the
    transaction is invalid, while the nearest-valid entry layouts
    approve.

    EIP-8141 §Default code: "Let `sig_index = 0` if `allowed_scope &
    APPROVE_EXECUTION != 0`, else `sig_index = 1`." and "If there is not
    a `SECP256K1` signature `sig` at index `sig_index` such that
    `resolved_signer == resolved_target` and `sig.msg == Bytes()`,
    revert."
    """
    accounts = {
        "sender": pre.fund_eoa(),
        "payer": pre.fund_eoa(),
        "third": pre.fund_eoa(),
    }
    frames, signatures = case(accounts)
    sender = accounts["sender"]
    payer = accounts[expected_payer] if expected_payer else None
    tx = Transaction(
        sender=sender,
        frames=frames,
        signatures=signatures,
        error=(
            None
            if payer
            else TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
        ),
    ).resolve_frames(fork, payer=payer)

    # Nothing is charged to an account that does not pay, and only the
    # sender's nonce is incremented.
    post: Dict[Address, Account] = {
        account: Account(nonce_change=0, balance_change=0)
        for account in accounts.values()
    }
    if payer is not None:
        post[sender] = Account(nonce_change=1, balance_change=0)
        post[payer] = Account(
            nonce_change=1 if payer == sender else 0,
            balance_change=-GasFee(
                tx, gas=tx.frame_settlement(fork).payer_gas_used()
            ),
        )
    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "sender_code",
    [
        pytest.param(
            None, id="default_code", marks=pytest.mark.exception_test
        ),
        pytest.param(
            APPROVE_ALL,
            id="approving_code",
            # Placing code at a fixed address mutates the shared
            # pre-alloc.
            marks=pytest.mark.pre_alloc_mutable,
        ),
    ],
)
def test_default_code_rejects_p256_entry(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    sender_code: Optional[Bytecode],
) -> None:
    """
    Send from a P-256 key's address with a valid P256 entry over the
    signature hash, whose empty signer resolves to the sender, as the
    only entry.

    Without code, the default code refuses the entry for its scheme, so
    the transaction is invalid. With code that approves, the same entry
    is accepted, so signature validation passes it.

    EIP-8141 §Default code: "If there is not a `SECP256K1` signature
    `sig` at index `sig_index` such that `resolved_signer ==
    resolved_target` and `sig.msg == Bytes()`, revert."
    """
    sender = P256Signer(0x8141)
    if sender_code is None:
        pre.fund_address(sender, 10**18)
    else:
        pre[sender] = Account(code=sender_code, balance=10**18)

    tx = Transaction(
        sender=sender,
        frames=[Frame.verify(code=sender_code)],
        signatures=[
            FrameSignature(
                scheme=Spec.SCHEME_P256, signed_by=sender, signer=Bytes()
            )
        ],
        error=(
            TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
            if sender_code is None
            else None
        ),
    ).resolve_frames(fork)

    if sender_code is None:
        sender_post = Account(nonce_change=0, balance_change=0)
    else:
        sender_post = Account(
            nonce_change=1,
            balance_change=-GasFee(
                tx, gas=tx.frame_settlement(fork).payer_gas_used()
            ),
        )
    state_test(pre=pre, tx=tx, post={sender: sender_post})
