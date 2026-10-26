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
itself valid, so the transaction passes signature validation and only
the default code's choice of entry, or the `APPROVE` it calls, decides
the verdict.
"""

from functools import cached_property
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
    FrameSignature,
    GasFee,
    StateTestFiller,
    Transaction,
    TransactionException,
    keccak256,
)

from .helpers import (
    APPROVE_ALL,
    FrameCase,
    FrameTransaction,
    expiry_frame,
    verify_frame,
)
from .signature_helpers import (
    DIGEST,
    P256_SIGNATURE,
    canonical_entry,
    p256_public_key,
    p256_sign,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

EXEC_ERROR = TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
"""A `VERIFY` frame failed, which invalidates the transaction."""

PAYER_FUNDS = 10**18
"""Balance of the payer EOA, far above any transaction's `max_cost`."""


class Accounts:
    """The accounts a default code case refers to."""

    def __init__(self, pre: Alloc) -> None:
        """Fund the sender and a payer."""
        self.pre = pre
        self.sender = pre.fund_eoa()
        self.payer = pre.fund_eoa(amount=PAYER_FUNDS)
        self.funded: List[EOA] = [self.sender, self.payer]

    @cached_property
    def third(self) -> EOA:
        """Fund an unrelated third account on first use."""
        account = self.pre.fund_eoa()
        self.funded.append(account)
        return account


Case = Callable[[Accounts], Tuple[List[FrameCase], List[FrameSignature]]]
"""Build a case's frames and signature entries from its accounts."""


def approve_execution() -> FrameCase:
    """Return a `VERIFY` frame on the sender approving execution only."""
    return verify_frame(flags=Spec.APPROVE_EXECUTION)


def approve_payment(target: Optional[Address] = None) -> FrameCase:
    """Return a `VERIFY` frame approving payment only."""
    return verify_frame(flags=Spec.APPROVE_PAYMENT, target=target)


ENTRY_SELECTION_CASES = [
    pytest.param(
        lambda a: (
            [approve_execution(), approve_payment(a.payer)],
            [canonical_entry(a.sender), canonical_entry(a.payer)],
        ),
        "payer",
        id="payer_entry_at_index_1",
    ),
    pytest.param(
        # §Default code: "If there is not a `SECP256K1` signature `sig`
        # at index `sig_index` [...] revert."
        lambda a: (
            [approve_execution(), approve_payment(a.payer)],
            [canonical_entry(a.sender)],
        ),
        None,
        id="payer_entry_missing",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # A payment-only frame reads index 1 even when its target is the
        # sender, whose entry sits at index 0.
        lambda a: (
            [approve_execution(), approve_payment()],
            [canonical_entry(a.sender)],
        ),
        None,
        id="sender_pays_separately_without_index_1",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The same entry twice gives the payment frame its index 1.
        lambda a: (
            [approve_execution(), approve_payment()],
            [canonical_entry(a.sender), canonical_entry(a.sender)],
        ),
        "sender",
        id="sender_pays_separately_duplicate_entry",
    ),
    pytest.param(
        # §Default code: "a `SECP256K1` signature". An `ARBITRARY` entry
        # has an empty signer, which a client skipping the scheme check
        # could resolve to the sender, the frame's resolved target.
        lambda a: (
            [approve_execution(), approve_payment()],
            [
                canonical_entry(a.sender),
                FrameSignature(
                    scheme=Spec.SCHEME_ARBITRARY,
                    signature=Bytes(b"\x01" * 65),
                ),
            ],
        ),
        None,
        id="arbitrary_entry_at_index_1",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # §Default code: "`resolved_signer == resolved_target`". A valid
        # entry from an account other than the payer.
        lambda a: (
            [approve_execution(), approve_payment(a.payer)],
            [canonical_entry(a.sender), canonical_entry(a.third)],
        ),
        None,
        id="index_1_signed_by_third_account",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # §Default code: "`sig.msg == Bytes()`". The sender's valid entry
        # signs an explicit digest instead of the signature hash.
        lambda a: (
            [verify_frame()],
            [canonical_entry(a.sender, msg=Bytes(DIGEST))],
        ),
        None,
        id="sender_entry_with_explicit_msg",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda a: (
            [approve_execution(), approve_payment(a.payer)],
            [
                canonical_entry(a.sender),
                canonical_entry(a.payer, msg=Bytes(DIGEST)),
            ],
        ),
        None,
        id="payer_entry_with_explicit_msg",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # §Transaction Signatures: "If absent, `tx.sender` is used". The
        # entry's empty signer resolves to the sender.
        lambda a: (
            [verify_frame()],
            [canonical_entry(a.sender, signer=Bytes())],
        ),
        "sender",
        id="sender_entry_with_empty_signer",
    ),
    pytest.param(
        # The payment frame names the sender explicitly, and its entry
        # at index 1 leaves the signer empty: both resolve to the sender,
        # which is warm from the start of the transaction.
        lambda a: (
            [
                approve_execution(),
                verify_frame(
                    flags=Spec.APPROVE_PAYMENT, target=a.sender, warm=True
                ),
            ],
            [
                canonical_entry(a.sender),
                canonical_entry(a.sender, signer=Bytes()),
            ],
        ),
        "sender",
        id="explicit_sender_target_empty_signer_entry",
    ),
]
"""
Frames and signature entries of a transaction whose approvals all go
through the default code, each with the account expected to pay, or
`None` where the default code must revert.
"""


