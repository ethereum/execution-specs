"""Helpers for EIP-8141 frame transaction tests."""

from typing import Any, Dict

from execution_testing import Fork, Frame

from .spec import Spec


def default_code_frame_gas(fork: Fork, *, target_warm: bool) -> int:
    """
    Return the execution gas a frame running the protocol default code
    reports in its receipt.

    The default code draws no execution gas of its own, so the frame's
    only charge is its resolved target's access at frame entry, warm or
    cold per `target_warm`. A frame that resolves to the transaction
    sender finds it warm, the sender seeding every frame's warm set; a
    frame targeting a sponsor usually does not.
    """
    return fork.frame_entry_gas_calculator()(target_warm=target_warm)


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
    )
    kwargs.update(overrides)
    return Frame(**kwargs)


def expiry_frame(**overrides: Any) -> Frame:
    """
    Return a `VERIFY` frame targeting the expiry verifier predeploy
    with the maximum expiry timestamp, so it never expires.

    An expiry verifier frame is only valid with a zero state gas
    budget, so the frame overrides the framework's default explicitly.

    Keyword arguments override the corresponding frame fields, for
    variants that differ from the canonical frame in a single field.
    """
    kwargs: Dict[str, Any] = dict(
        mode=Spec.MODE_VERIFY,
        flags=Spec.APPROVE_NONE,
        target=Spec.EXPIRY_VERIFIER,
        state_gas_limit=0,
        data=(2**64 - 1).to_bytes(Spec.EXPIRY_DATA_LENGTH, "big"),
    )
    kwargs.update(overrides)
    return Frame(**kwargs)
