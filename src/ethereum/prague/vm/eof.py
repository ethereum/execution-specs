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

from typing import Set

from ethereum.base_types import Uint

from . import EOF, EOF_MAGIC, EOF_MAGIC_LENGTH, MAX_CODE_SIZE, EOFMetadata
from .exceptions import InvalidEOF
from .instructions import (
    OPCODES_INVALID_IN_EOF1,
    OPCODES_INVALID_IN_LEGACY,
    Ops,
)


def get_opcode(opcode: int, eof: EOF) -> Ops:
    """
    Get the opcode enum from the opcode value.

    Parameters
    ----------
    opcode : `int`
        The opcode value.
    eof : `EOF`
        The version of the EOF.

    Returns
    -------
    opcode : `Ops`
        The opcode enum.
    """
    try:
        op = Ops(opcode)
    except ValueError:
        raise ValueError(f"Invalid opcode: {opcode}")

    if eof == EOF.LEGACY and op in OPCODES_INVALID_IN_LEGACY:
        raise ValueError(f"Invalid opcode: {op}")
    elif eof == EOF.EOF1 and op in OPCODES_INVALID_IN_EOF1:
        raise ValueError(f"Invalid opcode: {op}")

    return op


def meta_from_valid_eof1_container(code: bytes) -> EOFMetadata:
    """
    Extract the code from a valid EOF1 container.

    Parameters
    ----------
    code : bytes
        The EOF1 container.

    Returns
    -------
    meta : EOFMetadata
        The meta from the EOF1 container.
    """
    # Skip the magic and version bytes
    position = Uint(EOF_MAGIC_LENGTH + 1)

    # Skip the type marker
    position += 1

    # Read the type size
    type_size = Uint.from_be_bytes(code[position : position + 2])
    position += 2

    # Skip the code marker
    code_size = Uint.from_be_bytes(code[position : position + 1])
    position += 1

    # Read the number of code sections
    num_code_sections = Uint.from_be_bytes(code[position : position + 2])
    position += 2
    code_sizes = []
    for _ in range(num_code_sections):
        code_size = Uint.from_be_bytes(code[position : position + 2])
        position += 2
        code_sizes.append(code_size)

    total_container_size = 0
    if code[position] == 3:
        # Skip container section marker
        position += 1

        # Read the number of container sections
        num_container_sections = Uint.from_be_bytes(
            code[position : position + 2]
        )
        position += 2

        # Skip the container sizes
        container_sizes = []
        for _ in range(num_container_sections):
            container_size = Uint.from_be_bytes(code[position : position + 2])
            total_container_size += container_size
            container_sizes.append(container_size)
            position += 2
    else:
        num_container_sections = Uint(0)
        container_sizes = None

    # Skip the data marker
    position += 1
    # Read the data size
    data_size = Uint.from_be_bytes(code[position : position + 2])
    position += 2

    # Skip the terminator
    position += 1
    body_start_index = position

    # Read the type section
    type_section_contents = []
    num_types = type_size // 4
    for _ in range(num_types):
        type_section_contents.append(code[position : position + 4])
        position += 4

    # Read the code section
    code_section_contents = []
    for code_size in code_sizes:
        code_section_contents.append(code[position : position + code_size])
        position += code_size

    if container_sizes:
        # Read the container section
        container_section_contents = []
        for container_size in container_sizes:
            container_section_contents.append(
                code[position : position + container_size]
            )
            position += container_size
    else:
        container_section_contents = None

    # Read the data section
    data_section_contents = code[position : position + data_size]

    return EOFMetadata(
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


def validate_header(container: bytes) -> EOFMetadata:
    """
    Validate the header of the EOF container.

    Parameters
    ----------
    container : bytes
        The EOF container to validate.

    Returns
    -------
    EOFMetadata
        The metadata of the EOF container.

    Raises
    ------
    InvalidEOF
        If the header of the EOF container is invalid.
    """
    counter = len(EOF_MAGIC) + 1

    # Get the one byte kind type
    if len(container) < counter + 1:
        raise InvalidEOF("Kind type not specified in header")
    kind_type = container[counter]
    counter += 1
    if kind_type != 1:
        raise InvalidEOF("Invalid kind type")

    # Get the 2 bytes type_size
    if len(container) < counter + 2:
        raise InvalidEOF("Type size not specified in header")
    type_size = Uint.from_be_bytes(container[counter : counter + 2])
    counter += 2
    if type_size < 4 or type_size > 4096 or type_size % 4 != 0:
        raise InvalidEOF("Invalid type size")
    num_types = type_size // 4

    # Get the 1 byte kind_code
    if len(container) < counter + 1:
        raise InvalidEOF("Kind code not specified in header")
    kind_code = container[counter]
    counter += 1
    if kind_code != 2:
        raise InvalidEOF("Invalid kind code")
    # Get the 2 bytes num_code_sections
    if len(container) < counter + 2:
        raise InvalidEOF("Number of code sections not specified in header")
    num_code_sections = Uint.from_be_bytes(container[counter : counter + 2])
    counter += 2
    if (
        num_code_sections < 1
        or num_code_sections > 1024
        or num_code_sections != num_types
    ):
        raise InvalidEOF("Invalid number of code sections")

    code_sizes = []
    for i in range(num_code_sections):
        # Get the 2 bytes code_size
        if len(container) < counter + 2:
            raise InvalidEOF(
                f"Code section {i} does not have a size specified in header"
            )
        code_size = Uint.from_be_bytes(container[counter : counter + 2])
        counter += 2
        if code_size == 0:
            raise InvalidEOF(f"Invalid code size for code section {i}")
        code_sizes.append(code_size)

    # Check if the container section is present
    if len(container) < counter + 1:
        raise InvalidEOF("Kind data not specified in header")
    if container[counter] == 3:
        container_sizes = []
        counter += 1
        # Get the 2 bytes num_container_sections
        if len(container) < counter + 2:
            raise InvalidEOF("Number of container sections not specified")
        num_container_sections = Uint.from_be_bytes(
            container[counter : counter + 2]
        )
        counter += 2
        if num_container_sections < 1 or num_container_sections > 256:
            raise InvalidEOF("Invalid number of container sections")

        for i in range(num_container_sections):
            # Get the 2 bytes container_size
            if len(container) < counter + 2:
                raise InvalidEOF(
                    f"Container section {i} does not have a size specified"
                )
            container_size = Uint.from_be_bytes(
                container[counter : counter + 2]
            )
            counter += 2
            if container_size == 0:
                raise InvalidEOF("Invalid container size")
            container_sizes.append(container_size)
    else:
        num_container_sections = Uint(0)
        container_sizes = None

    # Get 1 byte kind_data
    kind_data = container[counter]
    counter += 1
    if kind_data != 4:
        raise InvalidEOF("Invalid kind data")
    # Get 2 bytes data_size
    if len(container) < counter + 2:
        raise InvalidEOF("Data size not specified in the header")
    data_size = Uint.from_be_bytes(container[counter : counter + 2])
    counter += 2

    # Get 1 byte terminator
    if len(container) < counter + 1:
        raise InvalidEOF("Header missing terminator byte")
    terminator = container[counter]
    counter += 1
    if terminator != 0:
        raise InvalidEOF("Invalid terminator")
    body_start_index = Uint(counter)

    if len(container) < counter + type_size:
        raise InvalidEOF("Type section size does not match header")
    type_section_contents = []
    for _ in range(type_size // 4):
        type_section_contents.append(container[counter : counter + 4])
        counter += 4

    if len(container) < counter + sum(code_sizes):
        raise InvalidEOF("Code section size does not match header")
    code_section_contents = []
    for code_size in code_sizes:
        code_section_contents.append(container[counter : counter + code_size])
        counter += code_size

    if container_sizes:
        if len(container) < counter + sum(container_sizes):
            raise InvalidEOF("Container section size does not match header")
        container_section_contents = []
        for container_size in container_sizes:
            container_section_contents.append(
                container[counter : counter + container_size]
            )
            counter += container_size
    else:
        container_section_contents = None

    if len(container) < counter + data_size:
        raise InvalidEOF("Data section size does not match header")
    data_section_contents = container[counter : counter + data_size]
    counter += data_size

    # Check for stray bytes after the data section
    if len(container) > counter:
        raise InvalidEOF("Stray bytes found after data section")

    return EOFMetadata(
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


def validate_body(eof_meta: EOFMetadata) -> None:
    """
    Validate the body of the EOF container.

    Parameters
    ----------
    eof_meta : EOFMetadata
        The metadata of the EOF container.

    Raises
    ------
    InvalidEOF
        If the EOF container is invalid.
    """
    for i, type_section in enumerate(eof_meta.type_section_contents):
        num_inputs = type_section[0]
        if num_inputs > 127:
            raise InvalidEOF(f"Invalid number of inputs for type {i}")

        num_outputs = type_section[1]
        if num_outputs > 128:
            raise InvalidEOF(f"Invalid number of outputs for type {i}")

        max_stack_height = Uint.from_be_bytes(type_section[2:])
        if max_stack_height > 1023:
            raise InvalidEOF(f"Invalid max stack height for type {i}")


def get_valid_instructions(code: bytes) -> Set[int]:
    """
    Get the valid instructions for the code. These will also be the
    positions within the code to which, jumps can be performed.
    The immediate bytesof the PUSH, RJUMP, RJUMPI, RJUMPV opcodes
    are invalid as jump destinations.

    Parameters
    ----------
    code : bytes
        The code section of the EOF container.

    Returns
    -------
    valid_instructions : Set[int]
        The valid jump destinations in the code.
    """
    counter = 0
    valid_instructions = set()
    while counter < len(code):
        try:
            opcode = get_opcode(code[counter], EOF.EOF1)
        except ValueError:
            raise InvalidEOF("Invalid opcode in code section")
        valid_instructions.add(counter)

        counter += 1

        if (
            opcode.value >= Ops.PUSH1.value
            and opcode.value <= Ops.PUSH32.value
        ):
            push_data_size = opcode.value - Ops.PUSH1.value + 1
            if len(code) < counter + push_data_size:
                raise InvalidEOF("Push data missing")
            counter += push_data_size

        elif opcode in (Ops.RJUMP, Ops.RJUMPI):
            if len(code) < counter + 2:
                raise InvalidEOF("Relative jump offset missing")
            counter += 2

        elif opcode == Ops.RJUMPV:
            if len(code) < counter + 1:
                raise InvalidEOF("max_index missing for RJUMPV")
            max_index = code[counter]
            num_relative_indices = max_index + 1
            counter += 1

            for _ in range(num_relative_indices):
                if len(code) < counter + 2:
                    raise InvalidEOF("Relative jump indices missing")
                counter += 2

    return valid_instructions


def validate_code_section(code: bytes) -> None:
    """
    Validate a code section of the EOF container.

    Parameters
    ----------
    code : bytes
        The code section to validate.

    Raises
    ------
    InvalidEOF
        If the code section is invalid.
    """
    counter = 0
    valid_instructions = get_valid_instructions(code)

    for counter in valid_instructions:
        opcode = get_opcode(code[counter], EOF.EOF1)

        # Make sure the bytes encoding relative offset
        # are available
        if opcode in (Ops.RJUMP, Ops.RJUMPI):
            relative_offset = int.from_bytes(
                code[counter + 1 : counter + 3], "big", signed=True
            )
            pc_post_instruction = counter + 3
            jump_destination = pc_post_instruction + relative_offset
            if (
                jump_destination < 0
                or len(code) < jump_destination + 1
                or jump_destination not in valid_instructions
            ):
                raise InvalidEOF("Invalid jump destination")

        elif opcode == Ops.RJUMPV:
            num_relative_indices = code[counter + 1] + 1
            # pc_post_instruction will be
            # counter + 1 <- for normal pc increment to next opcode
            # + 1 <- for the 1 byte max_index
            # + 2 * num_relative_indices <- for the 2 bytes of each offset
            pc_post_instruction = counter + 2 + 2 * num_relative_indices

            index_position = counter + 2
            for _ in range(num_relative_indices):
                relative_offset = int.from_bytes(
                    code[index_position : index_position + 2],
                    "big",
                    signed=True,
                )
                index_position += 2
                jump_destination = pc_post_instruction + relative_offset
                if (
                    jump_destination < 0
                    or len(code) < jump_destination + 1
                    or jump_destination not in valid_instructions
                ):
                    raise InvalidEOF("Invalid jump destination")


def validate_eof_code(eof_meta: EOFMetadata) -> None:
    """
    Validate the code section of the EOF container.

    Parameters
    ----------
    eof_meta : EOFMetadata
        The metadata of the EOF container.

    Raises
    ------
    InvalidEOF
        If the code section is invalid.
    """
    for code in eof_meta.code_section_contents:
        validate_code_section(code)


def validate_eof_container(container: bytes) -> None:
    """
    Validate the Ethereum Object Format (EOF) container.

    Parameters
    ----------
    container : bytes
        The EOF container to validate.

    Raises
    ------
    InvalidEOF
        If the EOF container is invalid.
    """
    # Validate the magic
    if (
        len(container) < EOF_MAGIC_LENGTH
        or container[:EOF_MAGIC_LENGTH] != EOF_MAGIC
    ):
        raise InvalidEOF("Invalid magic")

    if len(container) < EOF_MAGIC_LENGTH + 1:
        raise InvalidEOF("EOF version not specified")
    elif container[EOF_MAGIC_LENGTH] != 1:
        raise InvalidEOF("Invalid EOF version")

    if len(container) > 2 * MAX_CODE_SIZE:
        raise InvalidEOF("EOF container size too long")

    eof_meta = validate_header(container)

    validate_body(eof_meta)

    validate_eof_code(eof_meta)
