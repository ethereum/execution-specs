"""
Ethereum Object Format (EOF)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the Ethereum Object Format (EOF) specification.
"""

from copy import deepcopy
from typing import List, Tuple

from ethereum_types.numeric import Uint, ulen

from .. import MAX_CODE_SIZE
from ..exceptions import InvalidEof
from ..instructions import EOF1_TERMINATING_INSTRUCTIONS, Ops, map_int_to_op
from . import (
    EOF_MAGIC,
    EOF_MAGIC_LENGTH,
    ContainerContext,
    Eof,
    EofVersion,
    OperandStackHeight,
    Validator,
)
from .instructions_check import get_op_validation
from .stack_height_check import get_stack_validation
from .utils import metadata_from_container


def validate_body(validator: Validator) -> None:
    """
    Validate the body of the EOF container.

    Parameters
    ----------
    validator : Validator
        The validator for the EOF container.

    Raises
    ------
    InvalidEof
        If the EOF container is invalid.
    """
    eof_meta = validator.eof.metadata
    for i, type_section in enumerate(eof_meta.type_section_contents):
        num_inputs = type_section[0]
        if num_inputs > 127:
            raise InvalidEof(f"Invalid number of inputs for type {i}")

        num_outputs = type_section[1]
        if num_outputs > 128:
            raise InvalidEof(f"Invalid number of outputs for type {i}")

        max_stack_increase = Uint.from_be_bytes(type_section[2:])
        if max_stack_increase + Uint(num_inputs) > Uint(1023):
            raise InvalidEof(f"Invalid max stack height for type {i}")

        # 4750: Input and output for first section should
        # be 0 and 128 respectively
        if i == 0 and (num_inputs != 0 or num_outputs != 0x80):
            raise InvalidEof("Invalid input/output for first section")


def update_successor_stack_height(validator: Validator) -> None:
    """
    Update the stack height after instruction execution.

    Parameters
    ----------
    validator : `Validator`
        The validator object.
    """
    index = validator.current_index
    section_metadata = validator.sections[index]
    code = validator.eof.metadata.code_section_contents[index]
    op_metadata = section_metadata[validator.current_pc]
    valid_opcode_positions = list(section_metadata.keys())
    current_stack_height = validator.current_stack_height
    assert current_stack_height is not None

    # Update the stack height for Successor instructions
    for relative_offset in op_metadata.relative_offsets:
        if int(op_metadata.pc_post_instruction) + relative_offset < 0:
            raise InvalidEof("Invalid successor or jump destination")

        successor_position = Uint(
            int(op_metadata.pc_post_instruction) + relative_offset
        )
        if (
            successor_position + Uint(1) > ulen(code)
            or successor_position not in valid_opcode_positions
        ):
            raise InvalidEof("Invalid successor or jump destination")

        successor_metadata = section_metadata[successor_position]

        if relative_offset >= 0:
            if successor_metadata.stack_height is None:
                # Visited for the first time
                successor_metadata.stack_height = deepcopy(
                    current_stack_height
                )
            else:
                assert successor_metadata.stack_height is not None
                recorded_stack_height = successor_metadata.stack_height
                recorded_stack_height.min = min(
                    recorded_stack_height.min,
                    current_stack_height.min,
                )
                recorded_stack_height.max = max(
                    recorded_stack_height.max,
                    current_stack_height.max,
                )
        else:
            # Backward jump
            assert successor_metadata.stack_height is not None
            recorded_stack_height = successor_metadata.stack_height
            if recorded_stack_height.min != current_stack_height.min:
                raise InvalidEof("Invalid stack height")
            if recorded_stack_height.max != current_stack_height.max:
                raise InvalidEof("Invalid stack height")


