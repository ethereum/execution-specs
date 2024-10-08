"""
EOF validation tests for non-returning code sections.
"""

import pytest

from ethereum_test_tools import EOFException, EOFTestFiller
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_types.eof.v1 import NON_RETURNING_SECTION, ContainerKind
from ethereum_test_vm import Bytecode

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-6206.md"
REFERENCE_SPEC_VERSION = "2f365ea0cd58faa6e26013ea77ce6d538175f7d0"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


@pytest.mark.parametrize(
    "code_section",
    [
        pytest.param(Section.Code(Op.STOP, code_outputs=0), id="stop"),
        pytest.param(Section.Code(Op.INVALID, code_outputs=0), id="invalid0"),
        pytest.param(
            Section.Code(Op.ADDRESS + Op.POP + Op.INVALID, code_outputs=0), id="invalid1"
        ),
        pytest.param(Section.Code(Op.RETURN(0, 0), code_outputs=0), id="return"),
        pytest.param(Section.Code(Op.RETF, code_outputs=0), id="retf0"),
        pytest.param(Section.Code(Op.PUSH0 + Op.RETF, code_outputs=1), id="retf1"),
    ],
)
def test_first_section_returning(eof_test: EOFTestFiller, code_section: Section):
    """Test EOF validation failing because the first section is not non-returning."""
    eof_test(
        data=Container(
            sections=[code_section], validity_error=EOFException.INVALID_FIRST_SECTION_TYPE
        )
    )


@pytest.mark.parametrize(
    "code_section",
    [
        pytest.param(Section.Code(Op.STOP, code_outputs=0), id="stop0"),
        pytest.param(Section.Code(Op.PUSH0 + Op.STOP, code_outputs=1), id="stop1"),
        pytest.param(Section.Code(Op.INVALID, code_outputs=0), id="invalid0"),
        pytest.param(Section.Code(Op.PUSH0 + Op.INVALID, code_outputs=1), id="invalid1"),
        pytest.param(Section.Code(Op.RETURN(0, 0), code_outputs=0), id="return0"),
        pytest.param(Section.Code(Op.PUSH0 + Op.RETURN(0, 0), code_outputs=1), id="return1"),
        pytest.param(Section.Code(Op.REVERT(0, 0), code_outputs=0), id="revert0"),
        pytest.param(Section.Code(Op.PUSH0 + Op.REVERT(0, 0), code_outputs=1), id="revert1"),
        pytest.param(Section.Code(Op.RJUMP[-3], code_outputs=0), id="rjump0"),
        pytest.param(Section.Code(Op.PUSH0 + Op.RJUMP[-3], code_outputs=1), id="rjump1"),
    ],
)
def test_returning_section_not_returning(eof_test: EOFTestFiller, code_section: Section):
    """
    Test EOF validation failing because a returning section has no RETF or JUMPF-to-returning.
    """
    eof_test(
        data=Container(
            sections=[
                Section.Code(Op.CALLF[1] + Op.STOP, max_stack_height=code_section.code_outputs),
                code_section,
            ],
            validity_error=EOFException.INVALID_NON_RETURNING_FLAG,
        ),
    )


@pytest.mark.parametrize(
    "code_section",
    [
        pytest.param(
            Section.Code(Op.RETURNCONTRACT[0](0, 0), code_outputs=0), id="returncontract0"
        ),
        pytest.param(
            Section.Code(Op.PUSH0 + Op.RETURNCONTRACT[0](0, 0), code_outputs=1),
            id="returncontract1",
        ),
    ],
)
def test_returning_section_returncontract(eof_test: EOFTestFiller, code_section: Section):
    """
    Test EOF validation failing because a returning section has no RETF or JUMPF-to-returning -
    RETURNCONTRACT version
    """
    eof_test(
        data=Container(
            sections=[
                Section.Code(Op.CALLF[1] + Op.INVALID, max_stack_height=code_section.code_outputs),
                code_section,
            ]
            + [Section.Container(Container.Code(Op.INVALID))],
            validity_error=EOFException.INVALID_NON_RETURNING_FLAG,
            kind=ContainerKind.INITCODE,
        )
    )


first = pytest.mark.parametrize("first", [True, False])
code_prefix = pytest.mark.parametrize(
    "code_prefix",
    [
        Bytecode(),
        Op.PUSH0,
        pytest.param(Op.PUSH0 * NON_RETURNING_SECTION, id="PUSH0x0x80"),
    ],
)


@first
@code_prefix
def test_retf_in_nonreturning(eof_test: EOFTestFiller, first: bool, code_prefix: Bytecode):
    """
    Test EOF validation failing because a non-returning section contains the RETF instruction.
    """
    sections = [Section.Code(code_prefix + Op.RETF, code_outputs=NON_RETURNING_SECTION)]
    if not first:  # Prefix sections with additional valid JUMPF to invalid section
        sections = [Section.Code(Op.JUMPF[1])] + sections
    eof_test(
        data=Container(sections=sections, validity_error=EOFException.INVALID_NON_RETURNING_FLAG)
    )


@first
@code_prefix
def test_jumpf_in_nonreturning(eof_test: EOFTestFiller, first: bool, code_prefix: Bytecode):
    """
    Test EOF validation failing because a non-returning section contains the JUMPF instruction.
    """
    invalid_section = Section.Code(
        code_prefix + Op.JUMPF[1 if first else 2],
        code_outputs=NON_RETURNING_SECTION,
    )
    target_section = Section.Code(Op.RETF, code_outputs=0)
    sections = [invalid_section, target_section]
    if not first:  # Prefix sections with additional valid JUMPF to invalid section
        sections = [Section.Code(Op.JUMPF[1])] + sections

    eof_test(
        data=Container(
            sections=sections,
            validity_error=EOFException.INVALID_NON_RETURNING_FLAG,
        )
    )
