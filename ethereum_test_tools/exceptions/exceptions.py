"""
Exceptions for invalid execution.
"""

from enum import Enum, auto, unique
from typing import Annotated, Any, List

from pydantic import BeforeValidator, GetCoreSchemaHandler, PlainSerializer
from pydantic_core.core_schema import (
    PlainValidatorFunctionSchema,
    no_info_plain_validator_function,
    to_string_ser_schema,
)


class ExceptionBase(Enum):
    """
    Base class for exceptions.
    """

    @staticmethod
    def __get_pydantic_core_schema__(
        source_type: Any, handler: GetCoreSchemaHandler
    ) -> PlainValidatorFunctionSchema:
        """
        Calls the class constructor without info and appends the serialization schema.
        """
        return no_info_plain_validator_function(
            source_type,
            serialization=to_string_ser_schema(),
        )

    def __contains__(self, exception) -> bool:
        """
        Checks if provided exception is equal to this
        """
        return self == exception

    def __str__(self) -> str:
        """
        Returns the string representation of the exception
        """
        return f"{self.__class__.__name__}.{self.name}"


def to_pipe_str(value: Any) -> str:
    """
    Single pipe-separated string representation of an exception list.

    Obtain a deterministic ordering by ordering using the exception string
    representations.
    """
    if isinstance(value, list):
        return "|".join(str(exception) for exception in value)
    return str(value)


def create_exception_from_str(exception_str: str) -> ExceptionBase:
    """
    Create an exception instance from its string representation.
    """
    class_name, enum_name = exception_str.split(".")
    exception_class = globals().get(class_name, None)

    if exception_class and issubclass(exception_class, ExceptionBase):
        enum_value = getattr(exception_class, enum_name, None)
        if enum_value and enum_value in exception_class:
            return exception_class(enum_value)
        else:
            raise ValueError(f"No such enum in class: {exception_str}")
    else:
        raise ValueError(f"No such exception class: {class_name}")


def from_pipe_str(value: Any) -> ExceptionBase | List[ExceptionBase]:
    """
    Parses a single string as a pipe separated list into enum exceptions.
    """
    if isinstance(value, str):
        exception_list = [create_exception_from_str(v) for v in value.split("|")]
        if len(exception_list) == 1:
            return exception_list[0]
        return exception_list
    return value


@unique
class TransactionException(ExceptionBase):
    """
    Exception raised when a transaction is invalid, and thus cannot be executed.

    If a transaction with any of these exceptions is included in a block, the block is invalid.
    """

    INSUFFICIENT_ACCOUNT_FUNDS = auto()
    """
    Transaction's sender does not have enough funds to pay for the transaction.
    """
    INSUFFICIENT_MAX_FEE_PER_GAS = auto()
    """
    Transaction's max-fee-per-gas is lower than the block base-fee.
    """
    PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS = auto()
    """
    Transaction's max-priority-fee-per-gas is greater than the max-fee-per-gas.
    """
    INSUFFICIENT_MAX_FEE_PER_BLOB_GAS = auto()
    """
    Transaction's max-fee-per-blob-gas is lower than the block's blob-gas price.
    """
    INTRINSIC_GAS_TOO_LOW = auto()
    """
    Transaction's gas limit is too low.
    """
    INITCODE_SIZE_EXCEEDED = auto()
    """
    Transaction's initcode for a contract-creating transaction is too large.
    """
    TYPE_3_TX_PRE_FORK = auto()
    """
    Transaction type 3 included before activation fork.
    """
    TYPE_3_TX_ZERO_BLOBS_PRE_FORK = auto()
    """
    Transaction type 3, with zero blobs, included before activation fork.
    """
    TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH = auto()
    """
    Transaction contains a blob versioned hash with an invalid version.
    """
    TYPE_3_TX_WITH_FULL_BLOBS = auto()
    """
    Transaction contains full blobs (network-version of the transaction).
    """
    TYPE_3_TX_BLOB_COUNT_EXCEEDED = auto()
    """
    Transaction contains too many blob versioned hashes.
    """
    TYPE_3_TX_CONTRACT_CREATION = auto()
    """
    Transaction is a type 3 transaction and has an empty `to`.
    """
    TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED = auto()
    """
    Transaction causes block to go over blob gas limit.
    """
    TYPE_3_TX_ZERO_BLOBS = auto()
    """
    Transaction is type 3, but has no blobs.
    """


