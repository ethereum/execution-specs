"""Defines the EIP-8141 public mempool rules the tests exercise."""

from dataclasses import dataclass
from typing import Dict

from tests.bogota.eip8141_frame_transactions.spec import ref_spec_8141

__all__ = ["MempoolRule", "RULE_SET", "ref_spec_8141"]

RULE_SET: Dict[str, str] = {"frame-transaction": "1"}
"""Admission rule set version the expectations assume."""


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