def validate_code_section(validator: Validator) -> None:
    """
    Validate a code section of the EOF container.

    Parameters
    ----------
    validator : Validator
        The validator for the EOF container.

    Raises
    ------
    InvalidEof
        If the code section is invalid.
    """
    while validator.current_pc < ulen(validator.current_code):
        try:
            opcode = map_int_to_op(
                validator.current_code[validator.current_pc], EofVersion.EOF1
            )
        except ValueError:
            raise InvalidEof("Invalid opcode in code section")

        op_validation = get_op_validation(opcode)

        op_validation(validator)

    current_section_metadata = validator.sections[validator.current_index]
    valid_opcode_positions = list(current_section_metadata.keys())
    code_index = validator.current_index
    section_type = validator.eof.metadata.type_section_contents[code_index]
    section_inputs = section_type[0]
    section_outputs = section_type[1]
    section_max_stack_increase = Uint.from_be_bytes(section_type[2:])

    # If the return flag from the section type does not agree with
    # the instructions in the code.
    if (
        section_outputs != 0x80 and not validator.is_current_section_returning
    ) or (section_outputs == 0x80 and validator.is_current_section_returning):
        raise InvalidEof(f"Invalid return flag in section {code_index}")

    computed_maximum_stack_height = 0
    for index, position in enumerate(valid_opcode_positions):
        validator.current_pc = position
        op_metadata = current_section_metadata[position]
        op = op_metadata.opcode

        if index == 0:
            validator.current_stack_height = OperandStackHeight(
                min=section_inputs,
                max=section_inputs,
            )
            op_metadata.stack_height = deepcopy(validator.current_stack_height)
        elif op_metadata.stack_height is not None:
            validator.current_stack_height = deepcopy(op_metadata.stack_height)

        # The section has to end in a terminating instruction
        if index + 1 == len(valid_opcode_positions):
            if op not in EOF1_TERMINATING_INSTRUCTIONS and op != Ops.RJUMP:
                raise InvalidEof("Code section does not terminate")

        if op_metadata.stack_height is None:
            raise InvalidEof("Stack height not set")

        stack_validation = get_stack_validation(op)
        stack_validation(validator)

        update_successor_stack_height(validator)
        if op_metadata.stack_height.max > computed_maximum_stack_height:
            computed_maximum_stack_height = op_metadata.stack_height.max

    if computed_maximum_stack_height > 1023:
        raise InvalidEof("Invalid stack height")

    if computed_maximum_stack_height != section_max_stack_increase + Uint(section_inputs):
        raise InvalidEof("Invalid max stack increase")


def get_reached_code_sections(
    validator: Validator,
    start_index: Uint,
    all_reached_sections: List[Uint],
) -> None:
    """
    Get the reached code sections starting from a given index.

    Parameters
    ----------
    validator : Validator
        The validator for the EOF container.
    start_index : Uint
        The index to start from.
    all_reached_sections : Set[Uint]
        The set of all code sections reached until now.
    """
    sections_called_from_start_index = validator.reached_code_sections[
        start_index
    ]
    all_reached_sections.append(start_index)
    for i in sections_called_from_start_index:
        if i in all_reached_sections:
            continue
        get_reached_code_sections(validator, i, all_reached_sections)


def validate_eof_code(validator: Validator) -> None:
    """
    Validate the code section of the EOF container.

    Parameters
    ----------
    validator : Validator
        The validator for the EOF container.

    Raises
    ------
    InvalidEof
        If the code section is invalid.
    """
    eof_meta = validator.eof.metadata
    validator.referenced_subcontainers = {
        Ops.EOFCREATE: [],
        Ops.RETURNCONTRACT: [],
    }
    for code_index, code in enumerate(eof_meta.code_section_contents):
        validator.reached_code_sections.append(set())
        validator.current_index = Uint(code_index)
        validator.current_code = code
        validator.current_pc = Uint(0)
        validator.is_current_section_returning = False
        validator.sections[validator.current_index] = {}
        validate_code_section(validator)

    all_reached_sections: list[Uint] = [Uint(0)]
    get_reached_code_sections(validator, Uint(0), all_reached_sections)

    for i in range(eof_meta.num_code_sections):
        if i not in all_reached_sections:
            raise InvalidEof(f"Code section {i} not reachable")

    if validator.has_return_contract and (
        validator.has_return or validator.has_stop
    ):
        raise InvalidEof("Container has both RETURNCONTRACT and STOP/RETURN")

    if eof_meta.num_container_sections > Uint(0):
        for index in range(eof_meta.num_container_sections):
            is_eofcreate_target = (
                index in validator.referenced_subcontainers[Ops.EOFCREATE]
            )
            is_returncontract_target = (
                index in validator.referenced_subcontainers[Ops.RETURNCONTRACT]
            )
            if is_eofcreate_target and is_returncontract_target:
                raise InvalidEof(
                    "Container referenced by both EOFCREATE and RETURNCONTRACT"
                )

            if is_eofcreate_target:
                sub_container_context = ContainerContext.INIT
            elif is_returncontract_target:
                sub_container_context = ContainerContext.RETURNCONTRACT_TARGET
            else:
                raise InvalidEof("Container never referenced")

            validate_eof_container(
                eof_meta.container_section_contents[index],
                sub_container_context,
            )


