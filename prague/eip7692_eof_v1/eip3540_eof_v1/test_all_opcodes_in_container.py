"""
EOF Container: check how every opcode behaves in the middle of the valid eof container code
"""

import pytest

from ethereum_test_tools import Bytecode, EOFTestFiller, Opcode
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import UndefinedOpcodes
from ethereum_test_tools.eof.v1 import Container, EOFException, Section

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-3540.md"
REFERENCE_SPEC_VERSION = "8dcb0a8c1c0102c87224308028632cc986a61183"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)

# Invalid Opcodes will produce EOFException.UNDEFINED_INSTRUCTION when used in EOFContainer
invalid_eof_opcodes = {
    Op.CODESIZE,
    Op.SELFDESTRUCT,
    Op.CREATE2,
    Op.CODECOPY,
    Op.EXTCODESIZE,
    Op.EXTCODECOPY,
    Op.EXTCODEHASH,
    Op.JUMP,
    Op.JUMPI,
    Op.PC,
    Op.GAS,
    Op.CREATE,
    Op.CALL,
    Op.CALLCODE,
    Op.DELEGATECALL,
    Op.STATICCALL,
}

# Halting the execution opcodes can be placed without STOP instruction at the end
halting_opcodes = {
    Op.STOP,
    Op.JUMPF,
    Op.RETURNCONTRACT,
    Op.RETURN,
    Op.REVERT,
    Op.INVALID,
}

# Special eof opcodes that require [] operator
eof_opcodes = {
    Op.DATALOADN,
    Op.RJUMPV,
    Op.CALLF,
    Op.RETF,
    Op.JUMPF,
    Op.EOFCREATE,
    Op.RETURNCONTRACT,
    Op.EXCHANGE,
}


def expect_exception(opcode: Opcode) -> EOFException | None:
    """
    Returns exception that eof container reports when having this opcode in the middle of the code
    """
    if opcode in invalid_eof_opcodes or opcode in list(UndefinedOpcodes):
        return EOFException.UNDEFINED_INSTRUCTION

    # RETF not allowed in first section
    if opcode == Op.RETF:
        return EOFException.INVALID_NON_RETURNING_FLAG
    return None


def make_opcode_valid_bytes(opcode: Opcode) -> Opcode | Bytecode:
    """
    Construct a valid stack and bytes for the opcode
    """
    code: Opcode | Bytecode
    if opcode.data_portion_length == 0 and opcode.data_portion_formatter is None:
        code = opcode
    elif opcode == Op.CALLF:
        code = opcode[1]
    else:
        code = opcode[0]
    if opcode not in halting_opcodes:
        return code + Op.STOP
    return code


def eof_opcode_stack(opcode: Opcode) -> int:
    """
    Eof opcode has special stack influence
    """
    if opcode in eof_opcodes:
        if opcode == Op.CALLF or opcode == Op.JUMPF or opcode == Op.EXCHANGE:
            return 0
        return 1
    return 0


@pytest.mark.parametrize("opcode", list(Op) + list(UndefinedOpcodes))
def test_all_opcodes_in_container(eof_test: EOFTestFiller, opcode: Opcode):
    """
    Test all opcodes inside valid container
    257 because 0x5B is duplicated
    """
    section_call = []
    if opcode == Op.CALLF:
        section_call = [
            Section.Code(
                code=Op.RETF,
                code_inputs=0,
                code_outputs=0,
                max_stack_height=0,
            )
        ]

    eof_code = Container(
        sections=[
            Section.Code(
                code=Op.PUSH1(00) * 20 + make_opcode_valid_bytes(opcode),
                max_stack_height=max(
                    20,
                    20
                    + opcode.pushed_stack_items
                    - opcode.popped_stack_items
                    + eof_opcode_stack(opcode),
                ),
            ),
            Section.Container(
                container=Container(
                    sections=[
                        Section.Code(code=Op.STOP),
                    ]
                )
            ),
        ]
        + section_call
        + [
            Section.Data("1122334455667788" * 4),
        ],
    )

    eof_test(
        data=eof_code,
        expect_exception=expect_exception(opcode),
    )
