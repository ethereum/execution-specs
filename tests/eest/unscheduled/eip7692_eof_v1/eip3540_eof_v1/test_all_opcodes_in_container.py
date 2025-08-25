"""EOF Container: check how every opcode behaves in the middle of the valid eof container code."""

import itertools
from typing import Any, Dict, Generator, List, Tuple

import pytest

from ethereum_test_tools import EOFException, EOFTestFiller, Opcode, UndefinedOpcodes
from ethereum_test_tools import Opcodes as Op
from ethereum_test_types.eof.constants import MAX_RUNTIME_STACK_HEIGHT
from ethereum_test_types.eof.v1 import Container, ContainerKind, Section
from ethereum_test_types.eof.v1.constants import MAX_STACK_INCREASE_LIMIT
from ethereum_test_vm import Bytecode

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-3540.md"
REFERENCE_SPEC_VERSION = "8dcb0a8c1c0102c87224308028632cc986a61183"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)

all_opcodes = set(Op)
undefined_opcodes = set(UndefinedOpcodes)

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

valid_eof_opcodes = all_opcodes - invalid_eof_opcodes

# Halting the execution opcodes can be placed without STOP instruction at the end
halting_opcodes = {
    Op.STOP,
    Op.RETURNCODE,
    Op.RETURN,
    Op.REVERT,
    Op.INVALID,
}

# Opcodes that end the code section and can be placed without STOP instruction at the end
section_terminating_opcodes = {
    Op.RETF,
    Op.JUMPF,
}

data_portion_opcodes = {op for op in all_opcodes if op.has_data_portion()}


# NOTE: `sorted` is used to ensure that the tests are collected in a deterministic order.


@pytest.mark.parametrize(
    "opcode",
    sorted((all_opcodes | undefined_opcodes) - {Op.RETF}),
)
def test_all_opcodes_in_container(
    eof_test: EOFTestFiller,
    opcode: Opcode,
):
    """
    Test all opcodes inside valid container
    257 because 0x5B is duplicated.
    """
    data_portion = 1 if opcode == Op.CALLF else 0
    opcode_with_data_portion = opcode[data_portion] if opcode.has_data_portion() else opcode

    # opcode_with_data_portion has the correct minimum stack height
    bytecode = Op.PUSH0 * opcode_with_data_portion.min_stack_height + opcode_with_data_portion

    if opcode not in (halting_opcodes | section_terminating_opcodes):
        bytecode += Op.STOP

    sections = [Section.Code(code=bytecode)]

    match opcode:
        case Op.EOFCREATE | Op.RETURNCODE:
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
                    code_outputs=0,
                )
            )
    sections.append(Section.Data("1122334455667788" * 4))

    if opcode == Op.RETURNCODE:
        eof_code = Container(sections=sections, kind=ContainerKind.INITCODE)
    else:
        eof_code = Container(sections=sections)

    eof_test(
        container=eof_code,
        expect_exception=(
            None if opcode in valid_eof_opcodes else EOFException.UNDEFINED_INSTRUCTION
        ),
    )


@pytest.mark.parametrize(
    "opcode",
    sorted(invalid_eof_opcodes | undefined_opcodes),
)
@pytest.mark.parametrize(
    "terminating_opcode",
    sorted(halting_opcodes) + [Op.RJUMP],
)
def test_invalid_opcodes_after_stop(
    eof_test: EOFTestFiller,
    opcode: Opcode,
    terminating_opcode: Opcode,
):
    """Test that an invalid opcode placed after STOP (terminating instruction) invalidates EOF."""
    terminating_code = Bytecode(terminating_opcode)
    match terminating_opcode:  # Enhance the code for complex opcodes.
        case Op.RETURNCODE:
            terminating_code = Op.RETURNCODE[0]
        case Op.RETURN | Op.REVERT:
            terminating_code = Op.PUSH0 + Op.PUSH0 + terminating_opcode
        case Op.RJUMP:
            terminating_code = Op.RJUMP[-3]

    eof_code = Container(
        kind=ContainerKind.INITCODE
        if terminating_opcode == Op.RETURNCODE
        else ContainerKind.RUNTIME,
        sections=[
            Section.Code(code=terminating_code + opcode),
            Section.Data("00" * 32),
        ]
        + (
            [Section.Container(container=Container.Code(Op.INVALID))]
            if terminating_opcode == Op.RETURNCODE
            else []
        ),
    )

    eof_test(
        container=eof_code,
        expect_exception=EOFException.UNDEFINED_INSTRUCTION,
    )


