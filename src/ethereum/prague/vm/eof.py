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

from dataclasses import dataclass
from typing import List, Optional, Set

from ethereum.base_types import Uint

from . import EOF, EOF_MAGIC, EOF_MAGIC_LENGTH
from .exceptions import InvalidEOF
from .instructions import (
    OPCODES_INVALID_IN_EOF1,
    OPCODES_INVALID_IN_LEGACY,
    Ops,
)


@dataclass
class EOFHeader:
    """
    Dataclass to hold the header information of the
    EOF container.
    """

    type_size: Uint
    num_code_sections: Uint
    code_sizes: List[Uint]
    num_container_sections: Uint
    container_sizes: Optional[List[Uint]]
    data_size: Uint
    header_end_index: Uint


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


def code_from_valid_eof1_container(code: bytes) -> bytes:
    """
    Extract the code from a valid EOF1 container.

    Parameters
    ----------
    code : bytes
        The EOF1 container.

    Returns
    -------
    bytes
        The code extracted from the EOF1 container.
    """
    # Skip the magic and version bytes
    position = EOF_MAGIC_LENGTH + 1

    # Skip the type marker
    position += 1

    # Read the type size
    type_size = Uint.from_be_bytes(code[position : position + 2])
    position += 2

    # Skip the code marker
    position += 1

    # Read the number of code sections
    num_code_sections = Uint.from_be_bytes(code[position : position + 2])
    position += 2
    code_sizes = []
    for _ in range(num_code_sections):
        code_size = Uint.from_be_bytes(code[position : position + 2])
        position += 2
        code_sizes.append(code_size)

    total_code_size = sum(code_sizes)

    if code[position] == 3:
        # Skip container section marker
        position += 1

        # Read the number of container sections
        num_container_sections = Uint.from_be_bytes(
            code[position : position + 2]
        )
        position += 2

        # Skip the container sizes
        for _ in range(num_container_sections):
            position += 2

    # Skip the data marker
    position += 1

    # Skip the data size
    position += 2

    # Skip the terminator
    position += 1

    # Skip the types section in the body
    num_types = type_size // 4
    # Multiplied by 4 since the input and output have 1 byte
    # and the max_stack_height has 2 bytes
    position += num_types * 4

    # Read the code
    return code[position : position + total_code_size]


def validate_header(code: bytes) -> EOFHeader:
    """
    Validate the header of the EOF container.

    Parameters
    ----------
    code : bytes
        The EOF container to validate.

    Returns
    -------
    EOFHeader
        The header of the EOF container.

    Raises
    ------
    InvalidEOF
        If the header of the EOF container is invalid.
    """
    counter = len(EOF_MAGIC) + 1

    eof_header = EOFHeader(
        Uint(0), Uint(0), [], Uint(0), None, Uint(0), Uint(0)
    )

    # Get the one byte kind type
    if len(code) < counter + 1:
        raise InvalidEOF("Kind type not specified in header")
    kind_type = code[counter]
    counter += 1
    if kind_type != 1:
        raise InvalidEOF("Invalid kind type")

    # Get the 2 bytes type_size
    if len(code) < counter + 2:
        raise InvalidEOF("Type size not specified in header")
    type_size = Uint.from_be_bytes(code[counter : counter + 2])
    counter += 2
    if type_size < 4 or type_size > 4096 or type_size % 4 != 0:
        raise InvalidEOF("Invalid type size")
    eof_header.type_size = type_size
    num_types = type_size // 4

    # Get the 1 byte kind_code
    if len(code) < counter + 1:
        raise InvalidEOF("Kind code not specified in header")
    kind_code = code[counter]
    counter += 1
    if kind_code != 2:
        raise InvalidEOF("Invalid kind code")
    # Get the 2 bytes num_code_sections
    if len(code) < counter + 2:
        raise InvalidEOF("Number of code sections not specified in header")
    num_code_sections = Uint.from_be_bytes(code[counter : counter + 2])
    counter += 2
    if (
        num_code_sections < 1
        or num_code_sections > 1024
        or num_code_sections != num_types
    ):
        raise InvalidEOF("Invalid number of code sections")
    eof_header.num_code_sections = num_code_sections

    for i in range(num_code_sections):
        # Get the 2 bytes code_size
        if len(code) < counter + 2:
            raise InvalidEOF(
                f"Code section {i} does not have a size specified in header"
            )
        code_size = Uint.from_be_bytes(code[counter : counter + 2])
        counter += 2
        if code_size == 0:
            raise InvalidEOF(f"Invalid code size for code section {i}")
        eof_header.code_sizes.append(code_size)

    # Check if the container section is present
    if len(code) < counter + 1:
        raise InvalidEOF("Kind data not specified in header")
    if code[counter] == 3:
        eof_header.container_sizes = []
        counter += 1
        # Get the 2 bytes num_container_sections
        if len(code) < counter + 2:
            raise InvalidEOF("Number of container sections not specified")
        num_container_sections = Uint.from_be_bytes(
            code[counter : counter + 2]
        )
        counter += 2
        if num_container_sections < 1 or num_container_sections > 256:
            raise InvalidEOF("Invalid number of container sections")
        eof_header.num_container_sections = num_container_sections

        for i in range(num_container_sections):
            # Get the 2 bytes container_size
            if len(code) < counter + 2:
                raise InvalidEOF(
                    f"Container section {i} does not have a size specified"
                )
            container_size = Uint.from_be_bytes(code[counter : counter + 2])
            counter += 2
            if container_size == 0:
                raise InvalidEOF("Invalid container size")
            eof_header.container_sizes.append(container_size)

    # Get 1 byte kind_data
    kind_data = code[counter]
    counter += 1
    if kind_data != 4:
        raise InvalidEOF("Invalid kind data")
    # Get 2 bytes data_size
    if len(code) < counter + 2:
        raise InvalidEOF("Data size not specified in the header")
    data_size = Uint.from_be_bytes(code[counter : counter + 2])
    counter += 2
    eof_header.data_size = data_size

    # Get 1 byte terminator
    if len(code) < counter + 1:
        raise InvalidEOF("Header missing terminator byte")
    terminator = code[counter]
    counter += 1
    if terminator != 0:
        raise InvalidEOF("Invalid terminator")
    eof_header.header_end_index = Uint(counter)

    return eof_header


