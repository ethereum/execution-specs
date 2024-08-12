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
from dataclasses import dataclass
from typing import Dict, List, Optional

from ethereum.base_types import Uint

from . import EOF_MAGIC, EOF_MAGIC_LENGTH, MAX_CODE_SIZE, Eof, EofVersion
from .eof1.utils import metadata_from_container
from .exceptions import InvalidEof
from .instructions import (
    EOF1_TERMINATING_INSTRUCTIONS,
    OPCODES_INVALID_IN_EOF1,
    OPCODES_INVALID_IN_LEGACY,
    Ops,
)


@dataclass
class OperandStackHeight:
    """
    Stack height bounds of an instruction.
    """

    min: int
    max: int


@dataclass
class InstructionMetadata:
    """
    Metadata of an instruction in the code section.
    """

    opcode: Ops
    pc_post_instruction: Uint
    relative_offsets: List[int]
    target_index: Optional[Uint]
    container_index: Optional[Uint]
    stack_height: Optional[OperandStackHeight]


SectionMetadata = Dict[Uint, InstructionMetadata]


@dataclass
class Validator:
    """
    Validator for the Ethereum Object Format (EOF) container.
    """

    eof: Eof
    sections: Dict[Uint, SectionMetadata]
    current_index: Uint
    current_code: bytes
    current_pc: Uint
    has_return_contract: bool
    has_stop: bool
    has_return: bool
    referenced_subcontainers: Dict[Ops, List[Uint]]
    current_stack_height: Optional[OperandStackHeight]


def map_int_to_op(opcode: int, eof_version: EofVersion) -> Ops:
    """
    Get the opcode enum from the opcode value.

    Parameters
    ----------
    opcode : `int`
        The opcode value.
    eof_version : `EofVersion`
        The version of the EOF.

    Returns
    -------
    opcode : `Ops`
        The opcode enum.
    """
    try:
        op = Ops(opcode)
    except ValueError as e:
        raise ValueError(f"Invalid opcode: {opcode}") from e

    if eof_version == EofVersion.LEGACY and op in OPCODES_INVALID_IN_LEGACY:
        raise ValueError(f"Invalid legacy opcode: {op}")
    elif eof_version == EofVersion.EOF1 and op in OPCODES_INVALID_IN_EOF1:
        raise ValueError(f"Invalid eof1 opcode: {op}")

    return op


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

        max_stack_height = Uint.from_be_bytes(type_section[2:])
        if max_stack_height > 1023:
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
            successor_position + 1 > len(code)
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
    # TODO: Move this import to the top
    from .eof1.instructions_check import get_op_validation
    from .eof1.stack_height_check import get_stack_validation

    while validator.current_pc < len(validator.current_code):
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
    section_max_stack_height = Uint.from_be_bytes(section_type[2:])

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

        # The section has to end in a terminating instruction
        if index + 1 == len(valid_opcode_positions):
            if op not in EOF1_TERMINATING_INSTRUCTIONS and op != Ops.RJUMP:
                raise InvalidEof("Code section does not terminate")

        if op_metadata.stack_height is None:
            raise InvalidEof("Stack height not set")

        stack_implementation = get_stack_validation(op)
        stack_implementation(validator)

        update_successor_stack_height(validator)
        if op_metadata.stack_height.max > computed_maximum_stack_height:
            computed_maximum_stack_height = op_metadata.stack_height.max

    if computed_maximum_stack_height > 1023:
        raise InvalidEof("Invalid stack height")

    if computed_maximum_stack_height != section_max_stack_height:
        raise InvalidEof("Invalid stack height")


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
        validator.current_index = Uint(code_index)
        validator.current_code = code
        validator.current_pc = Uint(0)
        validator.sections[validator.current_index] = {}
        validate_code_section(validator)

    if validator.has_return_contract and (
        validator.has_return or validator.has_stop
    ):
        raise InvalidEof("Container has both RETURNCONTRACT and STOP/RETURN")

    if eof_meta.num_container_sections > 0:
        eofcreate_references = validator.referenced_subcontainers[
            Ops.EOFCREATE
        ]
        returncontract_references = validator.referenced_subcontainers[
            Ops.RETURNCONTRACT
        ]
        for index in range(len(eof_meta.container_section_contents)):
            if (
                index in eofcreate_references
                and index in returncontract_references
            ):
                raise InvalidEof(
                    "Container referenced by both EOFCREATE and RETURNCONTRACT"
                )
            elif (
                index not in eofcreate_references
                and index not in returncontract_references
            ):
                raise InvalidEof("Container never referenced")

            sub_validator = validate_eof_container(
                eof_meta.container_section_contents[index], False
            )
            if index in eofcreate_references and (
                sub_validator.has_stop or sub_validator.has_return
            ):
                raise InvalidEof(
                    "Container referenced by EOFCREATE has STOP or RETURN"
                )
            if (
                index in returncontract_references
                and sub_validator.has_return_contract
            ):
                raise InvalidEof(
                    "Container referenced by RETURNCONTRACT has RETURNCONTRACT"
                )


def validate_eof_container(
    container: bytes, is_init_container: bool
) -> Validator:
    """
    Validate the Ethereum Object Format (EOF) container.

    Parameters
    ----------
    container : bytes
        The EOF container to validate.
    is_init_container : bool
        Whether the container is an init container for EOFCREATE/
        create transactions.

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
        is_deploy_container=False,
        is_init_container=is_init_container,
    )

    eof = Eof(
        version=EofVersion.EOF1,
        container=container,
        metadata=metadata,
        is_deploy_container=False,
        is_init_container=is_init_container,
    )

    validator = Validator(
        eof=eof,
        current_index=Uint(0),
        current_code=metadata.code_section_contents[0],
        current_pc=Uint(0),
        sections={},
        has_return_contract=False,
        has_stop=False,
        has_return=False,
        referenced_subcontainers={Ops.EOFCREATE: [], Ops.RETURNCONTRACT: []},
        current_stack_height=None,
    )

    validate_body(validator)

    validate_eof_code(validator)

    if is_init_container and (validator.has_stop or validator.has_return):
        raise InvalidEof("Init container has STOP/RETURN")

    return validator
