"""
EOF v1 code validation tests
"""

from typing import List

from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.eof.v1.constants import MAX_BYTECODE_SIZE, MAX_OPERAND_STACK_HEIGHT
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .opcodes import (
    INVALID_OPCODES,
    INVALID_TERMINATING_OPCODES,
    V1_EOF_DEPRECATED_OPCODES,
    V1_EOF_OPCODES,
    VALID_TERMINATING_OPCODES,
)

VALID: List[Container] = []
INVALID: List[Container] = []


def make_valid_stack_opcode(op: Op) -> bytes:
    """
    Builds bytecode with the specified op at the end and the proper number of
    stack items to not underflow.
    """
    out = bytes()
    # We need to push some items onto the stack so the code is valid
    # even with stack validation
    out += Op.ORIGIN * op.min_stack_height
    out += op
    return out


# Create containers where each valid terminating opcode is at the end of the
# bytecode.
for op in VALID_TERMINATING_OPCODES:
    opcode_name = op._name_.lower()
    # Valid terminating opcode at the end of the section
    VALID.append(
        Container(
            name=f"valid_terminating_opcode_{opcode_name}",
            sections=[
                Section.Code(
                    code=make_valid_stack_opcode(op),
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=op.min_stack_height,
                ),
            ],
        ),
    )
    # Two valid terminating opcodes in sequence
    # resulting in unreachable code
    INVALID.append(
        Container(
            name=f"unreachable_code_after_opcode_{opcode_name}",
            sections=[
                Section.Code(
                    code=make_valid_stack_opcode(op) + Op.STOP,
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=op.min_stack_height,
                ),
            ],
            validity_error="UnreachableCode",
        ),
    )

# Create containers where each valid non-terminating opcodes is used somewhere
# in the code, with also a valid terminating opcode at the end (STOP).
for op in V1_EOF_OPCODES:
    if op not in VALID_TERMINATING_OPCODES and op != Op.RJUMPV:
        opcode_name = op._name_.lower()
        max_stack_height = max(
            op.min_stack_height,
            op.min_stack_height - op.popped_stack_items + op.pushed_stack_items,
        )
        VALID.append(
            Container(
                name=f"valid_opcode_{opcode_name}",
                sections=[
                    Section.Code(
                        code=make_valid_stack_opcode(op)
                        + bytes([0x00]) * op.data_portion_length
                        + Op.STOP,
                        code_inputs=0,
                        code_outputs=0,
                        max_stack_height=max_stack_height,
                    ),
                ],
            ),
        )

# Create containers where each invalid terminating opcode is located at the
# end of the bytecode.
for op in INVALID_TERMINATING_OPCODES:
    opcode_name = op._name_.lower()
    max_stack_height = max(
        op.min_stack_height,
        op.min_stack_height - op.popped_stack_items + op.pushed_stack_items,
    )
    INVALID.append(
        Container(
            name=f"invalid_terminating_opcode_{opcode_name}",
            sections=[
                Section.Code(
                    code=make_valid_stack_opcode(op),
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=max_stack_height,
                ),
            ],
            validity_error="InvalidTerminatingOpcode",
        ),
    )

# Create containers containing a valid terminating opcode, but a
# invalid opcode somewhere in the bytecode.
for invalid_op_byte in INVALID_OPCODES:
    INVALID.append(
        Container(
            name=f"invalid_opcode_0x{invalid_op_byte.hex()}",
            sections=[
                Section.Code(
                    code=invalid_op_byte + Op.STOP,
                ),
            ],
            validity_error="UndefinedInstruction",
        ),
    )

# Create containers containing a valid terminating opcode, but a
# deprecated opcode somewhere in the bytecode.
# We need to add the proper stack items so the stack validation does not
# produce a false positive.
for op in V1_EOF_DEPRECATED_OPCODES:
    opcode_name = op._name_.lower()
    max_stack_height = max(
        op.min_stack_height,
        op.min_stack_height - op.popped_stack_items + op.pushed_stack_items,
    )
    INVALID.append(
        Container(
            name=f"deprecated_opcode_{opcode_name}",
            sections=[
                Section.Code(
                    code=make_valid_stack_opcode(op) + Op.STOP,
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=max_stack_height,
                ),
            ],
            validity_error="UndefinedInstruction",
        ),
    )

