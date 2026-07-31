"""Helpers for EIP-8141 frame transaction tests."""

from execution_testing import Bytecode, Op

from .spec import Spec


def approve_bytecode(
    scope: int = Spec.APPROVE_EXECUTION_AND_PAYMENT,
) -> Bytecode:
    """
    Return bytecode that calls `APPROVE` with the given scope and no
    return data.

    `APPROVE` succeeds only when the executing account is the frame's
    resolved target, so this code is meant to be deployed at the account
    a `VERIFY` frame targets.
    """
    return Op.APPROVE(0, 0, scope)
