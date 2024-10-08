"""
EOF JUMPF tests covering JUMPF target rules.
"""

import pytest

from ethereum_test_tools import Account, EOFException, EOFStateTestFiller
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.eof.v1.constants import NON_RETURNING_SECTION
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME
from .helpers import slot_code_worked, value_code_worked

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-6206.md"
REFERENCE_SPEC_VERSION = "2f365ea0cd58faa6e26013ea77ce6d538175f7d0"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


@pytest.mark.parametrize(
    "target_outputs",
    [NON_RETURNING_SECTION, 0, 2, 4, 127],
    ids=lambda x: "to-%s" % ("N" if x == NON_RETURNING_SECTION else x),
)
@pytest.mark.parametrize(
    "source_outputs",
    [NON_RETURNING_SECTION, 0, 2, 4, 127],
    ids=lambda x: "so-%s" % ("N" if x == NON_RETURNING_SECTION else x),
)
def test_jumpf_target_rules(
    eof_state_test: EOFStateTestFiller,
    source_outputs: int,
    target_outputs: int,
):
    """
    Validate the target section rules of JUMPF, and execute valid cases.
    We are not testing stack so a lot of the logic is to get correct stack values.
    """
    source_non_returning = source_outputs == NON_RETURNING_SECTION
    source_height = 0 if source_non_returning else source_outputs
    source_section_index = 1

    target_non_returning = target_outputs == NON_RETURNING_SECTION
    target_height = 0 if target_non_returning else target_outputs
    target_section_index = 2

    # Because we are testing the target and not the stack height validation we need to do some work
    # to make sure the stack passes validation.

    # `source_extra_push` is how many more pushes we need to match our stack commitments
    source_extra_push = max(0, source_height - target_height)
    source_section = Section.Code(
        code=Op.PUSH0 * (source_height)
        + Op.CALLDATALOAD(0)
        + Op.RJUMPI[1]
        + (Op.STOP if source_non_returning else Op.RETF)
        + Op.PUSH0 * source_extra_push
        + Op.JUMPF[target_section_index],
        code_inputs=0,
        code_outputs=source_outputs,
        max_stack_height=source_height + max(1, source_extra_push),
    )

    # `delta` is how many stack items the target output is from the input height, and tracks the
    # number of pushes or (if negative) pops the target needs to do to match output commitments
    delta = 0 if target_non_returning or source_non_returning else target_outputs - source_height
    target_section = Section.Code(
        code=((Op.PUSH0 * delta) if delta >= 0 else (Op.POP * -delta))
        + Op.CALLF[3]
        + (Op.STOP if target_non_returning else Op.RETF),
        code_inputs=source_height,
        code_outputs=target_outputs,
        max_stack_height=max(source_height, source_height + delta),
    )

    base_code = (
        Op.JUMPF[source_section_index]
        if source_non_returning
        else (Op.CALLF[source_section_index](0, 0) + Op.STOP)
    )
    base_height = 0 if source_non_returning else 2 + source_outputs
    container = Container(
        name="so-%s_to-%s"
        % (
            "N" if source_non_returning else source_outputs,
            "N" if target_non_returning else target_outputs,
        ),
        sections=[
            Section.Code(
                code=base_code,
                max_stack_height=base_height,
            ),
            source_section,
            target_section,
            Section.Code(
                code=Op.SSTORE(slot_code_worked, value_code_worked) + Op.RETF,
                code_outputs=0,
            ),
        ],
    )
    if target_non_returning or source_non_returning:
        if not target_non_returning and source_non_returning:
            # both as non-returning handled above
            container.validity_error = EOFException.INVALID_NON_RETURNING_FLAG
    elif source_outputs < target_outputs:
        container.validity_error = EOFException.JUMPF_DESTINATION_INCOMPATIBLE_OUTPUTS

    eof_state_test(
        data=container,
        container_post=Account(storage={slot_code_worked: value_code_worked}),
        tx_data=b"\1",
    )


@pytest.mark.skip("Not implemented")
def test_jumpf_multi_target_rules(
    eof_state_test: EOFStateTestFiller,
):
    """
    NOT IMPLEMENTED:
    Test a section that contains multiple JUMPF to different targets with different outputs.
    """
    pass
