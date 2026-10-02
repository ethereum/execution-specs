"""Reference spec for [EIP-7979: Call and Return Opcodes for the EVM](https://eips.ethereum.org/EIPS/eip-7979)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_7979 = ReferenceSpec(
    git_path="EIPS/eip-7979.md",
    version="0b9221c7958ba4c5f2d11bfba355cafdbf2a3e1e",
)


class Spec:
    """Constants and parameters from EIP-7979."""

    # Placeholder opcode values, to be confirmed on final assignment.
    CALLSUB_OPCODE: int = 0xB0
    CALLDEST_OPCODE: int = 0xB1
    RETURNSUB_OPCODE: int = 0xB2

    # Gas costs: mid, jumpdest, low.
    CALLSUB_GAS: int = 8
    CALLDEST_GAS: int = 1
    RETURNSUB_GAS: int = 5

    # Maximum number of return addresses a frame's return stack may hold.
    RETURN_STACK_LIMIT: int = 1024
