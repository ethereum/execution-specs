"""Helpers for EIP-8141 frame transaction tests."""

from typing import Any, Dict

from execution_testing import Frame

from .spec import Spec

AMPLE_FRAME_GAS = 100_000
"""
Default frame gas limit, with ample headroom for the sender's default
code (signature validation plus `APPROVE`) or a small value transfer.
Tests that are not gas-sensitive should use this default rather than
picking a value.
"""


def verify_frame(**overrides: Any) -> Frame:
    """
    Return the `VERIFY` frame that approves execution and payment
    against the sender's default code.

    Keyword arguments override the corresponding frame fields, for
    variants that differ from the canonical frame in a single field.
    """
    kwargs: Dict[str, Any] = dict(
        mode=Spec.MODE_VERIFY,
        flags=Spec.APPROVE_EXECUTION_AND_PAYMENT,
        gas_limit=AMPLE_FRAME_GAS,
    )
    kwargs.update(overrides)
    return Frame(**kwargs)


def default_frame(**overrides: Any) -> Frame:
    """
    Return a `DEFAULT` frame executing the frame entry point.

    Keyword arguments override the corresponding frame fields, for
    variants that differ from the canonical frame in a single field.
    """
    kwargs: Dict[str, Any] = dict(
        mode=Spec.MODE_DEFAULT,
        gas_limit=AMPLE_FRAME_GAS,
    )
    kwargs.update(overrides)
    return Frame(**kwargs)


def sender_frame(**overrides: Any) -> Frame:
    """
    Return a `SENDER` frame executing as the sender at its resolved
    target.

    Keyword arguments override the corresponding frame fields, for
    variants that differ from the canonical frame in a single field.
    """
    kwargs: Dict[str, Any] = dict(
        mode=Spec.MODE_SENDER,
        gas_limit=AMPLE_FRAME_GAS,
    )
    kwargs.update(overrides)
    return Frame(**kwargs)


def expiry_frame(**overrides: Any) -> Frame:
    """
    Return a `VERIFY` frame targeting the expiry verifier predeploy
    with the maximum expiry timestamp, so it never expires.

    Keyword arguments override the corresponding frame fields, for
    variants that differ from the canonical frame in a single field.
    """
    kwargs: Dict[str, Any] = dict(
        mode=Spec.MODE_VERIFY,
        flags=Spec.APPROVE_NONE,
        target=Spec.EXPIRY_VERIFIER,
        gas_limit=AMPLE_FRAME_GAS,
        data=(2**64 - 1).to_bytes(Spec.EXPIRY_DATA_LENGTH, "big"),
    )
    kwargs.update(overrides)
    return Frame(**kwargs)
