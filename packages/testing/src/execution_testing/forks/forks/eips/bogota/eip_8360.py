"""
EIP-8360: TCREATE Opcode.

https://eips.ethereum.org/EIPS/eip-8360

Opcode ``0xF6`` is a placeholder pending assignment in the EIPs repo
(matches Nethermind's implementation).
"""

from typing import Callable, Dict, List

from execution_testing.vm import OpcodeBase, Opcodes

from ....base_fork import BaseFork


class EIP8360(BaseFork):
    """EIP-8360 class."""

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add TCREATE base gas cost (plus CREATE2-like dynamics at fill)."""
        gas_costs = cls.gas_costs()
        base_map = super(EIP8360, cls).opcode_gas_map()
        # Static portion used by the framework for rough estimates; the
        # EELS implementation charges OPCODE_TCREATE_BASE + CREATE_ACCESS
        # (+ memory / initcode / keccak) at runtime.
        return {
            **base_map,
            Opcodes.TCREATE: gas_costs.WARM_ACCESS + 32_000,
        }

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add TCREATE to valid opcodes."""
        return [
            Opcodes.TCREATE,
        ] + super(EIP8360, cls).valid_opcodes()