@pytest.mark.parametrize("case,expected_payer", ENTRY_SELECTION_CASES)
def test_default_code_entry_selection(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    case: Case,
    expected_payer: Optional[str],
) -> None:
    """
    Approve through the default code with the authorizing entry missing,
    of the wrong scheme, signed by the wrong account or over an explicit
    digest, and check the transaction is invalid, while the
    nearest-valid entry layouts approve.

    EIP-8141 §Default code: "Let `sig_index = 0` if `allowed_scope &
    APPROVE_EXECUTION != 0`, else `sig_index = 1`." and "If there is not
    a `SECP256K1` signature `sig` at index `sig_index` such that
    `resolved_signer == resolved_target` and `sig.msg == Bytes()`,
    revert."
    """
    accounts = Accounts(pre)
    frames, signatures = case(accounts)
    payer = getattr(accounts, expected_payer) if expected_payer else None
    tx = FrameTransaction.build(
        fork=fork,
        sender=accounts.sender,
        payer=payer,
        frames=frames,
        signatures=signatures,
        error=None if payer else EXEC_ERROR,
    )

    # Nothing is charged to an account that does not pay, and only the
    # sender's nonce is incremented.
    post: Dict[Address, Account] = {
        account: Account(nonce=0, balance_change=0)
        for account in accounts.funded
    }
    if payer is not None:
        post[accounts.sender] = Account(nonce=1, balance_change=0)
        post[payer] = Account(
            nonce=1 if payer == accounts.sender else 0,
            balance_change=-GasFee(tx, gas=tx.payer_gas_used()),
        )
    state_test(pre=pre, tx=tx, post=post)


APPROVAL_REFUSAL_CASES = [
    pytest.param(
        lambda a: (
            [approve_execution(), approve_payment(a.payer)],
            [canonical_entry(a.sender), canonical_entry(a.payer)],
        ),
        False,
        id="execution_then_payment",
    ),
    pytest.param(
        # §APPROVE Behavior, `APPROVE_PAYMENT`: "If `sender_approved ==
        # false`, revert the current call frame."
        lambda a: (
            [approve_payment(a.payer), approve_execution()],
            [canonical_entry(a.sender), canonical_entry(a.payer)],
        ),
        True,
        id="payment_before_execution",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # §APPROVE Behavior, `APPROVE_PAYMENT`: "If `payer` was already
        # set, revert the current call frame." The second payer can
        # afford `max_cost`, so only the first approval refuses it.
        lambda a: (
            [verify_frame(), approve_payment(a.payer)],
            [canonical_entry(a.sender), canonical_entry(a.payer)],
        ),
        True,
        id="second_payment_approval",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # §APPROVE Behavior, `APPROVE_EXECUTION`: "If `sender_approved ==
        # true`, revert the current call frame."
        lambda a: (
            [
                approve_execution(),
                approve_execution(),
                approve_payment(a.payer),
            ],
            [canonical_entry(a.sender), canonical_entry(a.payer)],
        ),
        True,
        id="second_execution_approval",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # §APPROVE Behavior, `APPROVE_EXECUTION_AND_PAYMENT`: "If
        # `sender_approved` or `payer` was already set, revert the
        # current call frame."
        lambda a: (
            [approve_execution(), verify_frame()],
            [canonical_entry(a.sender)],
        ),
        True,
        id="execution_and_payment_after_execution",
        marks=pytest.mark.exception_test,
    ),
]
"""
Sequences of default code approvals, each with whether one of them
must be refused, which reverts its `VERIFY` frame.
"""


@pytest.mark.parametrize("case,refused", APPROVAL_REFUSAL_CASES)
def test_default_code_approval_refusals(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    case: Case,
    refused: bool,
) -> None:
    """
    Order default code approvals so that the `APPROVE` one of them
    calls must be refused, and check the refusal reverts its `VERIFY`
    frame and invalidates the transaction.

    EIP-8141 §Default code: "Call `APPROVE(allowed_scope)`." The
    default code's `APPROVE` is subject to every check of §APPROVE
    Behavior, and a refusal reverts the frame.
    """
    accounts = Accounts(pre)
    frames, signatures = case(accounts)
    tx = FrameTransaction.build(
        fork=fork,
        sender=accounts.sender,
        payer=accounts.payer,
        frames=frames,
        signatures=signatures,
        error=EXEC_ERROR if refused else None,
    )

    post = {
        accounts.sender: Account(nonce=0 if refused else 1),
        accounts.payer: Account(
            nonce=0,
            balance_change=(
                0 if refused else -GasFee(tx, gas=tx.payer_gas_used())
            ),
        ),
    }
    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "gas_short",
    [
        pytest.param(0, id="entry_charge_covered"),
        pytest.param(1, id="one_below", marks=pytest.mark.exception_test),
    ],
)
def test_default_code_warm_sender_entry_charge(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_short: int,
) -> None:
    """
    Give a `VERIFY` frame on the warm sender exactly the warm access the
    frame is charged at entry, or one unit less.

    EIP-8141 §Default code: "The default code draws no execution gas of
    its own: the frame's only execution charge is the resolved target's
    access, taken at frame entry" and "A frame whose `limits.execution`
    cannot cover the entry access charge halts exceptionally before the
    default code is evaluated — which, for a `VERIFY` frame,
    invalidates the transaction."
    """
    sender = pre.fund_eoa()
    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[verify_frame(gas_limit_delta=-gas_short)],
        error=EXEC_ERROR if gas_short else None,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=0 if gas_short else 1)},
    )


