"""
EOF Container: check how every opcode behaves in the middle of the valid eof container code
"""
from typing import List

import pytest

from ethereum_test_tools import Bytecode, EOFTestFiller, Opcode
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import UndefinedOpcodes
from ethereum_test_tools.eof.v1 import Container, ContainerKind, EOFException, Section

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


@pytest.fixture
def expect_exception(opcode: Opcode) -> EOFException | None:
    """
    Returns exception that eof container reports when having this opcode in the middle of the code
    """
    if opcode in invalid_eof_opcodes or opcode in list(UndefinedOpcodes):
        return EOFException.UNDEFINED_INSTRUCTION
    return None


@pytest.fixture
def bytecode(opcode: Opcode) -> Opcode | Bytecode:
    """
    Construct a valid stack and bytes for the opcode
    """
    code: Opcode | Bytecode = Op.PUSH1[0] * 20
    if opcode.data_portion_length == 0 and opcode.data_portion_formatter is None:
        code += opcode
    else:
        code += opcode[1 if opcode == Op.CALLF else 0]
    if opcode not in halting_opcodes:
        return code + Op.STOP
    return code


@pytest.fixture
def sections(
    opcode: Opcode,
    bytecode: Opcode | Bytecode,
) -> List[Section]:
    """
    Returns extra sections that are needed for the opcode
    """
    sections = [Section.Code(code=bytecode)]

    match opcode:
        case Op.EOFCREATE | Op.RETURNCONTRACT:
            sections.append(
                Section.Container(
                    container=Container(
                        sections=[
                            Section.Code(code=Op.REVERT(0, 0)),
                        ]
                    )
                )
            )
        case Op.CALLF:
            sections.append(
                Section.Code(
                    code=Op.RETF,
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=0,
                )
            )
    sections.append(Section.Data("1122334455667788" * 4))
    return sections


@pytest.mark.parametrize(
    "opcode", [op for op in list(Op) + list(UndefinedOpcodes) if op != Op.RETF]
)
def test_all_opcodes_in_container(
    eof_test: EOFTestFiller,
    sections: List[Section],
    expect_exception: EOFException | None,
    opcode: Opcode,
):
    """
    Test all opcodes inside valid container
    257 because 0x5B is duplicated
    """
    if opcode == Op.RETURNCONTRACT:
        eof_code = Container(sections=sections, kind=ContainerKind.INITCODE)
    else:
        eof_code = Container(sections=sections)

    eof_test(
        data=eof_code,
        expect_exception=expect_exception,
    )
