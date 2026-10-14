"""
EIP-9999: 64-bit Opcodes for the EVM.

Twenty-eight single-byte instructions computing on the low 64 bits of
their operands: the twin of each at its opcode plus 0xC0.

https://eips.ethereum.org/EIPS/eip-9999
"""

from typing import Callable, Dict, List

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork

# Gas tiers, each a step below the tier of the twin.
VERY_LOW_64 = 2
LOW_64 = 3
MID_64 = 5
EXP64_BASE = 5
EXP64_PER_BYTE = 25

VERY_LOW_64_OPCODES = [
    Opcodes.ADD64,
    Opcodes.SUB64,
    Opcodes.CALLDATALOAD64,
    Opcodes.LT64,
    Opcodes.GT64,
    Opcodes.SLT64,
    Opcodes.SGT64,
    Opcodes.EQ64,
    Opcodes.ISZERO64,
    Opcodes.AND64,
    Opcodes.OR64,
    Opcodes.XOR64,
    Opcodes.NOT64,
    Opcodes.SHL64,
    Opcodes.SHR64,
    Opcodes.SAR64,
]

LOW_64_OPCODES = [
    Opcodes.MUL64,
    Opcodes.DIV64,
    Opcodes.SDIV64,
    Opcodes.MOD64,
    Opcodes.SMOD64,
    Opcodes.SIGNEXTEND64,
    Opcodes.CLZ64,
]

MID_64_OPCODES = [
    Opcodes.ADDMOD64,
    Opcodes.MULMOD64,
]


class EIP9999(BaseFork):
    """EIP-9999 class."""

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add the 64-bit instructions to valid opcodes."""
        return (
            VERY_LOW_64_OPCODES
            + LOW_64_OPCODES
            + MID_64_OPCODES
            + [Opcodes.EXP64, Opcodes.MLOAD64, Opcodes.MSTORE64]
            + super(EIP9999, cls).valid_opcodes()
        )

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add the gas costs of the 64-bit instructions."""
        memory_expansion_calculator = cls.memory_expansion_gas_calculator()
        base_map = super(EIP9999, cls).opcode_gas_map()
        return {
            **base_map,
            **dict.fromkeys(VERY_LOW_64_OPCODES, VERY_LOW_64),
            **dict.fromkeys(LOW_64_OPCODES, LOW_64),
            **dict.fromkeys(MID_64_OPCODES, MID_64),
            Opcodes.EXP64: lambda op: (
                EXP64_BASE
                + EXP64_PER_BYTE
                * (((op.metadata["exponent"] % 2**64).bit_length() + 7) // 8)
            ),
            Opcodes.MLOAD64: cls._with_memory_expansion(
                VERY_LOW_64,
                memory_expansion_calculator,
            ),
            Opcodes.MSTORE64: cls._with_memory_expansion(
                VERY_LOW_64,
                memory_expansion_calculator,
            ),
        }
