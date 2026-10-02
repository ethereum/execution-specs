"""
EIP-8163: Reserve EXTENSION (0xae) opcode.

Reserve `EXTENSION` as an extension prefix for EVM chains other than
Ethereum L1, where it behaves exactly like `INVALID`.

https://eips.ethereum.org/EIPS/eip-8163
"""

from typing import Callable, Dict

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork


class EIP8163(BaseFork):
    """EIP-8163 class."""

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add EXTENSION, which halts exceptionally like INVALID."""
        base_map = super(EIP8163, cls).opcode_gas_map()
        return {
            **base_map,
            Opcodes.EXTENSION: 0,
        }
