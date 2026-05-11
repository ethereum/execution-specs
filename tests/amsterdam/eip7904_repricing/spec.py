"""Defines EIP-7904 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_7904 = ReferenceSpec(
    git_path="EIPS/eip-7904.md",
    version="",
    # TODO: Add version after eip revision released
)


@dataclass(frozen=True)
class Spec:
    """Updated gas costs from EIP-7904."""

    # Opcodes
    OPCODE_MOD: int = 6
    OPCODE_SDIV: int = 6
    OPCODE_SMOD: int = 6
    OPCODE_MULMOD: int = 12

    # Precompiles
    PRECOMPILE_BLAKE2F_BASE: int = 48
    PRECOMPILE_BLAKE2F_PER_ROUND: int = 1
    PRECOMPILE_ECADD: int = 382
    PRECOMPILE_P256VERIFY: int = 15958
    PRECOMPILE_POINT_EVALUATION: int = 84081

    # Precompile addresses
    ECADD_ADDRESS: int = 0x06
    BLAKE2F_ADDRESS: int = 0x09
    POINT_EVALUATION_ADDRESS: int = 0x0A
    P256VERIFY_ADDRESS: int = 0x100