def validate_eof_container(
    container: bytes, context: ContainerContext
) -> Validator:
    """
    Validate the Ethereum Object Format (EOF) container.

    Parameters
    ----------
    container : bytes
        The EOF container to validate.
    context : ContainerContext
        Context of the container.

    Raises
    ------
    InvalidEof
        If the EOF container is invalid.
    """
    # Validate the magic
    if (
        len(container) < EOF_MAGIC_LENGTH
        or container[:EOF_MAGIC_LENGTH] != EOF_MAGIC
    ):
        raise InvalidEof("Invalid magic")

    if len(container) < EOF_MAGIC_LENGTH + 1:
        raise InvalidEof("EOF version not specified")
    elif container[EOF_MAGIC_LENGTH] != 1:
        raise InvalidEof("Invalid EOF version")

    if len(container) > 2 * MAX_CODE_SIZE:
        raise InvalidEof("EOF container size too long")

    metadata = metadata_from_container(
        container,
        validate=True,
        context=context,
    )

    eof = Eof(
        version=EofVersion.EOF1,
        container=container,
        metadata=metadata,
    )

    validator = Validator(
        eof=eof,
        current_index=Uint(0),
        current_code=metadata.code_section_contents[0],
        current_pc=Uint(0),
        is_current_section_returning=False,
        sections={},
        has_return_contract=False,
        has_stop=False,
        has_return=False,
        reached_code_sections=[],
        referenced_subcontainers={Ops.EOFCREATE: [], Ops.RETURNCONTRACT: []},
        current_stack_height=None,
    )

    validate_body(validator)

    validate_eof_code(validator)

    return validator


def parse_create_tx_call_data(data: bytes) -> Tuple[Eof, bytes]:
    """
    Parse the data for a create transaction.

    Parameters
    ----------
    data : bytes
        The data for the create call.

    Returns
    -------
    code : bytes
        The code for the create call.
    data : bytes
        The data for the create call.
    """
    eof_metadata = metadata_from_container(
        data, validate=True, context=ContainerContext.CREATE_TX_DATA
    )

    total_code_size = Uint(
        sum([int(size) for size in eof_metadata.code_sizes])
    )
    total_container_size = Uint(
        sum([int(size) for size in eof_metadata.container_sizes])
    )

    container_size = (
        eof_metadata.body_start_index
        + eof_metadata.type_size
        + total_code_size
        + total_container_size
        + eof_metadata.data_size
    )

    eof = Eof(
        version=EofVersion.EOF1,
        container=data[:container_size],
        metadata=eof_metadata,
    )

    validator = Validator(
        eof=eof,
        sections={},
        current_index=Uint(0),
        current_code=eof.metadata.code_section_contents[0],
        current_pc=Uint(0),
        is_current_section_returning=False,
        has_return_contract=False,
        has_stop=False,
        has_return=False,
        reached_code_sections=[],
        referenced_subcontainers={},
        current_stack_height=None,
    )

    validate_body(validator)

    validate_eof_code(validator)

    return eof, data[container_size:]
