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

from . import EOF_MAGIC, EOF_MAGIC_LENGTH, MAX_CODE_SIZE, Eof, EofMetadata
from .exceptions import InvalidEof
from .instructions import (
    EOF1_TERMINATING_INSTRUCTIONS,
    OPCODES_INVALID_IN_EOF1,
    OPCODES_INVALID_IN_LEGACY,
    Ops,
    op_stack_items,
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
    pc_post_instruction: int
    relative_offsets: List[int]
    target_section_index: Optional[Uint]
    stack_height: Optional[OperandStackHeight]


def map_int_to_op(opcode: int, eof: Eof) -> Ops:
    """
    Get the opcode enum from the opcode value.

    Parameters
    ----------
    opcode : `int`
        The opcode value.
    eof : `Eof`
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

    if eof == Eof.LEGACY and op in OPCODES_INVALID_IN_LEGACY:
        raise ValueError(f"Invalid legacy opcode: {op}")
    elif eof == Eof.EOF1 and op in OPCODES_INVALID_IN_EOF1:
        raise ValueError(f"Invalid eof1 opcode: {op}")

    return op


def parse_container_metadata(container: bytes, validate: bool) -> EofMetadata:
    """
    Validate the header of the EOF container.

    Parameters
    ----------
    container : bytes
        The EOF container to validate.
    validate : bool
        Whether to validate the EOF container. If the container is simply read
        from an existing account, it is assumed to be validated. However, if
        the container is being created, it should be validated first.

    Returns
    -------
    EofMetadata
        The metadata of the EOF container.

    Raises
    ------
    InvalidEof
        If the header of the EOF container is invalid.
    """
    counter = len(EOF_MAGIC) + 1

    # Get the one byte kind type
    if validate and len(container) < counter + 1:
        raise InvalidEof("Kind type not specified in header")
    kind_type = container[counter]
    counter += 1
    if validate and kind_type != 1:
        raise InvalidEof("Invalid kind type")

    # Get the 2 bytes type_size
    if validate and len(container) < counter + 2:
        raise InvalidEof("Type size not specified in header")
    type_size = Uint.from_be_bytes(container[counter : counter + 2])
    counter += 2
    if validate and (type_size < 4 or type_size > 4096 or type_size % 4 != 0):
        raise InvalidEof("Invalid type size")
    num_types = type_size // 4

    # Get the 1 byte kind_code
    if validate and len(container) < counter + 1:
        raise InvalidEof("Kind code not specified in header")
    kind_code = container[counter]
    counter += 1
    if validate and kind_code != 2:
        raise InvalidEof("Invalid kind code")
    # Get the 2 bytes num_code_sections
    if validate and len(container) < counter + 2:
        raise InvalidEof("Number of code sections not specified in header")
    num_code_sections = Uint.from_be_bytes(container[counter : counter + 2])
    counter += 2
    if validate and (
        num_code_sections < 1
        or num_code_sections > 1024
        or num_code_sections != num_types
    ):
        raise InvalidEof("Invalid number of code sections")

    code_sizes = []
    for i in range(num_code_sections):
        # Get the 2 bytes code_size
        if validate and len(container) < counter + 2:
            raise InvalidEof(
                f"Code section {i} does not have a size specified in header"
            )
        code_size = Uint.from_be_bytes(container[counter : counter + 2])
        counter += 2
        if validate and code_size == 0:
            raise InvalidEof(f"Invalid code size for code section {i}")
        code_sizes.append(code_size)

    # Check if the container section is present
    if validate and len(container) < counter + 1:
        raise InvalidEof("Kind data not specified in header")
    if container[counter] == 3:
        container_sizes = []
        counter += 1
        # Get the 2 bytes num_container_sections
        if validate and len(container) < counter + 2:
            raise InvalidEof("Number of container sections not specified")
        num_container_sections = Uint.from_be_bytes(
            container[counter : counter + 2]
        )
        counter += 2
        if validate and (
            num_container_sections < 1 or num_container_sections > 256
        ):
            raise InvalidEof("Invalid number of container sections")

        for i in range(num_container_sections):
            # Get the 2 bytes container_size
            if validate and len(container) < counter + 2:
                raise InvalidEof(
                    f"Container section {i} does not have a size specified"
                )
            container_size = Uint.from_be_bytes(
                container[counter : counter + 2]
            )
            counter += 2
            if validate and container_size == 0:
                raise InvalidEof("Invalid container size")
            container_sizes.append(container_size)
    else:
        num_container_sections = Uint(0)
        container_sizes = None

    # Get 1 byte kind_data
    kind_data = container[counter]
    counter += 1
    if validate and kind_data != 4:
        raise InvalidEof("Invalid kind data")
    # Get 2 bytes data_size
    if validate and len(container) < counter + 2:
        raise InvalidEof("Data size not specified in the header")
    data_size = Uint.from_be_bytes(container[counter : counter + 2])
    counter += 2

    # Get 1 byte terminator
    if validate and len(container) < counter + 1:
        raise InvalidEof("Header missing terminator byte")
    terminator = container[counter]
    counter += 1
    if validate and terminator != 0:
        raise InvalidEof("Invalid terminator")
    body_start_index = Uint(counter)

    if validate and len(container) < counter + type_size:
        raise InvalidEof("Type section size does not match header")
    type_section_contents = []
    for _ in range(type_size // 4):
        type_section_contents.append(container[counter : counter + 4])
        counter += 4

    if validate and len(container) < counter + sum(code_sizes):
        raise InvalidEof("Code section size does not match header")
    code_section_contents = []
    for code_size in code_sizes:
        code_section_contents.append(container[counter : counter + code_size])
        counter += code_size

    if container_sizes:
        if validate and len(container) < counter + sum(container_sizes):
            raise InvalidEof("Container section size does not match header")
        container_section_contents = []
        for container_size in container_sizes:
            container_section_contents.append(
                container[counter : counter + container_size]
            )
            counter += container_size
    else:
        container_section_contents = None

    if validate and len(container) < counter + data_size:
        raise InvalidEof("Data section size does not match header")
    data_section_contents = container[counter : counter + data_size]
    counter += data_size

    # Check for stray bytes after the data section
    if validate and len(container) > counter:
        raise InvalidEof("Stray bytes found after data section")

    return EofMetadata(
        type_size=type_size,
        num_code_sections=num_code_sections,
        code_sizes=code_sizes,
        num_container_sections=num_container_sections,
        container_sizes=container_sizes,
        data_size=data_size,
        body_start_index=body_start_index,
        type_section_contents=type_section_contents,
        code_section_contents=code_section_contents,
        container_section_contents=container_section_contents,
        data_section_contents=data_section_contents,
    )


def validate_body(eof_meta: EofMetadata) -> None:
    """
    Validate the body of the EOF container.

    Parameters
    ----------
    eof_meta : EofMetadata
        The metadata of the EOF container.

    Raises
    ------
    InvalidEof
        If the EOF container is invalid.
    """
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


def analyse_code_section(code: bytes) -> Dict[Uint, InstructionMetadata]:
    """
    Analyse a code section of the EOF container.

    Parameters
    ----------
    code : bytes
        The code section to analyse.

    Returns
    -------
    section_metadata: Dict[Uint, InstructionMetadata]

    Raises
    ------
    InvalidEof
        If the code section is invalid.
    """
    counter = 0
    section_metadata = {}
    target_section_index = None
    while counter < len(code):
        position = Uint(counter)
        try:
            opcode = map_int_to_op(code[counter], Eof.EOF1)
        except ValueError:
            raise InvalidEof("Invalid opcode in code section")

        counter += 1

        if (
            opcode.value >= Ops.PUSH1.value
            and opcode.value <= Ops.PUSH32.value
        ):
            # Immediate Data Check
            push_data_size = opcode.value - Ops.PUSH1.value + 1
            if len(code) < counter + push_data_size:
                raise InvalidEof("Push data missing")
            counter += push_data_size

            # Successor instruction positions
            relative_offsets = [0]

        elif opcode in (Ops.RJUMP, Ops.RJUMPI):
            # Immediate Data Check
            if len(code) < counter + 2:
                raise InvalidEof("Relative jump offset missing")
            relative_offset = int.from_bytes(
                code[counter : counter + 2], "big", signed=True
            )
            counter += 2

            # Successor instruction positions
            if opcode == Ops.RJUMP:
                relative_offsets = [relative_offset]
            else:
                relative_offsets = [0, relative_offset]

        elif opcode == Ops.RJUMPV:
            # Immediate Data Check
            if len(code) < counter + 1:
                raise InvalidEof("max_index missing for RJUMPV")
            max_index = code[counter]
            num_relative_indices = max_index + 1
            counter += 1

            # Successor instruction positions
            relative_offsets = [0]
            for _ in range(num_relative_indices):
                if len(code) < counter + 2:
                    raise InvalidEof("Relative jump indices missing")
                relative_offset = int.from_bytes(
                    code[counter : counter + 2],
                    "big",
                    signed=True,
                )
                counter += 2
                relative_offsets += [relative_offset]

        elif opcode == Ops.CALLF:
            # Immediate Data Check
            if len(code) < counter + 2:
                raise InvalidEof("CALLF target code section index missing")
            target_section_index = Uint.from_be_bytes(
                code[counter : counter + 2],
            )
            counter += 2

            # Successor instruction positions
            relative_offsets = [0]
        elif opcode == Ops.DATALOADN:
            # Immediate Data Check
            if len(code) < counter + 2:
                raise InvalidEof("DATALOADN offset missing")
            counter += 2

            # Successor instruction positions
            relative_offsets = [0]
        elif opcode in (Ops.DUPN, Ops.SWAPN, Ops.EXCHANGE):
            # Immediate Data Check
            if len(code) < counter + 1:
                raise InvalidEof("DUPN/SWAPN/EXCHANGE index missing")
            counter += 1

            # Successor instruction positions
            relative_offsets = [0]
        elif opcode in EOF1_TERMINATING_INSTRUCTIONS:
            # Immediate Data Check
            pass

            # Successor instruction positions
            relative_offsets = []
        else:
            # Immediate Data Check
            pass

            # Successor instruction positions
            relative_offsets = [0]

        section_metadata[position] = InstructionMetadata(
            opcode=opcode,
            pc_post_instruction=counter,
            relative_offsets=relative_offsets,
            target_section_index=target_section_index,
            stack_height=None,
        )

    return section_metadata


def validate_code_section(
    eof_meta: EofMetadata,
    code_index: Uint,
    section_metadata: Dict[Uint, InstructionMetadata],
) -> None:
    """
    Validate a code section of the EOF container.

    Parameters
    ----------
    eof_meta : EofMetadata
        The metadata of the EOF container.
    code_index : Uint
        The index of the code section.
    section_metadata : Dict[Uint, InstructionMetadata]
        The metadata of the code section.

    Raises
    ------
    InvalidEof
        If the code section is invalid.
    """
    code = eof_meta.code_section_contents[code_index]

    valid_opcode_positions = list(section_metadata.keys())
    first_instruction = min(section_metadata.keys())
    last_instruction = max(section_metadata.keys())

    section_type = eof_meta.type_section_contents[code_index]
    section_inputs = section_type[0]
    section_max_stack_height = Uint.from_be_bytes(section_type[2:])

    current_stack_height = OperandStackHeight(
        min=section_inputs,
        max=section_inputs,
    )
    for position, metadata in section_metadata.items():
        opcode = metadata.opcode

        # TODO: See if ordering can automatically be take care of
        # Initiate the stack height for the first instruction
        if position == first_instruction:
            metadata.stack_height = deepcopy(current_stack_height)

        # The section has to end in a terminating instruction
        if position == last_instruction:
            if (
                opcode not in EOF1_TERMINATING_INSTRUCTIONS
                and opcode != Ops.RJUMP
            ):
                raise InvalidEof("Code section does not terminate")

        if metadata.stack_height is None:
            raise InvalidEof("Stack height not set")

        # Opcode Specific Validity Checks
        if opcode == Ops.CALLF:
            assert metadata.target_section_index is not None
            # General Validity Check
            if metadata.target_section_index >= eof_meta.num_code_sections:
                raise InvalidEof("Invalid target code section index")

            # Stack Height Check

            target_section_type = eof_meta.type_section_contents[
                metadata.target_section_index
            ]
            target_inputs = target_section_type[0]
            target_outputs = target_section_type[1]
            target_max_height = Uint.from_be_bytes(target_section_type[2:])

            if metadata.stack_height.min < target_inputs:
                raise InvalidEof("Invalid stack height")

            # Stack Overflow Check
            if (
                metadata.stack_height.max
                > 1024 - target_max_height + target_inputs
            ):
                raise InvalidEof("Stack overflow")

            # Update the stack height after instruction
            increment = target_outputs - target_inputs
            current_stack_height.min += increment
            current_stack_height.max += increment

        elif opcode == Ops.RETF:
            # General Validity Checks
            if code_index == 0:
                raise InvalidEof("First code section cannot return")

            # Stack Height Check
            if metadata.stack_height.min != metadata.stack_height.max:
                raise InvalidEof("Invalid stack height")
            type_section = eof_meta.type_section_contents[code_index]
            type_section_outputs = type_section[1]
            if metadata.stack_height.min != type_section_outputs:
                raise InvalidEof("Invalid stack height")

            # Stack Overflow Check
            pass

            # Update the stack height after instruction
            instruction_inputs = op_stack_items[opcode].inputs
            instruction_outputs = op_stack_items[opcode].outputs
            current_stack_height.min += (
                instruction_outputs - instruction_inputs
            )
            current_stack_height.max += (
                instruction_outputs - instruction_inputs
            )
        elif opcode == Ops.DATALOADN:
            # General Validity Checks
            offset = Uint.from_be_bytes(code[position + 1 : position + 3])
            if offset >= eof_meta.data_size:
                raise InvalidEof("Invalid DATALOADN offset")

            # Stack Height Check
            instruction_inputs = op_stack_items[opcode].inputs
            if metadata.stack_height.min < instruction_inputs:
                raise InvalidEof("Invalid stack height")

            # Stack Overflow Check
            pass

            # Update the stack height after instruction
            instruction_inputs = op_stack_items[opcode].inputs
            instruction_outputs = op_stack_items[opcode].outputs
            current_stack_height.min += (
                instruction_outputs - instruction_inputs
            )
            current_stack_height.max += (
                instruction_outputs - instruction_inputs
            )

        elif opcode == Ops.DUPN:
            # General Validity Checks
            pass

            # Stack Height Check
            immediate_data = code[position + 1]
            n = immediate_data + 1
            if current_stack_height.min < n:
                raise InvalidEof("Invalid stack height for DUPN")

            # Stack Overflow Check
            pass

            # Update the stack height after instruction
            current_stack_height.min += 1
            current_stack_height.max += 1

        elif opcode == Ops.SWAPN:
            # General Validity Checks
            pass

            # Stack Height Check
            immediate_data = code[position + 1]
            n = immediate_data + 1
            if current_stack_height.min < n + 1:
                raise InvalidEof("Invalid stack height for SWAPN")

            # Stack Overflow Check
            pass

            # Update the stack height after instruction
            pass

        elif opcode == Ops.EXCHANGE:
            # General Validity Checks
            pass

            # Stack Height Check
            immediate_data = code[position + 1]
            n = (immediate_data >> 4) + 1
            m = (immediate_data & 0xF) + 1
            if current_stack_height.min < n + m + 1:
                raise InvalidEof("Invalid stack height for EXCHANGE")

            # Stack Overflow Check
            pass

            # Update the stack height after instruction
            pass

        else:
            # General Validity Checks
            pass

            # Stack Height Check
            instruction_inputs = op_stack_items[opcode].inputs
            if metadata.stack_height.min < instruction_inputs:
                raise InvalidEof("Invalid stack height")

            # Stack Overflow Check
            pass

            # Update the stack height after instruction
            instruction_inputs = op_stack_items[opcode].inputs
            instruction_outputs = op_stack_items[opcode].outputs
            current_stack_height.min += (
                instruction_outputs - instruction_inputs
            )
            current_stack_height.max += (
                instruction_outputs - instruction_inputs
            )

        # Update the stack height for Successor instructions
        for relative_offset in metadata.relative_offsets:
            if metadata.pc_post_instruction + relative_offset < 0:
                raise InvalidEof("Invalid successor or jump destination")

            successor_position = Uint(
                metadata.pc_post_instruction + relative_offset
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

    # TODO: See if this can be integrated in the above loop
    computed_maximum_stack_height = 0
    for _, metadata in section_metadata.items():
        assert metadata.stack_height is not None
        if metadata.stack_height.max > computed_maximum_stack_height:
            computed_maximum_stack_height = metadata.stack_height.max

    if computed_maximum_stack_height > 1023:
        raise InvalidEof("Invalid stack height")

    if computed_maximum_stack_height != section_max_stack_height:
        raise InvalidEof("Invalid stack height")


def validate_eof_code(eof_meta: EofMetadata) -> None:
    """
    Validate the code section of the EOF container.

    Parameters
    ----------
    eof_meta : EofMetadata
        The metadata of the EOF container.

    Raises
    ------
    InvalidEof
        If the code section is invalid.
    """
    for code_index, code in enumerate(eof_meta.code_section_contents):
        section_metadata = analyse_code_section(code)

        validate_code_section(eof_meta, Uint(code_index), section_metadata)


def validate_eof_container(container: bytes) -> None:
    """
    Validate the Ethereum Object Format (EOF) container.

    Parameters
    ----------
    container : bytes
        The EOF container to validate.

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

    eof_metadata = parse_container_metadata(container, validate=True)

    validate_body(eof_metadata)

    validate_eof_code(eof_metadata)
