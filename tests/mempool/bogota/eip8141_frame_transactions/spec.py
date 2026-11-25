"""Defines the EIP-8141 public mempool rules the tests exercise."""

from dataclasses import dataclass
from enum import StrEnum

from tests.bogota.eip8141_frame_transactions.spec import ref_spec_8141

__all__ = ["MempoolRule", "MempoolSpec", "ref_spec_8141"]


@dataclass(frozen=True)
class MempoolSpec:
    """Constants of the EIP-8141 public mempool rules."""

    MAX_VERIFY_GAS = 100_000
    MAX_VERIFY_STATE_GAS = 500_000


class MempoolRule(StrEnum):
    """
    IDs of the EIP-8141 rules of the public mempool rule set, from the
    EIP's "Mempool" section.
    """

    BANNED_OPCODE = "FRAME_TRANSACTION_VALIDATION_PREFIX_BANNED_OPCODE"
    """A banned opcode runs before the payer is set."""

    STORAGE_OUTSIDE_SENDER = (
        "FRAME_TRANSACTION_VALIDATION_PREFIX_STORAGE_OUTSIDE_SENDER"
    )
    """`SLOAD` reads storage outside `tx.sender` before the payer is set."""

    PREFIX_SHAPE = "FRAME_TRANSACTION_VALIDATION_PREFIX_SHAPE"
    """The validation prefix matches a recognized prefix shape."""

    VERIFY_GAS = "FRAME_TRANSACTION_VALIDATION_PREFIX_GAS_CAP"
    """
    Prefix execution limits plus signature validation fit
    `MAX_VERIFY_GAS`.
    """

    VERIFY_STATE_GAS = "FRAME_TRANSACTION_VALIDATION_PREFIX_STATE_GAS_CAP"
    """Prefix state limits fit `MAX_VERIFY_STATE_GAS`."""

    STATE_WRITE = "FRAME_TRANSACTION_VALIDATION_PREFIX_STATE_WRITE"
    """
    The prefix writes state only to install code at `tx.sender`, or to
    its storage, inside the first `deploy` frame.
    """

    PREFIX_REVERT = "FRAME_TRANSACTION_VALIDATION_PREFIX_REVERT"
    """No frame in the validation prefix reverts."""

    DEPLOY_INSTALLS_CODE = "FRAME_TRANSACTION_DEPLOY_FRAME_INSTALLS_CODE"
    """A `deploy` frame installs non-empty code at `tx.sender`."""
