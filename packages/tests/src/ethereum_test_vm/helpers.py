"""Helper functions for the EVM."""

from .bytecode import Bytecode
from .opcodes import Opcodes as Op


class MemoryVariable(Bytecode):
    """
    Variable abstraction to help keep track values that are stored in memory.

    To use, simply declare a variable with an unique offset that is not used
    by any other variable.

    The variable then can be used in-place to read the value from memory:

    ```python
    v = MemoryVariable(128)

    bytecode = Op.ADD(v, Op.CALLDATASIZE())
    ```

    The previous example is equivalent to:

    ```python
    bytecode = Op.ADD(Op.MLOAD(offset=128), Op.CALLDATASIZE())
    ```

    The variable also contains methods to add and subtract values from the
    memory offset.

    ```python
    v = MemoryVariable(128)

    bytecode = (
        v.set(0xff)
        + v.add(1)
        + v.return_value()
    )
    ```

    The previous example is equivalent to:

    ```python
    bytecode = (
        Op.MSTORE(offset=128, value=0xff)
        + Op.MSTORE(offset=128, value=Op.ADD(Op.MLOAD(offset=128), 1))
        + Op.RETURN(offset=128, size=32)
    )
    ```

    """

    offset: int

    def __new__(cls, offset: int) -> "MemoryVariable":
        """
        Instantiate a new EVM memory variable.

        When used with normal bytecode, this class simply returns the MLOAD
        with the provided offset.
        """
        instance = super().__new__(cls, Op.MLOAD(offset=offset))
        instance.offset = offset
        return instance

    def set(self, value: int | Bytecode) -> Bytecode:
        """Set the given value at the memory location of this variable."""
        return Op.MSTORE(offset=self.offset, value=value)

    def add(self, value: int | Bytecode) -> Bytecode:
        """In-place add the given value to the one currently in memory."""
        return Op.MSTORE(
            offset=self.offset,
            value=Op.ADD(Op.MLOAD(offset=self.offset), value),
        )

    def sub(self, value: int | Bytecode) -> Bytecode:
        """
        In-place subtract the given value from the one currently
        in memory.
        """
        return Op.MSTORE(
            offset=self.offset,
            value=Op.SUB(Op.MLOAD(offset=self.offset), value),
        )

    def store_value(self, key: int | Bytecode) -> Bytecode:
        """Op.SSTORE the value that is currently in memory."""
        return Op.SSTORE(key, Op.MLOAD(offset=self.offset))

    def return_value(self) -> Bytecode:
        """Op.RETURN the value that is currently in memory."""
        return Op.RETURN(offset=self.offset, size=32)


def call_return_code(
    opcode: Op, success: bool, *, revert: bool = False
) -> int:
    """Return return code for a CALL operation."""
    if opcode in [Op.CALL, Op.CALLCODE, Op.DELEGATECALL, Op.STATICCALL]:
        return int(success)
    elif opcode in [Op.EXTCALL, Op.EXTDELEGATECALL, Op.EXTSTATICCALL]:
        if success:
            return 0
        if revert:
            return 1
        return 2
    raise ValueError(f"Not a call opcode: {opcode}")