P256_SENDER_KEY = 0x8141
"""P-256 private key whose public key words hash to `P256_SENDER`."""

P256_SENDER_QX, P256_SENDER_QY = p256_public_key(P256_SENDER_KEY)
"""The public key words `qx` and `qy` of `P256_SENDER_KEY`."""

P256_SENDER = Address(
    keccak256(
        P256_SENDER_QX.to_bytes(32, "big") + P256_SENDER_QY.to_bytes(32, "big")
    )[12:]
)
"""The address `keccak256(qx || qy)[12:]` of `P256_SENDER_KEY`."""


def p256_sender_entry(signature: bytes) -> FrameSignature:
    """
    Return a P256 entry with an empty signer, which resolves to the
    sender, and an empty `msg`, which signs the signature hash.
    """
    return FrameSignature(scheme=Spec.SCHEME_P256, signature=Bytes(signature))


def p256_sender_signature(digest: bytes) -> bytes:
    """
    Sign `digest` with `P256_SENDER_KEY` and return the entry's
    `r || s || qx || qy` bytes, with `s` normalized to the low half.

    The nonce is derived deterministically (RFC 6979), so the fixture
    does not change between fills.
    """
    r, s = p256_sign(digest, P256_SENDER_KEY)
    return b"".join(
        word.to_bytes(32, "big")
        for word in (r, s, P256_SENDER_QX, P256_SENDER_QY)
    )


# Placing an account at a fixed address mutates the shared pre-alloc.
@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "sender_code",
    [
        pytest.param(
            None, id="default_code", marks=pytest.mark.exception_test
        ),
        pytest.param(
            APPROVE_ALL,
            id="approving_code",
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
    Send from the P-256 key's address with a valid P256 entry over the
    signature hash, whose signer resolves to the sender, as the only
    entry.

    Without code, the default code refuses the entry for its scheme, so
    the transaction is invalid. With code that approves, the same entry
    is accepted, which shows signature validation passes it and only the
    default code's scheme check rejects it.

    EIP-8141 §Default code: "If there is not a `SECP256K1` signature
    `sig` at index `sig_index` such that `resolved_signer ==
    resolved_target` and `sig.msg == Bytes()`, revert."
    """
    if sender_code is None:
        pre.fund_address(P256_SENDER, PAYER_FUNDS)
        nonce = 0
    else:
        pre.deploy_contract(
            sender_code, balance=PAYER_FUNDS, address=P256_SENDER
        )
        nonce = 1

    def with_signature(signature: bytes) -> FrameTransaction:
        return FrameTransaction.build(
            fork=fork,
            sender=P256_SENDER,
            nonce=nonce,
            frames=[verify_frame(code=sender_code)],
            signatures=[p256_sender_entry(signature)],
            error=EXEC_ERROR if sender_code is None else None,
        )

    sig_hash = (
        with_signature(bytes(len(P256_SIGNATURE)))
        .rlp_signing_bytes()
        .keccak256()
    )
    tx = with_signature(p256_sender_signature(bytes(sig_hash)))
    assert tx.rlp_signing_bytes().keccak256() == sig_hash

    state_test(
        pre=pre,
        tx=tx,
        post={
            P256_SENDER: Account(
                nonce=nonce if sender_code is None else nonce + 1
            )
        },
    )


# Replacing the expiry verifier's pre-state mutates the shared pre-alloc.
@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "verifier_deployed",
    [
        pytest.param(True, id="verifier_deployed"),
        pytest.param(
            False, id="verifier_absent", marks=pytest.mark.exception_test
        ),
    ],
)
def test_expiry_frame_without_verifier_code(
    state_test: StateTestFiller,
    pre: Alloc,
    verifier_deployed: bool,
) -> None:
    """
    Run an expiry verifier frame while the expiry verifier address holds
    no code, so the frame runs the default code with an approval scope
    of zero and reverts.

    EIP-8141 §Expiry Verifier Frame: "it is not installed by the
    protocol at activation", and §Default code: "If `allowed_scope ==
    APPROVE_SCOPE_NONE`, revert." An expiry verifier frame must carry
    `frame.flags == 0`. The address holds a balance only because the
    pre-state cannot hold an empty account.
    """
    if not verifier_deployed:
        pre[Spec.EXPIRY_VERIFIER] = Account(balance=1)
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=[verify_frame(), expiry_frame()],
        error=None if verifier_deployed else EXEC_ERROR,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=1 if verifier_deployed else 0)},
    )
