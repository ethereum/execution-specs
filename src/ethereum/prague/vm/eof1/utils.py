"""
Utility functions for EOF containers.
"""
from typing import Tuple

from ethereum.base_types import Uint

from .. import EOF_MAGIC, EofMetadata
from ..exceptions import InvalidEof


def metadata_from_container(
    container: bytes,
    validate: bool,
    is_deploy_container: bool,
    is_init_container: bool,
) -> EofMetadata:
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
    is_deploy_container : bool
        Whether the container is a deploy container for EOFCREATE/ create
        transactions.
    is_init_container : bool
        Whether the container is an init container for EOFCREATE/
        create transactions.

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

    num_container_sections = Uint(0)
    container_sizes = []

    if container[counter] == 3:
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

    container_section_contents = []
    if num_container_sections > 0:
        if validate and len(container) < counter + sum(container_sizes):
            raise InvalidEof("Container section size does not match header")
        for container_size in container_sizes:
            container_section_contents.append(
                container[counter : counter + container_size]
            )
            counter += container_size

    if (
        validate
        and not is_deploy_container
        and len(container) < counter + data_size
    ):
        raise InvalidEof("Data section size does not match header")

    if (
        validate
        and is_init_container
        and len(container) != counter + data_size
    ):
        raise InvalidEof("invalid init container data size")

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


def container_from_metadata(eof_metadata: EofMetadata) -> bytes:
    """
    Build the EOF container from the metadata.

    Parameters
    ----------
    eof_metadata : EofMetadata
        The metadata of the EOF container.

    Returns
    -------
    container : bytes
        The EOF container.
    """
    # Add the magic bytes
    container = EOF_MAGIC

    # Add EOF Version
    container += b"\x01"

    # Add the kind type
    container += b"\x01"
    container += eof_metadata.type_size.to_bytes(2, "big")

    # Add the kind code
    container += b"\x02"
    container += eof_metadata.num_code_sections.to_bytes(2, "big")
    for code_size in eof_metadata.code_sizes:
        container += code_size.to_bytes(2, "big")

    # Add the kind container
    if eof_metadata.num_container_sections > 0:
        container += b"\x03"
        container += eof_metadata.num_container_sections.to_be_bytes()
        for container_size in eof_metadata.container_sizes:
            container += container_size.to_bytes(2, "big")

    # Add the kind data
    container += b"\x04"
    container += eof_metadata.data_size.to_bytes(2, "big")

    # Add the terminator
    container += b"\x00"

    # Add the body
    # Add the type section
    for type_section in eof_metadata.type_section_contents:
        container += type_section

    # Add the code section
    for code_section in eof_metadata.code_section_contents:
        container += code_section

    # Add the container section
    if eof_metadata.num_container_sections > 0:
        for container_section in eof_metadata.container_section_contents:
            container += container_section

    # Add the data section
    container += eof_metadata.data_section_contents

    return container


def parse_create_tx_call_data(data: bytes) -> Tuple[bytes, bytes]:
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
    # TODO: Global import this after re-factor
    from ..eof import validate_body, validate_eof_code

    eof_metadata = metadata_from_container(
        data, validate=True, is_deploy_container=False, is_init_container=False
    )

    validate_body(eof_metadata)

    _, has_stop, has_return = validate_eof_code(eof_metadata)

    if has_stop or has_return:
        raise InvalidEof("Init container has STOP/RETURN")

    container_size = (
        eof_metadata.body_start_index
        + eof_metadata.type_size
        + sum(eof_metadata.code_sizes)
        + sum(eof_metadata.container_sizes)
        + eof_metadata.data_size
    )

    return data[:container_size], data[container_size:]
