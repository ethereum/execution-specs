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

from . import EOF_MAGIC, EOF_MAGIC_LENGTH, MAX_CODE_SIZE, Eof, EofMetadata
from .exceptions import InvalidEof
from .instructions import (
    OPCODES_INVALID_IN_EOF1,
    OPCODES_INVALID_IN_LEGACY,
    Ops,
)


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


def get_valid_opcode_positions(code: bytes) -> Set[int]:
    """
    Get the positions of the valid opcodes for the code. These will
    also be the positions within the code to which, jumps can be
    performed. The immediate bytes of the PUSH, RJUMP, RJUMPI,
    RJUMPV opcodes are invalid as jump destinations.

    Parameters
    ----------
    code : bytes
        The code section of the EOF container.

    Returns
    -------
    valid_opcode_positions : Set[int]
        The valid jump destinations in the code.
    """
    counter = 0
    valid_opcode_positions = set()
    while counter < len(code):
        try:
            opcode = map_int_to_op(code[counter], Eof.EOF1)
        except ValueError:
            raise InvalidEof("Invalid opcode in code section")
        valid_opcode_positions.add(counter)

        counter += 1

        if (
            opcode.value >= Ops.PUSH1.value
            and opcode.value <= Ops.PUSH32.value
        ):
            push_data_size = opcode.value - Ops.PUSH1.value + 1
            if len(code) < counter + push_data_size:
                raise InvalidEof("Push data missing")
            counter += push_data_size

        elif opcode in (Ops.RJUMP, Ops.RJUMPI):
            if len(code) < counter + 2:
                raise InvalidEof("Relative jump offset missing")
            counter += 2

        elif opcode == Ops.RJUMPV:
            if len(code) < counter + 1:
                raise InvalidEof("max_index missing for RJUMPV")
            max_index = code[counter]
            num_relative_indices = max_index + 1
            counter += 1

            for _ in range(num_relative_indices):
                if len(code) < counter + 2:
                    raise InvalidEof("Relative jump indices missing")
                counter += 2
        elif opcode == Ops.CALLF:
            if len(code) < counter + 2:
                raise InvalidEof("CALLF target code section index missing")
            counter += 2
        elif opcode == Ops.DATALOADN:
            if len(code) < counter + 2:
                raise InvalidEof("DATALOADN offset missing")
            counter += 2

    return valid_opcode_positions


def validate_code_section(
    eof_meta: EofMetadata,
    code_section_index: Uint,
    reached_code_sections: Set[Uint],
) -> None:
    """
    Validate a code section of the EOF container.

    Parameters
    ----------
    eof_meta : EofMetadata
        The metadata of the EOF container.
    code_section_index : Uint
        The index of the code section to validate.
    reached_code_sections : Set[Uint]
        The code sections that have been reached.

    Raises
    ------
    InvalidEof
        If the code section is invalid.
    """
    code = eof_meta.code_section_contents[code_section_index]
    valid_opcode_positions = get_valid_opcode_positions(code)

    for counter in valid_opcode_positions:
        opcode = map_int_to_op(code[counter], Eof.EOF1)

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
                or jump_destination not in valid_opcode_positions
            ):
                raise InvalidEof("Invalid jump destination")

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
                    or jump_destination not in valid_opcode_positions
                ):
                    raise InvalidEof("Invalid jump destination")

        elif opcode == Ops.CALLF:
            target_section_index = Uint.from_be_bytes(
                code[counter + 1 : counter + 3],
            )
            reached_code_sections.add(target_section_index)
            if target_section_index >= eof_meta.num_code_sections:
                raise InvalidEof("Invalid target code section index")
        elif opcode == Ops.RETF:
            if code_section_index == 0:
                raise InvalidEof("First code section cannot return")
        elif opcode == Ops.DATALOADN:
            offset = Uint.from_be_bytes(code[counter + 1 : counter + 3])
            if offset >= eof_meta.data_size:
                raise InvalidEof("Invalid DATALOADN offset")


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
    reached_code_sections = {Uint(0)}
    for code_section_index in range(eof_meta.num_code_sections):
        validate_code_section(
            eof_meta, Uint(code_section_index), reached_code_sections
        )

    for i in range(eof_meta.num_code_sections):
        if i not in reached_code_sections:
            raise InvalidEof(f"Code section {i} not reachable")


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
