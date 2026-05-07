"""Defines spec constants for the IDENTITY precompile."""

from dataclasses import dataclass

from execution_testing import Address


@dataclass(frozen=True)
class Spec:
    """Parameters for the IDENTITY precompile (frontier)."""

    IDENTITY = Address(0x04)
