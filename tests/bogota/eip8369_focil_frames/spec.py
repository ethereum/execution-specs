"""Identify the draft frame inclusion-list specification under test."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Identify the specification file and its reviewed blob."""

    git_path: str
    version: str


ref_spec_8369 = ReferenceSpec(
    "EIPS/eip-8369.md", "d679fc6bd41a211d7773c6cd22ffbb89c648e25b"
)