@pytest.mark.parametrize(
    "opcode",
    sorted(
        valid_eof_opcodes
        - halting_opcodes
        - section_terminating_opcodes
        - {Op.RJUMP, Op.RJUMPI, Op.RJUMPV}
    ),
)
def test_all_invalid_terminating_opcodes(
    eof_test: EOFTestFiller,
    opcode: Opcode,
):
    """Test all opcodes that are invalid as the last opcode in a container."""
    if opcode.has_data_portion():
        # Add the appropriate data portion to the opcode by using the get_item method.
        # On the CALLF opcode we need to reference the second code section, hence the [1] index.
        opcode = opcode[0] if opcode != Op.CALLF else opcode[1]

    bytecode = (Op.PUSH0 * opcode.min_stack_height) + opcode

    sections = [Section.Code(code=bytecode)]

    if opcode == Op.CALLF[1]:
        sections += [Section.Code(code=Op.RETF, code_outputs=0)]
    elif opcode == Op.EOFCREATE[0]:
        sections += [
            Section.Container(
                container=Container(
                    sections=[
                        Section.Code(code=Op.RETURNCODE[0](0, 0)),
                        Section.Container(Container.Code(code=Op.STOP)),
                    ]
                )
            )
        ]

    sections += [Section.Data(b"\0" * 32)]

    eof_test(
        container=Container(
            sections=sections,
        ),
        expect_exception=EOFException.MISSING_STOP_OPCODE,
    )


@pytest.mark.parametrize(
    "opcode",
    sorted(halting_opcodes | section_terminating_opcodes),
)
def test_all_unreachable_terminating_opcodes_after_stop(
    eof_test: EOFTestFiller,
    opcode: Opcode,
):
    """Test all terminating opcodes after stop."""
    match opcode:
        case Op.STOP:
            sections = [Section.Code(code=Op.STOP + Op.STOP)]
        case Op.RETF:
            sections = [
                Section.Code(code=Op.CALLF[1] + Op.STOP),
                Section.Code(code=Op.STOP + Op.RETF, code_outputs=0),
            ]
        case Op.JUMPF:
            sections = [
                Section.Code(code=Op.STOP + Op.JUMPF[1]),
                Section.Code(code=Op.STOP),
            ]
        case Op.RETURNCODE:
            sections = [
                Section.Code(code=Op.EOFCREATE[0](0, 0, 0, 0) + Op.STOP),
                Section.Container(
                    container=Container(
                        sections=[
                            Section.Code(code=Op.STOP + Op.RETURNCODE[0](0, 0)),
                            Section.Container(Container.Code(code=Op.STOP)),
                        ]
                    )
                ),
            ]
        case Op.RETURN | Op.REVERT | Op.INVALID:
            sections = [
                Section.Code(code=Op.PUSH0 + Op.PUSH0 + Op.STOP + opcode),
            ]
        case _:
            raise NotImplementedError(f"Opcode {opcode} is not implemented")

    eof_test(
        container=Container(
            sections=sections,
        ),
        expect_exception=EOFException.UNREACHABLE_INSTRUCTIONS
        if opcode != Op.RETURNCODE
        else EOFException.INCOMPATIBLE_CONTAINER_KIND,
    )


@pytest.mark.parametrize(
    "opcode",
    sorted((halting_opcodes | section_terminating_opcodes) - {Op.STOP}),
)
def test_all_unreachable_terminating_opcodes_before_stop(
    eof_test: EOFTestFiller,
    opcode: Opcode,
):
    """Test all opcodes terminating opcodes before."""
    match opcode:
        case Op.RETF:
            sections = [
                Section.Code(code=Op.CALLF[1] + Op.STOP),
                Section.Code(code=Op.RETF + Op.STOP, code_outputs=0),
            ]
        case Op.JUMPF:
            sections = [
                Section.Code(code=Op.JUMPF[1] + Op.STOP),
                Section.Code(code=Op.STOP),
            ]
        case Op.RETURNCODE:
            sections = [
                Section.Code(code=Op.EOFCREATE[0](0, 0, 0, 0) + Op.STOP),
                Section.Container(
                    container=Container(
                        sections=[
                            Section.Code(code=Op.RETURNCODE[0](0, 0) + Op.STOP),
                            Section.Container(Container.Code(code=Op.STOP)),
                        ]
                    )
                ),
            ]
        case Op.RETURN | Op.REVERT | Op.INVALID:
            sections = [
                Section.Code(code=Op.PUSH1(0) + Op.PUSH1(0) + opcode + Op.STOP),
            ]
        case _:
            raise NotImplementedError(f"Opcode {opcode} is not implemented")

    eof_test(
        container=Container(
            sections=sections,
        ),
        expect_exception=EOFException.UNREACHABLE_INSTRUCTIONS
        if opcode != Op.RETURNCODE
        else EOFException.INCOMPATIBLE_CONTAINER_KIND,
    )


