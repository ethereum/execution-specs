"""Helpers for EIP-8141 frame transaction tests."""

from execution_testing import Frame

from .spec import Spec


def verify_frame() -> Frame:
    """
    Return the `VERIFY` frame that approves execution and payment
    against the sender's default code.
    """
    return Frame(
        mode=Spec.MODE_VERIFY,
        flags=Spec.APPROVE_EXECUTION_AND_PAYMENT,
        gas_limit=100_000,
    )
