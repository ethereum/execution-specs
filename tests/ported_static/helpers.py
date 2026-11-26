"""Helpers shared by the ported static tests."""

from enum import StrEnum

from execution_testing import Bytecode, Bytes, Hash
from execution_testing.vm import Op


class Operands:
    """
    Supply operands as PUSH immediates or as successive calldata words.

    Build the code through an instance, then send `calldata` with the
    transaction. With `Operands.Source.PUSH` each value is pushed as an
    immediate and the calldata stays empty. With `Operands.Source.CALLDATA`
    each value is appended to the calldata as a 32-byte word and read back
    with a `CALLDATALOAD`, in the order the values are requested.
    """

    class Source(StrEnum):
        """How operands reach the stack."""

        PUSH = "push"
        CALLDATA = "calldata"

    def __init__(self, source: Source) -> None:
        """Start with empty calldata."""
        self.source = source
        self.calldata = Bytes()

    def __call__(self, value: int) -> int | Bytecode:
        """Return `value` itself, or a load of it from fresh calldata."""
        if self.source == Operands.Source.PUSH:
            return value
        if self.source == Operands.Source.CALLDATA:
            offset = len(self.calldata)
            self.calldata = Bytes(self.calldata + Hash(value))
            return Op.CALLDATALOAD(offset)
        raise ValueError(f"Unknown operand source: {self.source}")


class Memory:
    """Byte-level model of EVM memory, grown in 32-byte words."""

    def __init__(self) -> None:
        """Start with empty memory."""
        self.data = bytearray()

    def expand(self, end: int) -> None:
        """Grow memory to cover `[0, end)`, rounded up to a word."""
        size = (end + 31) // 32 * 32
        if size > len(self.data):
            self.data.extend(bytes(size - len(self.data)))

    def store(self, offset: int, value: int) -> None:
        """Write `value` as a word at `offset`, like MSTORE."""
        self.expand(offset + 32)
        self.data[offset : offset + 32] = value.to_bytes(32, "big")

    def store8(self, offset: int, value: int) -> None:
        """Write the low byte of `value` at `offset`, like MSTORE8."""
        self.expand(offset + 1)
        self.data[offset] = value & 0xFF

    def load(self, offset: int) -> int:
        """Return the word at `offset`, expanding memory like MLOAD."""
        self.expand(offset + 32)
        return int.from_bytes(self.data[offset : offset + 32], "big")

    def read(self, offset: int, size: int) -> bytes:
        """
        Return the `size` bytes at `offset`, like a LOG or RETURN range.

        An empty range does not expand memory, whatever its offset.
        """
        if size == 0:
            return b""
        self.expand(offset + size)
        return bytes(self.data[offset : offset + size])

    @property
    def size(self) -> int:
        """Return what MSIZE reports."""
        return len(self.data)
