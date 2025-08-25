"""EOF Exceptions."""

from enum import auto, unique

from .base import ExceptionBase


@unique
class EOFException(ExceptionBase):
    """Exception raised when an EOF container is invalid."""

    DEFAULT_EXCEPTION = auto()
    """
    Expect some exception, not yet known.
    """

    UNDEFINED_EXCEPTION = auto()
    """
    Indicates that exception string is not mapped to an exception enum.
    """

    UNDEFINED_INSTRUCTION = auto()
    """
    EOF container has undefined instruction in it's body code.
    """

    UNKNOWN_VERSION = auto()
    """
    EOF container has an unknown version.
    """
    INCOMPLETE_MAGIC = auto()
    """
    EOF container has not enough bytes to read magic.
    """
    INVALID_MAGIC = auto()
    """
    EOF container has not allowed magic version byte.
    """
    INVALID_VERSION = auto()
    """
    EOF container version bytes mismatch.
    """
    INVALID_NON_RETURNING_FLAG = auto()
    """
    EOF container's section has non-returning flag set incorrectly.
    """
    INVALID_RJUMP_DESTINATION = auto()
    """
    Code has RJUMP instruction with invalid parameters.
    """
    MISSING_TYPE_HEADER = auto()
    """
    EOF container missing types section.
    """
    INVALID_TYPE_SECTION_SIZE = auto()
    """
    EOF container types section has wrong size.
    """
    INVALID_TYPE_BODY = auto()
    """
    EOF container types body section bytes are wrong.
    """
    MISSING_CODE_HEADER = auto()
    """
    EOF container missing code section.
    """
    INVALID_CODE_SECTION = auto()
    """
    EOF container code section bytes are incorrect.
    """
    INCOMPLETE_CODE_HEADER = auto()
    """
    EOF container code header missing bytes.
    """
    INCOMPLETE_DATA_HEADER = auto()
    """
    EOF container data header missing bytes.
    """
    ZERO_SECTION_SIZE = auto()
    """
    EOF container data header construction is wrong.
    """
    MISSING_DATA_SECTION = auto()
    """
    EOF container missing data section
    """
    INCOMPLETE_CONTAINER = auto()
    """
    EOF container bytes are incomplete.
    """
    INVALID_SECTION_BODIES_SIZE = auto()
    """
    Sections bodies does not match sections headers.
    """
    TRAILING_BYTES = auto()
    """
    EOF container has bytes beyond data section.
    """
    MISSING_TERMINATOR = auto()
    """
    EOF container missing terminator bytes between header and body.
    """
    MISSING_HEADERS_TERMINATOR = auto()
    """
    Some type of another exception about missing headers terminator.
    """
    INVALID_FIRST_SECTION_TYPE = auto()
    """
    EOF container header does not have types section first.
    """
    INCOMPLETE_SECTION_NUMBER = auto()
    """
    EOF container header has section that is missing declaration bytes.
    """
    INCOMPLETE_SECTION_SIZE = auto()
    """
    EOF container header has section that is defined incorrectly.
    """
    TOO_MANY_CODE_SECTIONS = auto()
    """
    EOF container header has too many code sections.
    """
    MISSING_STOP_OPCODE = auto()
    """
    EOF container's code missing STOP bytecode at it's end.
    """
    INPUTS_OUTPUTS_NUM_ABOVE_LIMIT = auto()
    """
    EOF container code section inputs/outputs number is above the limit
    """
    UNREACHABLE_INSTRUCTIONS = auto()
    """
    EOF container's code have instructions that are unreachable.
    """
    UNREACHABLE_CODE_SECTIONS = auto()
    """
    EOF container's body have code sections that are unreachable.
    """
    STACK_UNDERFLOW = auto()
    """
    EOF container's code produces an stack underflow.
    """
    STACK_OVERFLOW = auto()
    """
    EOF container's code produces an stack overflow.
    """
    STACK_HEIGHT_MISMATCH = auto()
    """
    EOF container section stack height mismatch.
    """
    MAX_STACK_INCREASE_ABOVE_LIMIT = auto()
    """
    EOF container's specified max stack increase is above the limit.
    """
    STACK_HIGHER_THAN_OUTPUTS = auto()
    """
    EOF container section stack height is higher than the outputs.
    when returning
    """
    JUMPF_DESTINATION_INCOMPATIBLE_OUTPUTS = auto()
    """
    EOF container section JUMPF's to a destination section with incompatible outputs.
    """
    INVALID_MAX_STACK_INCREASE = auto()
    """
    EOF container section's specified max stack increase does not match the actual stack height.
    """
    INVALID_DATALOADN_INDEX = auto()
    """
    A DATALOADN instruction has out-of-bounds index for the data section.
    """
    TRUNCATED_INSTRUCTION = auto()
    """
    EOF container's code section has truncated instruction.
    """
    TOPLEVEL_CONTAINER_TRUNCATED = auto()
    """
    Top-level EOF container has data section truncated
    """
    ORPHAN_SUBCONTAINER = auto()
    """
    EOF container has an unreferenced subcontainer.
    '"""
    CONTAINER_SIZE_ABOVE_LIMIT = auto()
    """
    EOF container is above size limit
    """
    INVALID_CONTAINER_SECTION_INDEX = auto()
    """
    Instruction references container section that does not exist.
    """
    INCOMPATIBLE_CONTAINER_KIND = auto()
    """
    Incompatible instruction found in a container of a specific kind.
    """
    AMBIGUOUS_CONTAINER_KIND = auto()
    """
    The kind of a sub-container cannot be uniquely deduced.
    """
    TOO_MANY_CONTAINERS = auto()
    """
    EOF container header has too many sub-containers.
    """
    INVALID_CODE_SECTION_INDEX = auto()
    """
    CALLF Operation refers to a non-existent code section
    """
    UNEXPECTED_HEADER_KIND = auto()
    """
    Header parsing encountered a section kind it wasn't expecting
    """
    CALLF_TO_NON_RETURNING = auto()
    """
    CALLF instruction targeting a non-returning code section
    """
    EOFCREATE_WITH_TRUNCATED_CONTAINER = auto()
    """
    EOFCREATE with truncated container
    """