# Create an invalid EOF container where the immediate operand of an opcode is
# truncated or terminates the bytecode.
# Also add required stack items so we are really testing the immediate length
# check.
OPCODES_WITH_IMMEDIATE = [op for op in V1_EOF_OPCODES if op.data_portion_length > 0]
for op in OPCODES_WITH_IMMEDIATE:
    opcode_name = op._name_.lower()
    max_stack_height = max(
        op.min_stack_height,
        op.min_stack_height - op.popped_stack_items + op.pushed_stack_items,
    )
    stack_code = Op.ORIGIN * op.min_stack_height
    # No immediate
    INVALID.append(
        Container(
            name=f"truncated_opcode_{opcode_name}_no_immediate",
            sections=[
                Section.Code(
                    code=stack_code + op,
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=max_stack_height,
                )
            ],
            validity_error="TruncatedImmediate",
        ),
    )
    # Immediate minus one
    if op.data_portion_length > 1:
        INVALID.append(
            Container(
                name=f"truncated_opcode_{opcode_name}_terminating",
                sections=[
                    Section.Code(
                        code=stack_code + op + (Op.STOP * (op.data_portion_length - 1)),
                        code_inputs=0,
                        code_outputs=0,
                        max_stack_height=max_stack_height,
                    )
                ],
                validity_error="TruncatedImmediate",
            ),
        )
    # Single byte as immediate
    if op.data_portion_length > 2:
        INVALID.append(
            Container(
                name=f"truncated_opcode_{opcode_name}_one_byte",
                sections=[
                    Section.Code(
                        code=stack_code + op + Op.STOP,
                        code_inputs=0,
                        code_outputs=0,
                        max_stack_height=max_stack_height,
                    )
                ],
                validity_error="TruncatedImmediate",
            ),
        )


# Check all opcodes that can underflow the stack
OPCODES_WITH_min_stack_height = [op for op in V1_EOF_OPCODES if op.min_stack_height > 0]
for op in OPCODES_WITH_min_stack_height:
    opcode_name = op._name_.lower()
    underflow_stack_opcodes = Op.ORIGIN * (op.min_stack_height - 1)
    # Test using different max stack heights
    for max_stack_height in [
        op.min_stack_height - 1,
        op.min_stack_height,
    ]:
        if op in VALID_TERMINATING_OPCODES:
            INVALID.append(
                Container(
                    name=f"underflow_stack_opcode_{opcode_name}"
                    + f"_max_stack_height_{max_stack_height}",
                    sections=[
                        Section.Code(
                            code=underflow_stack_opcodes + op,
                            code_inputs=0,
                            code_outputs=0,
                            max_stack_height=max_stack_height,
                        )
                    ],
                    validity_error="StackUnderflow",
                ),
            )
        else:
            INVALID.append(
                Container(
                    name=f"underflow_stack_opcode_{opcode_name}"
                    + f"_max_stack_height_{max_stack_height}",
                    sections=[
                        Section.Code(
                            code=underflow_stack_opcodes + op + Op.STOP,
                            code_inputs=0,
                            code_outputs=0,
                            max_stack_height=max_stack_height,
                        )
                    ],
                    validity_error="StackUnderflow",
                ),
            )


def get_stack_overflow_opcode_iteration_count(op: Op) -> int:
    """
    Calculates the number of instances required of an opcode to produce an
    overflow.
    """
    assert op.pushed_stack_items > op.popped_stack_items
    iterations = 0
    stack_height = op.min_stack_height
    while stack_height < (MAX_OPERAND_STACK_HEIGHT + 1):
        stack_height -= op.popped_stack_items
        stack_height += op.pushed_stack_items
        iterations += 1
    return iterations


# Check all opcodes that can overflow the stack
OPCODES_WITH_PUSH_STACK_ITEMS = [
    op for op in V1_EOF_OPCODES if op.pushed_stack_items > op.popped_stack_items
]
for op in OPCODES_WITH_PUSH_STACK_ITEMS:
    opcode_name = op._name_.lower()
    increment_per_iter = op.pushed_stack_items - op.popped_stack_items
    iterations_needed = get_stack_overflow_opcode_iteration_count(op)
    op_data = bytes([0] * op.data_portion_length)

    invalid_container = Container(
        name=f"overflow_stack_opcode_{opcode_name}",
        sections=[
            Section.Code(
                code=(
                    (Op.ORIGIN * op.min_stack_height)
                    + ((op + op_data) * iterations_needed)
                    + Op.STOP
                ),
                code_inputs=0,
                code_outputs=0,
                # We are cheating a bit here
                max_stack_height=MAX_OPERAND_STACK_HEIGHT,
            )
        ],
        validity_error="StackOverflow",
    )

    non_overflowing_stack_height = op.min_stack_height + (
        increment_per_iter * (iterations_needed - 1)
    )
    assert non_overflowing_stack_height <= MAX_OPERAND_STACK_HEIGHT
    valid_container = Container(
        name=f"max_stack_opcode_{opcode_name}",
        sections=[
            Section.Code(
                code=(
                    (Op.ORIGIN * op.min_stack_height)
                    + ((op + op_data) * (iterations_needed - 1))
                    + Op.STOP
                ),
                code_inputs=0,
                code_outputs=0,
                max_stack_height=non_overflowing_stack_height,
            )
        ],
    )

    if len(valid_container) > MAX_BYTECODE_SIZE:
        continue
    VALID.append(valid_container)

    if len(invalid_container) > MAX_BYTECODE_SIZE:
        continue
    INVALID.append(invalid_container)
