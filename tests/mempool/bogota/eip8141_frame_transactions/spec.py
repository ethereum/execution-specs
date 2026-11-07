"""Defines the EIP-8141 public mempool rules the tests exercise."""

from dataclasses import dataclass
from typing import Dict

from tests.bogota.eip8141_frame_transactions.spec import ref_spec_8141

__all__ = ["MempoolRule", "MempoolSpec", "RULE_SET", "ref_spec_8141"]

RULE_SET: Dict[str, str] = {"frame-transaction": "1"}
"""Admission rule set version the expectations assume."""


@dataclass(frozen=True)
class MempoolSpec:
    """Constants of the EIP-8141 public mempool rules."""

    MAX_VERIFY_GAS = 100_000
    MAX_VERIFY_STATE_GAS = 500_000


@dataclass(frozen=True)
class MempoolRule:
    """
    IDs of the EIP-8141 public mempool rules, as listed in the EIP's
    "Mempool" section.
    """

    BANNED_OPCODE = "FRAME-OP-001"
    """A banned opcode runs before the payer is set."""

    STORAGE_OUTSIDE_SENDER = "FRAME-STO-001"
    """`SLOAD` reads storage outside `tx.sender` before the payer is set."""

    PREFIX_SHAPE = "FRAME-PFX-001"
    """The validation prefix matches a recognized prefix shape."""

    VERIFY_GAS = "FRAME-GAS-001"
    """
    Prefix execution limits plus signature validation fit
    `MAX_VERIFY_GAS`.
    """

    VERIFY_STATE_GAS = "FRAME-GAS-002"
    """Prefix state limits fit `MAX_VERIFY_STATE_GAS`."""

    STATE_WRITE = "FRAME-WRT-001"
    """
    The prefix writes state only to install code at `tx.sender`, or to
    its storage, inside the first `deploy` frame.
    """

    PREFIX_REVERT = "FRAME-REV-001"
    """No frame in the validation prefix reverts."""

    DEPLOY_INSTALLS_CODE = "FRAME-DEP-001"
    """A `deploy` frame installs non-empty code at `tx.sender`."""
