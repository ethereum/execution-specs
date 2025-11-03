"""Simple opcode gas cost calculator for bytecode sequences."""

from typing import Any, Dict

from .bytecode import Bytecode
from .opcodes import Opcodes


class OpcodeGasCalculator:
    """
    Calculator for computing base gas costs of opcode sequences.
    """

    def __init__(self, fork: Any) -> None:
        """
        Initialize the calculator with a specific fork.

        Args:
            fork: Fork class (Prague or Osaka)
        """
        self.fork = fork
        self._byte_to_opcode: Dict[int, Opcodes] = {}
        for opcode_member in Opcodes:
            opcode_bytes = bytes(opcode_member._value_)
            if len(opcode_bytes) > 0:
                byte_value = opcode_bytes[0]
                self._byte_to_opcode[byte_value] = opcode_member

    def calculate(self, opcodes: Bytecode) -> int:
        """
        Calculate total base gas cost for an opcode sequence.

        Args:
            opcodes: Bytecode object (result of Op.XXX + Op.YYY + ...)

        Returns:
            Total base gas cost
        """
        # Get bytecode bytes
        bytecode = bytes(opcodes)

        total_gas = 0
        pc = 0  # Program counter

        while pc < len(bytecode):
            opcode_byte = bytecode[pc]

            # Look up opcode from byte value
            if opcode_byte in self._byte_to_opcode:
                opcode = self._byte_to_opcode[opcode_byte]

                # Get gas cost from fork using opcode.name
                gas_cost = self.fork.op_cost(opcode)
                total_gas += gas_cost

                # Skip data portion for PUSH instructions
                if 0x60 <= opcode_byte <= 0x7F:  # PUSH1 to PUSH32
                    push_size = opcode_byte - 0x5F
                    pc += push_size

            pc += 1

        return total_gas
