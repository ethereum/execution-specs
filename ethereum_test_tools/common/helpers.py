"""
Helper functions/classes used to generate Ethereum tests.
"""

from dataclasses import dataclass

from ..code import Code, code_to_bytes


def to_address(input: int | str) -> str:
    """
    Converts an int or str into proper address 20-byte hex string.
    """
    if type(input) is str:
        # Convert to int
        input = int(input, 0)
    if type(input) is int:
        return "0x" + input.to_bytes(20, "big").hex()
    raise Exception("invalid type to convert to account address")


def to_hash(input: int | str) -> str:
    """
    Converts an int or str into proper address 20-byte hex string.
    """
    if type(input) is str:
        # Convert to int
        input = int(input, 0)
    if type(input) is int:
        return "0x" + input.to_bytes(32, "big").hex()
    raise Exception("invalid type to convert to hash")


@dataclass(kw_only=True)
class CodeGasMeasure(Code):
    """
    Helper class used to generate bytecode that measures gas usage of a
    bytecode, taking into account and subtracting any extra overhead gas costs
    required to execute.
    """

    code: bytes | str | Code
    """
    Bytecode to be executed to measure the gas usage.
    """
    overhead_cost: int
    """
    Extra gas cost to be subtracted from extra operations.
    """
    extra_stack_items: int = 0
    """
    Extra stack items that remain at the end of the execution.
    To be considered when subtracting the value of the previous GAS operation,
    and to be popped at the end of the execution.
    """
    sstore_key: int = 0
    """
    Storage key to save the gas used.
    """

    def assemble(self) -> bytes:
        res = bytes()
        res += bytes(
            [
                0x5A,  # GAS
            ]
        )
        res += code_to_bytes(self.code)  # Execute code to measure its gas cost
        res += bytes(
            [
                0x5A,  # GAS
            ]
        )
        # We need to swap and pop for each extra stack item that remained from
        # the execution of the code
        res += (
            bytes(
                [
                    0x90,  # SWAP1
                    0x50,  # POP
                ]
            )
            * self.extra_stack_items
        )
        res += bytes(
            [
                0x90,  # SWAP1
                0x03,  # SUB
                0x60,  # PUSH1
                self.overhead_cost + 2,  # Overhead cost + GAS opcode price
                0x90,  # SWAP1
                0x03,  # SUB
                0x60,  # PUSH1
                self.sstore_key,  # -> SSTORE key
                0x55,  # SSTORE
                0x00,  # STOP
            ]
        )
        return res
