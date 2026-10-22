"""
Tests for ecrecover inside the frames of an
[EIP-8141](https://eips.ethereum.org/EIPS/eip-8141) frame transaction under
[EIP-8151: Account Code Restricted ecRecover](https://eips.ethereum.org/EIPS/eip-8151).

The protocol validates a secp256k1 signature entry without looking at the
signer's code, while ecrecover in a frame withholds a signer whose code is
not a delegation designation. The sender starts the transaction warm, and a
signature entry leaves its signer cold.
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Alloc,
    Bytes,
    Conditional,
    Fork,
    FrameSignature,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
)

from ..eip8141_frame_transactions.helpers import default_frame, verify_frame
from ..eip8141_frame_transactions.spec import Spec as Spec8141
from .helpers import (
    INPUT_SIZE,
    OUTPUT_OFFSET,
    SENTINEL,
    fund_signer,
    recover,
    signed_input,
)
from .spec import ref_spec_8151

REFERENCE_SPEC_GIT_PATH = ref_spec_8151.git_path
REFERENCE_SPEC_VERSION = ref_spec_8151.version

pytestmark = pytest.mark.valid_from("EIP8151")

APPROVE_ALL = Op.APPROVE(0, 0, Spec8141.APPROVE_EXECUTION_AND_PAYMENT)
"""Code of a sender that approves the transaction unconditionally."""


def sender_entry(sender: EOA) -> FrameSignature:
    """Return the sender's secp256k1 entry over the canonical hash."""
    return FrameSignature(
        scheme=Spec8141.SCHEME_SECP256K1, signer=Bytes(sender)
    )


@pytest.mark.parametrize(
    "sender_has_code",
    [
        pytest.param(False, id="empty-code"),
        pytest.param(True, id="contract", marks=pytest.mark.pre_alloc_mutable),
    ],
)
def test_signature_entry_ignores_signer_code(
    state_test: StateTestFiller,
    pre: Alloc,
    sender_has_code: bool,
) -> None:
    """
    Test that the protocol accepts the sender's secp256k1 signature entry
    whatever the sender's code, while ecrecover of the same key in a later
    frame withholds a sender whose code is not a delegation designation.
    """
    sender = pre.fund_eoa(code=APPROVE_ALL if sender_has_code else None)

    # Empty output leaves the sentinel in the output word.
    storage = Storage()
    probe = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.MSTORE(OUTPUT_OFFSET, SENTINEL)
        + Op.SSTORE(storage.store_next(1, "success"), recover())
        + Op.SSTORE(
            storage.store_next(
                SENTINEL if sender_has_code else int.from_bytes(sender),
                "output",
            ),
            Op.MLOAD(OUTPUT_OFFSET),
        ),
        storage=storage.canary(),
    )

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(target=probe, data=signed_input(sender)),
        ],
        signatures=[sender_entry(sender)],
    )

    # The probe's storage shows the transaction was included.
    state_test(pre=pre, post={probe: Account(storage=storage)}, tx=tx)


@pytest.mark.parametrize(
    "gas_delta,call_succeeds",
    [
        pytest.param(0, True, id="exact"),
        pytest.param(-1, False, id="minus-one"),
    ],
)
@pytest.mark.parametrize(
    "signer_is_sender",
    [
        pytest.param(True, id="sender"),
        pytest.param(False, id="signature-entry-signer"),
    ],
)
def test_frame_signer_warmth(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    signer_is_sender: bool,
    gas_delta: int,
    call_succeeds: bool,
) -> None:
    """
    Test that ecrecover in a frame prices the transaction sender's code
    check warm, and a second signature entry's signer cold, even though
    the protocol recovered that signer while validating the entry.
    """
    sender = pre.fund_eoa()
    entry_signer = pre.fund_eoa()
    signer = sender if signer_is_sender else entry_signer

    storage = Storage()
    probe = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.SSTORE(
            storage.store_next(int(call_succeeds), "success"),
            recover(
                gas=fork.ecrecover_gas(
                    recovered=True, address_warm=signer_is_sender
                )
                + gas_delta
            ),
        ),
        storage=storage.canary(),
    )

    # The probe runs before any frame enters the sender, so only the
    # transaction's initial warm set prices the code check.
    tx = Transaction(
        sender=sender,
        frames=[
            default_frame(target=probe, data=signed_input(signer)),
            verify_frame(),
        ],
        signatures=[
            sender_entry(sender),
            FrameSignature(
                scheme=Spec8141.SCHEME_SECP256K1,
                signer=Bytes(entry_signer),
                secret_key=entry_signer.key,
            ),
        ],
    )

    state_test(pre=pre, post={probe: Account(storage=storage)}, tx=tx)


@pytest.mark.parametrize(
    "owner_has_code",
    [
        pytest.param(False, id="balance-only"),
        pytest.param(
            True,
            id="contract",
            marks=[pytest.mark.pre_alloc_mutable, pytest.mark.exception_test],
        ),
    ],
)
def test_verify_frame_recovers_owner(
    state_test: StateTestFiller,
    pre: Alloc,
    owner_has_code: bool,
) -> None:
    """
    Test that a contract sender whose `VERIFY` frame approves only when
    ecrecover returns its owner invalidates the transaction once the
    owner has code that is not a delegation designation.
    """
    owner = fund_signer(pre, has_code=owner_has_code)
    sender = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.POP(recover())
        + Conditional(
            condition=Op.EQ(Op.MLOAD(OUTPUT_OFFSET), owner),
            if_true=APPROVE_ALL,
            if_false=Op.REVERT(0, 0),
        ),
        balance=10**18,
    )

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[verify_frame(data=signed_input(owner))],
        error=(
            TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
            if owner_has_code
            else None
        ),
    )

    state_test(
        pre=pre,
        post={sender: Account(nonce=1 if owner_has_code else 2)},
        tx=tx,
    )