def validate_body(code: bytes, eof_header: EOFHeader) -> None:
    """
    Validate the body of the EOF container.

    Parameters
    ----------
    code : bytes
        The EOF container to validate.
    eof_header : EOFHeader
        The header of the EOF container.

    Raises
    ------
    InvalidEOF
        If the EOF container is invalid.
    """
    counter = eof_header.header_end_index
    num_types = eof_header.type_size // 4

    for i in range(num_types):
        if len(code) < counter + 1:
            raise InvalidEOF(f"Number of inputs not specified for type {i}")
        num_inputs = code[counter]
        counter += 1
        if num_inputs > 127:
            raise InvalidEOF(f"Invalid number of inputs for type {i}")

        if len(code) < counter + 1:
            raise InvalidEOF(f"Number of outputs not specified for type {i}")
        num_outputs = code[counter]
        counter += 1
        if num_outputs > 128:
            raise InvalidEOF(f"Invalid number of outputs for type {i}")

        if len(code) < counter + 2:
            raise InvalidEOF(f"Max stack height not specified for type {i}")
        max_stack_height = Uint.from_be_bytes(code[counter : counter + 2])
        counter += 2
        if max_stack_height > 1023:
            raise InvalidEOF(f"Invalid max stack height for type {i}")

    total_code_size = sum(eof_header.code_sizes)
    if len(code) < counter + total_code_size:
        raise InvalidEOF("Code section size does not match header")
    counter += total_code_size

    total_container_size = (
        sum(eof_header.container_sizes) if eof_header.container_sizes else 0
    )
    if len(code) < counter + total_container_size:
        raise InvalidEOF("Container section size does not match header")
    counter += total_container_size

    # Check for stray bytes after the data section
    if len(code) > counter + eof_header.data_size:
        raise InvalidEOF("Stray bytes found after data section")


def get_valid_jump_destinations(code: bytes) -> Set[int]:
    """
    Get the valid jump destinations for the code. The immediate bytes
    of the PUSH, RJUMP, RJUMPI, RJUMPV opcodes are invalid as jump
    destinations.

    Parameters
    ----------
    code : bytes
        The code section of the EOF container.

    Returns
    -------
    valid_jump_destinations : Set[int]
        The valid jump destinations in the code.
    """
    counter = 0
    valid_jump_destinations = set()
    while counter < len(code):
        try:
            opcode = get_opcode(code[counter], EOF.EOF1)
        except ValueError:
            raise InvalidEOF("Invalid opcode in code section")
        valid_jump_destinations.add(counter)

        counter += 1

        if (
            opcode.value >= Ops.PUSH1.value
            and opcode.value <= Ops.PUSH32.value
        ):
            push_data_size = opcode.value - Ops.PUSH1.value + 1
            if len(code) < counter + push_data_size:
                raise InvalidEOF("Push data missing")
            counter += push_data_size
            continue

        if opcode in (Ops.RJUMP, Ops.RJUMPI):
            if len(code) < counter + 2:
                raise InvalidEOF("Relative jump offset missing")
            counter += 2
            continue

        if opcode == Ops.RJUMPV:
            if len(code) < counter + 1:
                raise InvalidEOF("max_index missing for RJUMPV")
            max_index = code[counter]
            num_relative_indices = max_index + 1
            counter += 1

            for _ in range(num_relative_indices):
                if len(code) < counter + 2:
                    raise InvalidEOF("Relative jump indices missing")
                counter += 2
            continue

    return valid_jump_destinations


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
    valid_jump_destinations = get_valid_jump_destinations(code)

    for counter in valid_jump_destinations:
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
                or jump_destination not in valid_jump_destinations
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
                    or jump_destination not in valid_jump_destinations
                ):
                    raise InvalidEOF("Invalid jump destination")


def validate_eof_code(code: bytes, eof_header: EOFHeader) -> None:
    """
    Validate the code section of the EOF container.

    Parameters
    ----------
    code : bytes
        The code section to validate.
    eof_header : EOFHeader
        The header of the EOF container.

    Raises
    ------
    InvalidEOF
        If the code section is invalid.
    """
    code_start = eof_header.header_end_index + eof_header.type_size
    counter = code_start

    for code_size in eof_header.code_sizes:
        validate_code_section(code[counter : counter + code_size])
        counter += code_size


def validate_eof_container(code: bytes) -> None:
    """
    Validate the Ethereum Object Format (EOF) container.

    Parameters
    ----------
    code : bytes
        The EOF container to validate.

    Raises
    ------
    InvalidEOF
        If the EOF container is invalid.
    """
    # Validate the magic
    if len(code) < EOF_MAGIC_LENGTH or code[:EOF_MAGIC_LENGTH] != EOF_MAGIC:
        raise InvalidEOF("Invalid magic")

    if len(code) < EOF_MAGIC_LENGTH + 1:
        raise InvalidEOF("EOF version not specified")
    elif code[EOF_MAGIC_LENGTH] != 1:
        raise InvalidEOF("Invalid EOF version")

    eof_header = validate_header(code)

    validate_body(code, eof_header)

    validate_eof_code(code, eof_header)
