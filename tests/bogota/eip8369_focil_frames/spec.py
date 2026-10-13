"""Identify the draft frame inclusion-list specification under test."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Identify the specification file and its reviewed blob."""

    git_path: str
    version: str


ref_spec_8369 = ReferenceSpec(
    "EIPS/eip-8369.md", "41abab4f4d25f96826c78dfd510cbe56f97ad885"
)
