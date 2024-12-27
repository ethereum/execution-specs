"""Helper functions for the EVM."""

from .opcode import Opcodes as Op


def call_return_code(opcode: Op, success: bool, *, revert: bool = False) -> int:
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
