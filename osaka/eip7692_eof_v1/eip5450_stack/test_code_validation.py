"""Code validation of CALLF, JUMPF, RETF opcodes in conjunction with static relative jumps."""

import itertools
from enum import Enum, auto, unique
from typing import Tuple

import pytest

from ethereum_test_exceptions.exceptions import EOFException
from ethereum_test_tools import Account, EOFStateTestFiller, EOFTestFiller
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_types.eof.v1 import Container, Section
from ethereum_test_types.eof.v1.constants import MAX_STACK_INCREASE_LIMIT, NON_RETURNING_SECTION
from ethereum_test_vm.bytecode import Bytecode

from .. import EOF_FORK_NAME
from ..eip3540_eof_v1.test_all_opcodes_in_container import valid_eof_opcodes
from ..eip7620_eof_create.helpers import (
    smallest_initcode_subcontainer,
    smallest_runtime_subcontainer,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-5450.md"
REFERENCE_SPEC_VERSION = "f20b164b00ae5553f7536a6d7a83a0f254455e09"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


@unique
class RjumpKind(Enum):
    """Kinds of RJUMP* instruction snippets to generate."""

    EMPTY_RJUMP = auto()
    EMPTY_RJUMPI = auto()
    RJUMPI_OVER_PUSH = auto()
    RJUMPI_OVER_NOOP = auto()
    RJUMPI_OVER_STOP = auto()
    RJUMPI_OVER_PUSH_POP = auto()
    RJUMPI_OVER_POP = auto()
    RJUMPI_OVER_NEXT = auto()
    RJUMPI_OVER_NEXT_NESTED = auto()
    RJUMPI_TO_START = auto()
    RJUMPV_EMPTY_AND_OVER_NEXT = auto()
    RJUMPV_OVER_PUSH_AND_TO_START = auto()
    RJUMPI_OVER_RETF = auto()

    def __str__(self) -> str:
        """Return string representation of the enum."""
        return f"{self.name}"


@unique
class RjumpSpot(Enum):
    """Possible spots in the code section layout where the RJUMP* is injected."""

    BEGINNING = auto()
    BEFORE_TERMINATION = auto()

    def __str__(self) -> str:
        """Return string representation of the enum."""
        return f"{self.name}"


def rjump_code_with(
    rjump_kind: RjumpKind | None, code_so_far_len: int, next_code: Bytecode
) -> Tuple[Bytecode, bool, bool, bool]:
    """
    Unless `rjump_kind` is None generates a code snippet with an RJUMP* instruction.
    For some kinds `code_so_far_len` must be code length in bytes preceeding the snippet.
    For some kinds `next_code_len` must be code length in bytes of some code which follows.

    It is expected that the snippet and the jump target are valid, but the resulting code
    or its stack balance might not.

    Also returns some traits of the snippet: `is_backwards`, `pops` and `pushes`
    """
    body = Bytecode()

    is_backwards = False
    pops = False
    pushes = False
    jumps_over_next = False

    if rjump_kind == RjumpKind.EMPTY_RJUMP:
        body = Op.RJUMP[0]
    elif rjump_kind == RjumpKind.EMPTY_RJUMPI:
        body = Op.RJUMPI[0](0)
    elif rjump_kind == RjumpKind.RJUMPI_OVER_PUSH:
        body = Op.RJUMPI[1](0) + Op.PUSH0
        pushes = True
    elif rjump_kind == RjumpKind.RJUMPI_OVER_NOOP:
        body = Op.RJUMPI[1](0) + Op.NOOP
    elif rjump_kind == RjumpKind.RJUMPI_OVER_STOP:
        body = Op.RJUMPI[1](0) + Op.STOP
    elif rjump_kind == RjumpKind.RJUMPI_OVER_PUSH_POP:
        body = Op.RJUMPI[2](0) + Op.PUSH0 + Op.POP
    elif rjump_kind == RjumpKind.RJUMPI_OVER_POP:
        body = Op.RJUMPI[1](0) + Op.POP
        pops = True
    elif rjump_kind == RjumpKind.RJUMPI_OVER_NEXT:
        body = Op.RJUMPI[len(next_code)](0)
        jumps_over_next = True
    elif rjump_kind == RjumpKind.RJUMPI_OVER_NEXT_NESTED:
        rjump_inner = Op.RJUMPI[len(next_code)](0)
        body = Op.RJUMPI[len(rjump_inner)](0) + rjump_inner
        jumps_over_next = True
    elif rjump_kind == RjumpKind.RJUMPI_TO_START:
        rjumpi_len = len(Op.RJUMPI[0](0))
        body = Op.RJUMPI[-code_so_far_len - rjumpi_len](0)
        is_backwards = True
    elif rjump_kind == RjumpKind.RJUMPV_EMPTY_AND_OVER_NEXT:
        body = Op.RJUMPV[[0, len(next_code)]](0)
        jumps_over_next = True
    elif rjump_kind == RjumpKind.RJUMPV_OVER_PUSH_AND_TO_START:
        rjumpv_two_destinations_len = len(Op.RJUMPV[[0, 0]](0))
        body = Op.RJUMPV[[1, -code_so_far_len - rjumpv_two_destinations_len]](0) + Op.PUSH0
        is_backwards = True
        pushes = True
    elif rjump_kind == RjumpKind.RJUMPI_OVER_RETF:
        body = Op.RJUMPI[1](0) + Op.RETF
    elif not rjump_kind:
        pass
    else:
        raise TypeError("unknown rjumps value" + str(rjump_kind))

    if jumps_over_next:
        # This is against intuition, but if the code we're jumping over pushes, the path
        # which misses it will be short of stack items, as if the RJUMP* popped and vice versa.
        if next_code.pushed_stack_items > next_code.popped_stack_items:
            pops = True
        elif next_code.popped_stack_items > next_code.pushed_stack_items:
            pushes = True

    return body, is_backwards, pops, pushes


def call_code_with(inputs, outputs, call: Bytecode) -> Bytecode:
    """
    Generate code snippet with the `call` bytecode provided and its respective input/output
    management.

    `inputs` and `outputs` are understood as those of the code section we're generating for.
    """
    body = Bytecode()

    if call.popped_stack_items > inputs:
        body += Op.PUSH0 * (call.popped_stack_items - inputs)
    elif call.popped_stack_items < inputs:
        body += Op.POP * (inputs - call.popped_stack_items)

    body += call
    if call.pushed_stack_items < outputs:
        body += Op.PUSH0 * (outputs - call.pushed_stack_items)
    elif call.pushed_stack_items > outputs:
        body += Op.POP * (call.pushed_stack_items - outputs)

    return body


def section_code_with(
    inputs: int,
    outputs: int,
    rjump_kind: RjumpKind | None,
    rjump_spot: RjumpSpot,
    call: Bytecode | None,
    termination: Bytecode,
) -> Tuple[Bytecode, bool, bool, bool, bool]:
    """
    Generate code section with RJUMP* and CALLF/RETF instructions.

    Also returns some traits of the section: `has_invalid_back_jump`, `rjump_snippet_pops`,
    `rjump_snippet_pushes`, `rjump_falls_off_code`
    """
    code = Bytecode()
    code.pushed_stack_items, code.max_stack_height = (inputs, inputs)

    if call:
        body = call_code_with(inputs, outputs, call)
    else:
        body = Op.POP * inputs + Op.PUSH0 * outputs

    has_invalid_back_jump = False
    rjump_snippet_pushes = False
    rjump_snippet_pops = False
    rjump_falls_off_code = False

    if rjump_spot == RjumpSpot.BEGINNING:
        rjump, is_backwards, rjump_snippet_pops, rjump_snippet_pushes = rjump_code_with(
            rjump_kind, 0, body
        )
        if rjump_kind == RjumpKind.RJUMPI_OVER_RETF:
            if inputs > outputs:
                rjump_snippet_pushes = True
            elif outputs > inputs:
                rjump_snippet_pops = True
        code += rjump

    code += body

    if rjump_spot == RjumpSpot.BEFORE_TERMINATION:
        rjump, is_backwards, rjump_snippet_pops, rjump_snippet_pushes = rjump_code_with(
            rjump_kind, len(code), next_code=termination
        )
        code += rjump

        if is_backwards and inputs != outputs:
            has_invalid_back_jump = True

    if rjump_spot == RjumpSpot.BEFORE_TERMINATION or (
        rjump_spot == RjumpSpot.BEGINNING and len(termination) == 0
    ):
        if rjump_kind in [
            RjumpKind.RJUMPI_OVER_NEXT,
            RjumpKind.RJUMPI_OVER_NEXT_NESTED,
            RjumpKind.RJUMPV_EMPTY_AND_OVER_NEXT,
        ]:
            # Jump over termination or jump over body, but there is nothing after the body.
            rjump_falls_off_code = True

    code += termination

    return (
        code,
        has_invalid_back_jump,
        rjump_snippet_pops,
        rjump_snippet_pushes,
        rjump_falls_off_code,
    )


num_sections = 3
possible_inputs_outputs = range(2)


@pytest.mark.parametrize(
    ["inputs", "outputs"],
    itertools.product(
        list(itertools.product(*([possible_inputs_outputs] * (num_sections - 1)))),
        list(itertools.product(*([possible_inputs_outputs] * (num_sections - 1)))),
    ),
)
@pytest.mark.parametrize(
    "rjump_kind",
    RjumpKind,
)
# Parameter value fixed for first iteration, to cover the most important case.
@pytest.mark.parametrize("rjump_section_idx", [0, 1])
@pytest.mark.parametrize(
    "rjump_spot",
    RjumpSpot,
)
def test_rjumps_callf_retf(
    eof_test: EOFTestFiller,
    inputs: Tuple[int, ...],
    outputs: Tuple[int, ...],
    rjump_kind: RjumpKind,
    rjump_section_idx: int,
    rjump_spot: RjumpSpot,
):
    """
    Test EOF container validaiton for EIP-4200 vs EIP-4750 interactions.

    Each test's code consists of `num_sections` code sections, which call into one another
    and then return. Code may include RJUMP* snippets of `rjump_kind` in various `rjump_spots`.
    """
    # Zeroth section has always 0 inputs and 0 outputs, so is excluded from param
    inputs = (0,) + inputs
    outputs = (0,) + outputs

    assert len(inputs) == len(outputs) == num_sections

    sections = []
    container_has_invalid_back_jump = False
    container_has_rjump_pops = False
    container_has_rjump_pushes = False
    container_has_rjump_off_code = False
    container_has_section_0_retf = (
        rjump_section_idx == 0 and rjump_kind == RjumpKind.RJUMPI_OVER_RETF
    )

    for section_idx in range(num_sections):
        if section_idx == 0:
            call = Op.CALLF[section_idx + 1]
            call.popped_stack_items = inputs[section_idx + 1]
            call.pushed_stack_items = outputs[section_idx + 1]
            call.min_stack_height = call.popped_stack_items
            call.max_stack_height = max(call.popped_stack_items, call.pushed_stack_items)
            termination = Op.STOP
        elif section_idx < num_sections - 1:
            call = Op.CALLF[section_idx + 1]
            call.popped_stack_items = inputs[section_idx + 1]
            call.pushed_stack_items = outputs[section_idx + 1]
            call.min_stack_height = call.popped_stack_items
            call.max_stack_height = max(call.popped_stack_items, call.pushed_stack_items)
            termination = Op.RETF
        else:
            call = None
            termination = Op.RETF

        (
            code,
            section_has_invalid_back_jump,
            rjump_snippet_pops,
            rjump_snippet_pushes,
            rjump_falls_off_code,
        ) = section_code_with(
            inputs[section_idx],
            outputs[section_idx],
            rjump_kind if rjump_section_idx == section_idx else None,
            rjump_spot,
            call,
            termination,
        )

        if section_has_invalid_back_jump:
            container_has_invalid_back_jump = True
        if rjump_snippet_pops:
            container_has_rjump_pops = True
        # Pushes to the stack never affect the zeroth section, because it `STOP`s and not `RETF`s.
        if rjump_snippet_pushes and section_idx != 0:
            container_has_rjump_pushes = True
        if rjump_falls_off_code:
            container_has_rjump_off_code = True

        if section_idx > 0:
            sections.append(
                Section.Code(
                    code,
                    code_inputs=inputs[section_idx],
                    code_outputs=outputs[section_idx],
                )
            )
        else:
            sections.append(Section.Code(code))

    possible_exceptions = []
    if container_has_invalid_back_jump:
        possible_exceptions.append(EOFException.STACK_HEIGHT_MISMATCH)
    if container_has_rjump_pops:
        possible_exceptions.append(EOFException.STACK_UNDERFLOW)
    if container_has_rjump_pushes:
        possible_exceptions.append(EOFException.STACK_HIGHER_THAN_OUTPUTS)
    if container_has_rjump_off_code:
        possible_exceptions.append(EOFException.INVALID_RJUMP_DESTINATION)
    if container_has_section_0_retf:
        possible_exceptions.append(EOFException.INVALID_NON_RETURNING_FLAG)

    eof_test(container=Container(sections=sections), expect_exception=possible_exceptions or None)


@pytest.mark.parametrize(
    "inputs", itertools.product(*([possible_inputs_outputs] * (num_sections - 1)))
)
@pytest.mark.parametrize(
    "rjump_kind",
    RjumpKind,
)
# Parameter value fixed for first iteration, to cover the most important case.
@pytest.mark.parametrize("rjump_section_idx", [0, 1])
@pytest.mark.parametrize(
    "rjump_spot",
    # `termination` is empty for JUMPF codes, because JUMPF serves as one. Spot
    # `BEFORE_TERMINATION` is unreachable code.
    [k for k in RjumpSpot if k not in [RjumpSpot.BEFORE_TERMINATION]],
)
def test_rjumps_jumpf_nonreturning(
    eof_test: EOFTestFiller,
    inputs: Tuple[int, ...],
    rjump_kind: RjumpKind,
    rjump_section_idx: int,
    rjump_spot: RjumpSpot,
):
    """
    Test EOF container validaiton for EIP-4200 vs EIP-6206 interactions on non-returning
    functions.
    """
    # Zeroth section has always 0 inputs and 0 outputs, so is excluded from param
    inputs = (0,) + inputs

    sections = []
    container_has_rjump_pops = False
    container_has_rjump_off_code = False
    container_has_non_returning_retf = False

    for section_idx in range(num_sections):
        if section_idx < num_sections - 1:
            call = Op.JUMPF[section_idx + 1]
            call.popped_stack_items = inputs[section_idx + 1]
            call.pushed_stack_items = 0
            call.min_stack_height = call.popped_stack_items
            call.max_stack_height = max(call.popped_stack_items, call.pushed_stack_items)
            termination = Bytecode()
        else:
            call = None
            termination = Op.STOP

        # `section_has_invalid_back_jump` - never happens: we excluded RJUMP from the end
        # `rjump_snippet_pushes` - never happens: we never RETF where too large stack would fail
        (
            code,
            _section_has_invalid_back_jump,
            rjump_snippet_pops,
            _rjump_snippet_pushes,
            rjump_falls_off_code,
        ) = section_code_with(
            inputs[section_idx],
            0,
            rjump_kind if rjump_section_idx == section_idx else None,
            rjump_spot,
            call,
            termination,
        )

        if rjump_snippet_pops:
            container_has_rjump_pops = True
        if rjump_falls_off_code:
            container_has_rjump_off_code = True
        if rjump_kind == RjumpKind.RJUMPI_OVER_RETF:
            container_has_non_returning_retf = True

        if section_idx > 0:
            sections.append(
                Section.Code(
                    code,
                    code_inputs=inputs[section_idx],
                    code_outputs=NON_RETURNING_SECTION,
                )
            )
        else:
            sections.append(Section.Code(code))

    possible_exceptions = []
    if container_has_rjump_pops:
        possible_exceptions.append(EOFException.STACK_UNDERFLOW)
    if container_has_rjump_off_code:
        possible_exceptions.append(EOFException.INVALID_RJUMP_DESTINATION)
    if container_has_non_returning_retf:
        possible_exceptions.append(EOFException.INVALID_NON_RETURNING_FLAG)

    eof_test(container=Container(sections=sections), expect_exception=possible_exceptions or None)


def gen_stack_underflow_params():
    """Generate parameters for stack underflow tests."""
    opcodes = sorted(op for op in valid_eof_opcodes if op.min_stack_height > 0) + [
        # Opcodes that have variable min_stack_height
        Op.SWAPN[0x00],
        Op.SWAPN[0xFF],
        Op.DUPN[0x00],
        Op.DUPN[0xFF],
        Op.EXCHANGE[0x00],
        Op.EXCHANGE[0xFF],
    ]
    for op in opcodes:
        yield op, 0
        if op.min_stack_height > 1:
            yield op, op.min_stack_height - 1


@pytest.mark.parametrize("spread", [-1, 0, 1, MAX_STACK_INCREASE_LIMIT])
@pytest.mark.parametrize("op,stack_height", gen_stack_underflow_params())
def test_all_opcodes_stack_underflow(
    eof_test: EOFTestFiller, op: Op, stack_height: int, spread: int
):
    """
    Test EOF validation failing due to stack overflow
    caused by the specific instruction `op`.
    """
    code = Bytecode()

    if spread >= 0:
        # Check if the op increases the stack height (e.g. DUP instructions).
        # We need to leave space for this increase not to cause stack overflow.
        max_stack_increase = max(op.pushed_stack_items - op.popped_stack_items, 0)
        # Cap the spread if it would exceed the maximum stack height.
        spread = min(spread, MAX_STACK_INCREASE_LIMIT - (stack_height + max_stack_increase))
        # Create a range stack height of 0-spread.
        code += Op.RJUMPI[spread](Op.CALLVALUE) + Op.PUSH0 * spread

    # Create the desired stack height.
    code += Op.PUSH0 * stack_height

    if op.has_data_portion():
        code += op[0]  # produce required imm bytes
    else:
        code += op

    if not op.terminating:
        code += Op.STOP

    sections = [
        Section.Code(
            code,
            # Set reasonable stack height. Don't rely on automatic calculation,
            # because we are in the invalid stack height scenario.
            max_stack_height=max(spread, stack_height, int(spread >= 0)),
        )
    ]

    if op == Op.EOFCREATE:
        # Make EOFCREATE valid by adding the target subcontainer.
        sections.append(Section.Container(smallest_initcode_subcontainer))
    elif op == Op.RETURNCODE:
        # Make RETURNCODE valid by wrapping it with a container with EOFCREATE.
        sections = [
            Section.Code(Op.EOFCREATE[0](0, 0, 0, 0) + Op.STOP),
            Section.Container(
                container=Container(
                    sections=[
                        sections[0],
                        Section.Container(smallest_runtime_subcontainer),
                    ]
                )
            ),
        ]

    eof_test(
        container=Container(
            sections=sections,
            validity_error=EOFException.STACK_UNDERFLOW,
        )
    )


@pytest.mark.parametrize(
    "container",
    [
        Container(
            name="underflow_0",
            sections=[
                Section.Code(
                    code=Op.ADD + Op.STOP,
                    max_stack_height=1,
                ),
            ],
        ),
        Container(
            name="underflow_variable_stack_0",
            sections=[
                Section.Code(
                    code=Op.PUSH0 + Op.RJUMPI[2](0) + Op.PUSH0 + Op.PUSH0 + Op.LOG2 + Op.STOP,
                    max_stack_height=3,
                ),
            ],
        ),
        Container(
            name="underflow_variable_stack_1",
            sections=[
                Section.Code(
                    code=Op.PUSH0 + Op.RJUMPI[2](0) + Op.PUSH0 + Op.PUSH0 + Op.ADD + Op.STOP,
                    max_stack_height=3,
                ),
            ],
        ),
        Container(
            name="underflow_variable_stack_2",
            sections=[
                Section.Code(
                    code=Op.PUSH0 * 2 + Op.RJUMPI[1](0) + Op.POP + Op.ADD + Op.STOP,
                    max_stack_height=3,
                ),
            ],
        ),
        Container(
            name="underflow_variable_stack_3",
            sections=[
                Section.Code(
                    Op.RJUMPI[8](0)
                    + Op.PUSH0 * 2
                    + Op.RJUMPI[1](0)
                    + Op.POP * 2
                    + Op.PUSH0 * 2
                    + Op.REVERT,
                    max_stack_height=3,
                ),
            ],
        ),
    ],
    ids=lambda x: x.name,
)
def test_stack_underflow_examples(eof_test, container):
    """Test EOF validation failing due to stack underflow at basic instructions."""
    eof_test(container=container, expect_exception=EOFException.STACK_UNDERFLOW)


@pytest.mark.parametrize("initial_stack", [0, 1, 2])
@pytest.mark.parametrize("calldata_1", [0, 1])
@pytest.mark.parametrize("calldata_2", [0, 1])
def test_valid_non_constant_stack_examples(
    eof_state_test: EOFStateTestFiller, initial_stack: int, calldata_1: int, calldata_2: int
):
    """Test valid containers with non constant stack items."""
    # Stores the number of added items to the stack in storage slot 0
    # calldata_1 == 1: number of items = 2
    # calldata_1 == 0:
    #   calldata_2 == 0: number of items: 3
    #   calldata_2 == 1: number of items: 4
    expected_storage = {0: 2} if calldata_1 == 1 else ({0: 3} if calldata_2 == 0 else {0: 4})
    data = calldata_1.to_bytes(32, "big") + calldata_2.to_bytes(32, "big")
    container = Container(
        sections=[
            Section.Code(
                code=Op.PUSH0 * initial_stack
                + Op.CALLDATALOAD(0)
                + Op.RJUMPI[19]
                + Op.PUSH0 * 2
                + Op.SSTORE(0, 2)  # Stores added items (2)
                + Op.CALLDATALOAD(32)
                + Op.RJUMPI[6]
                + Op.POP
                + Op.SSTORE(0, 1)  # Updates number of added items to 1
                + Op.PUSH0 * 2  # <-- RJUMPI[19]/RJUMPI[6] target
                + Op.SLOAD(0)
                + Op.PUSH1(2)
                + Op.ADD  # Add latest added items (+2)
                + Op.PUSH1(0)
                + Op.SSTORE
                + Op.STOP,
                max_stack_height=6 + initial_stack,
            ),
        ],
    )
    eof_state_test(
        container=container,
        expect_exception=None,
        data=data,
        container_post=Account(storage=expected_storage),
    )