@pytest.mark.parametrize(
    "opcode",
    sorted(op for op in valid_eof_opcodes if op.pushed_stack_items > op.popped_stack_items)
    + [
        Op.DUPN[0xFF],
    ],
)
@pytest.mark.parametrize(
    "exception",
    # We test two types of exceptions here:
    # 1. Invalid max stack height, where we modify the `max_stack_height` field of the code section
    #    to the maximum stack height allowed by the EIP-3540, so the code still has to be checked
    #    for stack overflow.
    # 2. Max stack height above limit, where we don't modify the `max_stack_height` field of the
    #    code section, so the actual code doesn't have to be verified for the stack overflow.
    [EOFException.INVALID_MAX_STACK_INCREASE, EOFException.MAX_STACK_INCREASE_ABOVE_LIMIT],
)
def test_all_opcodes_stack_overflow(
    eof_test: EOFTestFiller,
    opcode: Opcode,
    exception: EOFException,
):
    """Test stack overflow on all opcodes that push more items than they pop."""
    opcode = opcode[0] if opcode.has_data_portion() else opcode

    assert opcode.pushed_stack_items - opcode.popped_stack_items == 1
    opcode_count = MAX_RUNTIME_STACK_HEIGHT - opcode.min_stack_height

    bytecode = Op.PUSH0 * opcode.min_stack_height
    bytecode += opcode * opcode_count
    bytecode += Op.STOP

    kwargs: Dict[str, Any] = {"code": bytecode}

    if exception == EOFException.INVALID_MAX_STACK_INCREASE:
        # Lie about the max stack height to make the code be checked for stack overflow.
        kwargs["max_stack_height"] = MAX_STACK_INCREASE_LIMIT

    sections = [Section.Code(**kwargs)]

    if opcode == Op.DATALOADN[0]:
        sections.append(Section.Data(b"\0" * 32))
    eof_code = Container(sections=sections)

    eof_test(
        container=eof_code,
        expect_exception=exception,
    )


def valid_opcode_combinations(
    compute_max_stack_height_options: List[bool],
    truncate_all_options: List[bool],
    opcodes: List[Opcode],
) -> Generator[Tuple[bool, bool, Opcode], None, None]:
    """Create valid parameter combinations for test_truncated_data_portion_opcodes()."""
    for opcode, truncate_all, compute_max_stack_height in itertools.product(
        opcodes, truncate_all_options, compute_max_stack_height_options
    ):
        opcode_with_data_portion: bytes = bytes(opcode[1])

        # Skip invalid or redundant combinations to avoid using pytest.skip in the test
        if len(opcode_with_data_portion) == 2 and truncate_all:
            continue
        if (
            compute_max_stack_height
            and max(opcode.min_stack_height, opcode.pushed_stack_items) == 0
        ):
            continue

        yield compute_max_stack_height, truncate_all, opcode


@pytest.mark.parametrize(
    "compute_max_stack_height, truncate_all, opcode",
    valid_opcode_combinations([False, True], [False, True], sorted(data_portion_opcodes)),
)
def test_truncated_data_portion_opcodes(
    eof_test: EOFTestFiller,
    opcode: Opcode,
    truncate_all: bool,
    compute_max_stack_height: bool,
):
    """
    Test that an instruction with data portion and truncated immediate bytes
    (therefore a terminating instruction is also missing) invalidates EOF.
    """
    opcode_with_data_portion: bytes = bytes(opcode[1])

    # Compose instruction bytes with empty imm bytes (truncate_all) or 1 byte shorter imm bytes.
    opcode_bytes = opcode_with_data_portion[0:1] if truncate_all else opcode_with_data_portion[:-1]

    if opcode.min_stack_height > 0:
        opcode_bytes = bytes(Op.PUSH0 * opcode.min_stack_height) + opcode_bytes

    max_stack_height = (
        max(opcode.min_stack_height, opcode.pushed_stack_items) if compute_max_stack_height else 0
    )

    eof_code = Container(
        sections=[
            Section.Code(opcode_bytes, max_stack_height=max_stack_height),
            # Provide data section potentially confused with missing imm bytes.
            Section.Data(b"\0" * 64),
        ]
    )
    eof_test(
        container=eof_code,
        expect_exception=EOFException.TRUNCATED_INSTRUCTION,
    )