@unique
class BlockException(ExceptionBase):
    """
    Exception raised when a block is invalid, but not due to a transaction.

    E.g. all transactions in the block are valid, and can be applied to the state, but the
    block header contains an invalid field.
    """

    INCORRECT_BLOCK_FORMAT = auto()
    """
    Block's format is incorrect, contains invalid fields, is missing fields, or contains fields of
    a fork that is not active yet.
    """
    BLOB_GAS_USED_ABOVE_LIMIT = auto()
    """
    Block's blob gas used in header is above the limit.
    """
    INCORRECT_BLOB_GAS_USED = auto()
    """
    Block's blob gas used in header is incorrect.
    """
    INCORRECT_EXCESS_BLOB_GAS = auto()
    """
    Block's excess blob gas in header is incorrect.
    """
    RLP_STRUCTURES_ENCODING = auto()
    """
    Block's rlp encoding is valid but ethereum structures in it are invalid
    """


@unique
class EOFException(ExceptionBase):
    """
    Exception raised when an EOF container is invalid
    """

    DEFAULT_EXCEPTION = auto()
    """
    Expect some exception, not yet known
    """

    UNDEFINED_EXCEPTION = auto()
    """
    Indicates that exception string is not mapped to an exception enum
    """

    UNDEFINED_INSTRUCTION = auto()
    """
    EOF container has undefined instruction in it's body code
    """

    UNKNOWN_VERSION = auto()
    """
    EOF container has an unknown version
    """
    INCOMPLETE_MAGIC = auto()
    """
    EOF container has not enough bytes to read magic
    """
    INVALID_MAGIC = auto()
    """
    EOF container has not allowed magic version byte
    """
    INVALID_VERSION = auto()
    """
    EOF container version bytes mismatch
    """
    INVALID_RJUMP_DESTINATION = auto()
    """
    Code has RJUMP instruction with invalid parameters
    """
    MISSING_TYPE_HEADER = auto()
    """
    EOF container missing types section
    """
    INVALID_TYPE_SECTION_SIZE = auto()
    """
    EOF container types section has wrong size
    """
    INVALID_TYPE_BODY = auto()
    """
    EOF container types body section bytes are wrong
    """
    MISSING_CODE_HEADER = auto()
    """
    EOF container missing code section
    """
    INVALID_CODE_SECTION = auto()
    """
    EOF container code section bytes are incorrect
    """
    INCOMPLETE_CODE_HEADER = auto()
    """
    EOF container code header missing bytes
    """
    INCOMPLETE_DATA_HEADER = auto()
    """
    EOF container data header missing bytes
    """
    ZERO_SECTION_SIZE = auto()
    """
    EOF container data header construction is wrong
    """
    INCOMPLETE_CONTAINER = auto()
    """
    EOF container bytes are incomplete
    """
    INVALID_SECTION_BODIES_SIZE = auto()
    """
    Sections bodies does not match sections headers
    """
    TRAILING_BYTES = auto()
    """
    EOF container has bytes beyond data section
    """
    MISSING_TERMINATOR = auto()
    """
    EOF container missing terminator bytes between header and body
    """
    MISSING_HEADERS_TERMINATOR = auto()
    """
    Some type of another exception about missing headers terminator
    """
    INVALID_FIRST_SECTION_TYPE = auto()
    """
    EOF container header does not have types section first
    """
    INCOMPLETE_SECTION_NUMBER = auto()
    """
    EOF container header has section that is missing declaration bytes
    """
    INCOMPLETE_SECTION_SIZE = auto()
    """
    EOF container header has section that is defined incorrectly
    """
    TOO_MANY_CODE_SECTIONS = auto()
    """
    EOF container header has too many code sections
    """
    MISSING_STOP_OPCODE = auto()
    """
    EOF container's code missing STOP bytecode at it's end
    """
    UNREACHABLE_INSTRUCTIONS = auto()
    """
    EOF container's code have instructions that are unreachable
    """
    UNREACHABLE_CODE_SECTIONS = auto()
    """
    EOF container's body have code sections that are unreachable
    """
    INVALID_DATALOADN_INDEX = auto()
    """
    A DATALOADN instruction has out-of-bounds index for the data section
    """


"""
Pydantic Annotated Types
"""

ExceptionInstanceOrList = Annotated[
    TransactionException | BlockException | List[TransactionException | BlockException],
    BeforeValidator(from_pipe_str),
    PlainSerializer(to_pipe_str),
]

TransactionExceptionInstanceOrList = Annotated[
    TransactionException | List[TransactionException],
    BeforeValidator(from_pipe_str),
    PlainSerializer(to_pipe_str),
]

BlockExceptionInstanceOrList = Annotated[
    BlockException | List[BlockException],
    BeforeValidator(from_pipe_str),
    PlainSerializer(to_pipe_str),
]
