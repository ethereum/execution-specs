"""
EOF Subcontainer tests covering simple cases.
"""
import pytest

from ethereum_test_tools import Account, EOFException, EOFStateTestFiller, EOFTestFiller
from ethereum_test_tools.eof.v1 import Container, ContainerKind, Section
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME
from .helpers import slot_code_worked, value_code_worked

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7620.md"
REFERENCE_SPEC_VERSION = "52ddbcdddcf72dd72427c319f2beddeb468e1737"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)

eofcreate_code_section = Section.Code(
    code=Op.EOFCREATE[0](0, 0, 0, 0) + Op.SSTORE(slot_code_worked, value_code_worked) + Op.STOP,
    max_stack_height=4,
)
returncontract_code_section = Section.Code(
    code=Op.SSTORE(slot_code_worked, value_code_worked) + Op.RETURNCONTRACT[0](0, 0),
    max_stack_height=2,
)
stop_sub_container = Section.Container(container=Container(sections=[Section.Code(code=Op.STOP)]))
return_sub_container = Section.Container(
    container=Container(sections=[Section.Code(code=Op.RETURN(0, 0), max_stack_height=2)])
)
revert_sub_container = Section.Container(
    container=Container(sections=[Section.Code(code=Op.REVERT(0, 0), max_stack_height=2)])
)
returncontract_sub_container = Section.Container(
    container=Container(
        sections=[
            Section.Code(
                code=Op.RETURNCONTRACT[0](0, 0),
                max_stack_height=2,
            ),
            stop_sub_container,
        ],
    )
)


def test_simple_create_from_deployed(
    eof_state_test: EOFStateTestFiller,
):
    """Simple EOF creation from a deployed EOF container"""
    eof_state_test(
        data=Container(
            sections=[
                eofcreate_code_section,
                returncontract_sub_container,
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_simple_create_from_creation(
    eof_state_test: EOFStateTestFiller,
):
    """Simple EOF creation from a create transaction container"""
    eof_state_test(
        data=Container(
            sections=[
                returncontract_code_section,
                stop_sub_container,
            ],
            kind=ContainerKind.INITCODE,
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


@pytest.mark.parametrize(
    "zero_section",
    [eofcreate_code_section, returncontract_code_section],
    ids=["eofcreate", "returncontract"],
)
def test_reverting_container(
    eof_state_test: EOFStateTestFiller,
    zero_section: Container,
):
    """Test revert containers"""
    eof_state_test(
        data=Container(
            sections=[
                zero_section,
                revert_sub_container,
            ],
            kind=ContainerKind.INITCODE
            if zero_section == returncontract_code_section
            else ContainerKind.RUNTIME,
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


@pytest.mark.parametrize(
    "code_section,first_sub_container,container_kind",
    [
        (eofcreate_code_section, returncontract_sub_container, ContainerKind.RUNTIME),
        (returncontract_code_section, stop_sub_container, ContainerKind.INITCODE),
    ],
    ids=["eofcreate", "returncontract"],
)
@pytest.mark.parametrize(
    "extra_sub_container",
    [stop_sub_container, revert_sub_container, returncontract_sub_container],
    ids=["stop", "revert", "returncontract"],
)
def test_orphan_container(
    eof_test: EOFTestFiller,
    code_section: Section,
    first_sub_container: Container,
    extra_sub_container: Container,
    container_kind: ContainerKind,
):
    """Test orphaned containers"""
    eof_test(
        data=Container(
            sections=[
                code_section,
                first_sub_container,
                extra_sub_container,
            ],
            kind=container_kind,
        ),
        expect_exception=EOFException.ORPHAN_SUBCONTAINER,
    )


@pytest.mark.parametrize(
    "code_section,sub_container,container_kind",
    [
        pytest.param(
            eofcreate_code_section,
            returncontract_sub_container,
            ContainerKind.RUNTIME,
            id="EOFCREATE/RETURNCONTRACT",
        ),
        pytest.param(
            returncontract_code_section,
            stop_sub_container,
            ContainerKind.INITCODE,
            id="RETURNCONTRACT/STOP",
        ),
        pytest.param(
            returncontract_code_section,
            return_sub_container,
            ContainerKind.INITCODE,
            id="RETURNCONTRACT/RETURN",
        ),
        pytest.param(
            eofcreate_code_section,
            revert_sub_container,
            ContainerKind.RUNTIME,
            id="EOFCREATE/REVERT",
        ),
        pytest.param(
            returncontract_code_section,
            revert_sub_container,
            ContainerKind.INITCODE,
            id="RETURNCONTRACT/REVERT",
        ),
    ],
)
def test_container_combos_valid(
    eof_state_test: EOFStateTestFiller,
    code_section: Section,
    sub_container: Container,
    container_kind: ContainerKind,
):
    """Test valid subcontainer reference / opcode combos"""
    eof_state_test(
        data=Container(
            sections=[
                code_section,
                sub_container,
            ],
            kind=container_kind,
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


@pytest.mark.parametrize(
    "code_section,first_sub_container,error",
    [
        pytest.param(
            eofcreate_code_section,
            stop_sub_container,
            EOFException.UNDEFINED_EXCEPTION,
            id="EOFCREATE/STOP",
        ),
        pytest.param(
            eofcreate_code_section,
            return_sub_container,
            EOFException.UNDEFINED_EXCEPTION,
            id="EOFCREATE/RETURN",
        ),
        pytest.param(
            returncontract_code_section,
            returncontract_sub_container,
            EOFException.UNDEFINED_EXCEPTION,
            id="RETURNCONTRACT/RETURNCONTRACT",
        ),
    ],
)
def test_container_combos_invalid(
    eof_test: EOFTestFiller,
    code_section: Section,
    first_sub_container: Container,
    error: EOFException,
):
    """Test invalid subcontainer reference / opcode combos"""
    eof_test(
        data=Container(
            sections=[
                code_section,
                first_sub_container,
            ],
        ),
        expect_exception=error,
    )


def test_container_both_kinds_same_sub(eof_test: EOFTestFiller):
    """Test subcontainer conflicts (both EOFCREATE and RETURNCONTRACT Reference)"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.EOFCREATE[0](0, 0, 0, 0) + Op.JUMPF[1],
                ),
                Section.Code(
                    code=Op.RETURNCONTRACT[0](0, 0),
                ),
                revert_sub_container,
            ],
        ),
        expect_exception=EOFException.UNDEFINED_EXCEPTION,
    )


def test_container_both_kinds_different_sub(eof_test: EOFTestFiller):
    """Test multiple kinds of subcontainer at the same level"""
    eof_test(
        data=Container(
            sections=[
                Section.Code(
                    code=Op.EOFCREATE[0](0, 0, 0, 0) + Op.JUMPF[1],
                ),
                Section.Code(
                    code=Op.RETURNCONTRACT[1](0, 0),
                ),
                returncontract_sub_container,
                stop_sub_container,
            ],
            kind=ContainerKind.INITCODE,
        ),
    )
