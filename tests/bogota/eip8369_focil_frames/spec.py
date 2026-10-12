"""Identify the draft frame inclusion-list specification under test."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Identify the specification file and its reviewed blob."""

    git_path: str
    version: str


ref_spec_8369 = ReferenceSpec(
    "EIPS/eip-8369.md", "fb0b606f5d319bb74badd1f6d5f9098375fc31c6"
)
