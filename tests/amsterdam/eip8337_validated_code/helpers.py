"""Shared helpers for the EIP-8337 tests."""

from execution_testing import Bytecode, Op

from .spec import Spec

TX_GAS_LIMIT = 2_000_000

SLOT_RESULT = 0
SLOT_MARKER = 1
MARKER = 0xA1


def raw(data: bytes) -> Bytecode:
    """Wrap raw bytes as Bytecode with no stack effect."""
    return Bytecode(data, popped_stack_items=0, pushed_stack_items=0)


def magic(body: Bytecode | bytes) -> Bytecode:
    """Return `body` behind the placeholder MAGIC header."""
    if isinstance(body, bytes):
        body = raw(body)
    return raw(Spec.MAGIC_HEADER) + body


def factory_code(create_opcode: Op, initcode_length: int) -> Bytecode:
    """
    Return factory code that copies the initcode from calldata, creates
    with `create_opcode`, and stores the created address (0 on failure) at
    ``SLOT_RESULT`` and the gas left afterwards at ``SLOT_MARKER``.
    """
    return (
        Op.CALLDATACOPY(offset=0, size=initcode_length)
        + Op.SSTORE(SLOT_RESULT, create_opcode(offset=0, size=initcode_length))
        + Op.SSTORE(SLOT_MARKER, Op.GT(Op.GAS, 100_000))
    )
