"""
Public mempool validation budget tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

The public mempool bounds the work of simulating a transaction's
validation prefix: the prefix's execution budgets plus its signature
verification gas must not exceed `MAX_VERIFY_GAS`, and its state
budgets must not exceed `MAX_VERIFY_STATE_GAS`. Each test sends a
transaction at the limit, which must be admitted, and one past it,
which must be rejected. Filled, both land in a valid block: the limits
are mempool policy, not consensus.
"""

from typing import Callable

import pytest
from execution_testing import (
    EOA,
    Alloc,
    Bytes,
    Fork,
    FrameSignature,
    MempoolTestFiller,
    MempoolTransaction,
    Op,
    keccak256,
)

from .helpers import sender_frame
from .mempool_helpers import PrefixShape, prefix_transaction
from .signature_helpers import P256_SIGNATURE, p256_entry, signed_digest_entry
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")


@pytest.mark.parametrize(
    "expiry", [False, True], ids=["no_expiry", "expiry_first"]
)
@pytest.mark.parametrize("shape", list(PrefixShape), ids=str)
def test_verify_gas_cap(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    shape: PrefixShape,
    expiry: bool,
) -> None:
    """
    Test that a validation prefix using exactly `MAX_VERIFY_GAS` is
    admitted and one using one more is rejected, an opening expiry
    verifier frame counting toward the budget.
    """
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=prefix_transaction(
                    pre,
                    fork,
                    shape,
                    total_verify_gas=Spec.MAX_VERIFY_GAS,
                    expiry=expiry,
                ),
                accepted=True,
            ),
            MempoolTransaction(
                tx=prefix_transaction(
                    pre,
                    fork,
                    shape,
                    total_verify_gas=Spec.MAX_VERIFY_GAS + 1,
                    expiry=expiry,
                ),
                accepted=False,
                reason="validation prefix exceeds MAX_VERIFY_GAS",
            ),
        ],
    )


def arbitrary_entry() -> FrameSignature:
    """Return an `ARBITRARY` entry, verified by no protocol scheme."""
    return FrameSignature(
        scheme=Spec.SCHEME_ARBITRARY, msg=Bytes(b""), signature=b"\x01"
    )


DIGEST_SIGNER = EOA(key=1)
"""Signer of an extra secp256k1 entry, unrelated to any account."""


def secp256k1_entry() -> FrameSignature:
    """Return a valid secp256k1 entry over the explicit digest."""
    assert DIGEST_SIGNER.key is not None
    return signed_digest_entry(DIGEST_SIGNER.key, signer=Bytes(DIGEST_SIGNER))


def p256_signature_entry() -> FrameSignature:
    """Return a valid P256 entry over the explicit digest."""
    return p256_entry(
        r=int.from_bytes(P256_SIGNATURE[0:32], "big"),
        s=int.from_bytes(P256_SIGNATURE[32:64], "big"),
        qx=int.from_bytes(P256_SIGNATURE[64:96], "big"),
        qy=int.from_bytes(P256_SIGNATURE[96:128], "big"),
        signer=Bytes(keccak256(P256_SIGNATURE[64:128])[12:]),
    )


@pytest.mark.parametrize(
    "extra_signature",
    [
        pytest.param(arbitrary_entry, id="arbitrary"),
        pytest.param(secp256k1_entry, id="secp256k1"),
        pytest.param(p256_signature_entry, id="p256"),
    ],
)
def test_verify_gas_counts_signatures(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    extra_signature: Callable[[], FrameSignature],
) -> None:
    """
    Test that every signature entry's verification gas counts toward
    `MAX_VERIFY_GAS`, so an extra entry alone pushes a prefix whose
    frames fill the budget past the cap.
    """
    signature_gas = fork.frame_signature_verification_gas_calculator()(
        signatures=[extra_signature()]
    )
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=prefix_transaction(
                    pre,
                    fork,
                    PrefixShape.SELF_VERIFY,
                    total_verify_gas=Spec.MAX_VERIFY_GAS,
                    extra_signatures=[extra_signature()],
                ),
                accepted=True,
            ),
            MempoolTransaction(
                tx=prefix_transaction(
                    pre,
                    fork,
                    PrefixShape.SELF_VERIFY,
                    total_verify_gas=Spec.MAX_VERIFY_GAS + signature_gas,
                    extra_signatures=[extra_signature()],
                ),
                accepted=False,
                reason="signature verification exceeds MAX_VERIFY_GAS",
            ),
        ],
    )


@pytest.mark.parametrize("shape", list(PrefixShape), ids=str)
def test_verify_gas_ignores_frames_after_prefix(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    shape: PrefixShape,
) -> None:
    """
    Test that the budgets of frames after the validation prefix do not
    count toward `MAX_VERIFY_GAS`, while the prefix's own still do.
    """
    target = pre.deploy_contract(code=Op.STOP)

    def user_op() -> list:
        return [sender_frame(target=target, gas_limit=Spec.MAX_VERIFY_GAS)]

    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=prefix_transaction(
                    pre,
                    fork,
                    shape,
                    total_verify_gas=Spec.MAX_VERIFY_GAS,
                    after=user_op(),
                ),
                accepted=True,
            ),
            MempoolTransaction(
                tx=prefix_transaction(
                    pre,
                    fork,
                    shape,
                    total_verify_gas=Spec.MAX_VERIFY_GAS + 1,
                    after=user_op(),
                ),
                accepted=False,
                reason="validation prefix exceeds MAX_VERIFY_GAS",
            ),
        ],
    )


@pytest.mark.parametrize("shape", list(PrefixShape), ids=str)
def test_verify_state_gas_cap(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    shape: PrefixShape,
) -> None:
    """
    Test that a validation prefix budgeting exactly
    `MAX_VERIFY_STATE_GAS` is admitted and one budgeting one more is
    rejected.
    """
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=prefix_transaction(
                    pre,
                    fork,
                    shape,
                    total_verify_state_gas=Spec.MAX_VERIFY_STATE_GAS,
                ),
                accepted=True,
            ),
            MempoolTransaction(
                tx=prefix_transaction(
                    pre,
                    fork,
                    shape,
                    total_verify_state_gas=Spec.MAX_VERIFY_STATE_GAS + 1,
                ),
                accepted=False,
                reason="validation prefix exceeds MAX_VERIFY_STATE_GAS",
            ),
        ],
    )
