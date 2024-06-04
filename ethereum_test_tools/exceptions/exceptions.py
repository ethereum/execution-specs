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

    TYPE_NOT_SUPPORTED = auto()
    """
    Transaction type is not supported on this chain configuration.
    """
    SENDER_NOT_EOA = auto()
    """
    Transaction is coming from address that is not exist anymore.
    """
    ADDRESS_TOO_SHORT = auto()
    """
    Transaction `to` is not allowed to be less than 20 bytes.
    """
    ADDRESS_TOO_LONG = auto()
    """
    Transaction `to` is not allowed to be more than 20 bytes.
    """
    NONCE_MISMATCH_TOO_HIGH = auto()
    """
    Transaction nonce > sender.nonce.
    """
    NONCE_MISMATCH_TOO_LOW = auto()
    """
    Transaction nonce < sender.nonce.
    """
    NONCE_TOO_BIG = auto()
    """
    Transaction `nonce` is not allowed to be max_uint64 - 1 (this is probably TransactionTest).
    """
    NONCE_IS_MAX = auto()
    """
    Transaction `nonce` is not allowed to be max_uint64 - 1 (this is StateTests).
    """
    NONCE_OVERFLOW = auto()
    """
    Transaction `nonce` is not allowed to be more than uint64.
    """
    GASLIMIT_OVERFLOW = auto()
    """
    Transaction gaslimit exceeds 2^64-1 maximum value.
    """
    VALUE_OVERFLOW = auto()
    """
    Transaction value exceeds 2^256-1 maximum value.
    """
    GASPRICE_OVERFLOW = auto()
    """
    Transaction gasPrice exceeds 2^256-1 maximum value.
    """
    GASLIMIT_PRICE_PRODUCT_OVERFLOW = auto()
    """
    Transaction gasPrice * gasLimit exceeds 2^256-1 maximum value.
    """
    INVALID_SIGNATURE_VRS = auto()
    """
    Invalid transaction v, r, s values.
    """
    RLP_INVALID_SIGNATURE_R = auto()
    """
    Error reading transaction signature R value.
    """
    RLP_INVALID_SIGNATURE_S = auto()
    """
    Error reading transaction signature S value.
    """
    RLP_LEADING_ZEROS_GASLIMIT = auto()
    """
    Error reading transaction gaslimit field RLP.
    """
    RLP_LEADING_ZEROS_GASPRICE = auto()
    """
    Error reading transaction gasprice field RLP.
    """
    RLP_LEADING_ZEROS_VALUE = auto()
    """
    Error reading transaction value field RLP.
    """
    RLP_LEADING_ZEROS_NONCE = auto()
    """
    Error reading transaction nonce field RLP.
    """
    RLP_LEADING_ZEROS_R = auto()
    """
    Error reading transaction signature R field RLP.
    """
    RLP_LEADING_ZEROS_S = auto()
    """
    Error reading transaction signature S field RLP.
    """
    RLP_LEADING_ZEROS_V = auto()
    """
    Error reading transaction signature V field RLP.
    """
    RLP_LEADING_ZEROS_BASEFEE = auto()
    """
    Error reading transaction basefee field RLP.
    """
    RLP_LEADING_ZEROS_PRIORITY_FEE = auto()
    """
    Error reading transaction priority fee field RLP.
    """
    RLP_LEADING_ZEROS_DATA_SIZE = auto()
    """
    Error reading transaction data field RLP, (rlp field length has leading zeros).
    """
    RLP_LEADING_ZEROS_NONCE_SIZE = auto()
    """
    Error reading transaction nonce field RLP, (rlp field length has leading zeros).
    """
    RLP_TOO_FEW_ELEMENTS = auto()
    """
    Error reading transaction RLP, structure has too few elements than expected.
    """
    RLP_TOO_MANY_ELEMENTS = auto()
    """
    Error reading transaction RLP, structure has too many elements than expected.
    """
    RLP_ERROR_EOF = auto()
    """
    Error reading transaction RLP, rlp stream unexpectedly finished.
    """
    RLP_ERROR_SIZE = auto()
    """
    Error reading transaction RLP, rlp size is invalid.
    """
    RLP_ERROR_SIZE_LEADING_ZEROS = auto()
    """
    Error reading transaction RLP, field size has leading zeros.
    """
    INVALID_CHAINID = auto()
    """
    Transaction chain id encoding is incorrect.
    """
    RLP_INVALID_DATA = auto()
    """
    Transaction data field is invalid rlp.
    """
    RLP_INVALID_GASLIMIT = auto()
    """
    Transaction gaslimit field is invalid rlp.
    """
    RLP_INVALID_NONCE = auto()
    """
    Transaction nonce field is invalid rlp.
    """
    RLP_INVALID_TO = auto()
    """
    Transaction to field is invalid rlp.
    """
    RLP_INVALID_ACCESS_LIST_ADDRESS_TOO_LONG = auto()
    """
    Transaction access list address is > 20 bytes.
    """
    RLP_INVALID_ACCESS_LIST_ADDRESS_TOO_SHORT = auto()
    """
    Transaction access list address is < 20 bytes.
    """
    RLP_INVALID_ACCESS_LIST_STORAGE_TOO_LONG = auto()
    """
    Transaction access list storage hash > 32 bytes.
    """
    RLP_INVALID_ACCESS_LIST_STORAGE_TOO_SHORT = auto()
    """
    Transaction access list storage hash < 32 bytes.
    """
    RLP_INVALID_HEADER = auto()
    """
    Transaction failed to read from RLP as rlp header is invalid.
    """
    RLP_INVALID_VALUE = auto()
    """
    Transaction value field is invalid rlp/structure.
    """
    EC_RECOVERY_FAIL = auto()
    """
    Transaction has correct signature, but ec recovery failed.
    """
    INSUFFICIENT_ACCOUNT_FUNDS = auto()
    """
    Transaction's sender does not have enough funds to pay for the transaction.
    """
    INSUFFICIENT_MAX_FEE_PER_GAS = auto()
    """
    Transaction's max-fee-per-gas is lower than the block base-fee.
    """
    PRIORITY_OVERFLOW = auto()
    """
    Transaction's max-priority-fee-per-gas is exceeds 2^256-1 maximum value.
    """
    PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS = auto()
    """
    Transaction's max-priority-fee-per-gas is greater than the max-fee-per-gas.
    """
    PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS_2 = auto()
    """
    Transaction's max-priority-fee-per-gas is greater than the max-fee-per-gas (TransactionTests).
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
    GAS_ALLOWANCE_EXCEEDED = auto()
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

    TOO_MANY_UNCLES = auto()
    """
    Block declares too many uncles over the allowed limit.
    """
    UNCLE_IN_CHAIN = auto()
    """
    Block declares uncle header that is already imported into chain.
    """
    UNCLE_IS_ANCESTOR = auto()
    """
    Block declares uncle header that is directly a parent of this block.
    """
    UNCLE_IS_BROTHER = auto()
    """
    Block declares two similar uncle headers.
    """
    UNCLE_PARENT_INCORRECT = auto()
    """
    Block declares uncle header that is an outdated block to be an uncle.
    """
    EXTRA_DATA_TOO_BIG = auto()
    """
    Block header's extra data >32 bytes.
    """
    EXTRA_DATA_INVALID_DAO = auto()
    """
    Block header's extra data after dao fork must be a fixed pre defined hash.
    """
    UNKNOWN_PARENT = auto()
    """
    Block header's parent hash does not correspond to any of existing blocks on chain.
    """
    UNCLE_UNKNOWN_PARENT = auto()
    """
    Uncle header's parent hash does not correspond to any of existing blocks on chain.
    """
    UNKNOWN_PARENT_ZERO = auto()
    """
    Block header's parent hash is zero hash.
    """
    GASLIMIT_TOO_BIG = auto()
    """
    Block header's gas limit > 0x7fffffffffffffff.
    """
    INVALID_BLOCK_NUMBER = auto()
    """
    Block header's number != parent header's number + 1.
    """
    INVALID_BLOCK_TIMESTAMP_OLDER_THAN_PARENT = auto()
    """
    Block header's timestamp <= parent header's timestamp.
    """
    INVALID_DIFFICULTY = auto()
    """
    Block header's difficulty does not match the difficulty formula calculated from previous block.
    """
    INVALID_LOG_BLOOM = auto()
    """
    Block header's logs bloom hash does not match the actually computed log bloom.
    """
    INVALID_STATE_ROOT = auto()
    """
    Block header's state root hash does not match the actually computed hash of the state.
    """
    INVALID_RECEIPTS_ROOT = auto()
    """
    Block header's receipts root hash does not match the actually computed hash of receipts.
    """
    INVALID_TRANSACTIONS_ROOT = auto()
    """
    Block header's transactions root hash does not match the actually computed hash of tx tree.
    """
    INVALID_UNCLES_HASH = auto()
    """
    Block header's uncle hash does not match the actually computed hash of block's uncles.
    """
    GAS_USED_OVERFLOW = auto()
    """
    Block transactions consume more gas than block header allow.
    """
    INVALID_GASLIMIT = auto()
    """
    Block header's gas limit does not match the gas limit formula calculated from previous block.
    """
    INVALID_BASEFEE_PER_GAS = auto()
    """
    Block header's base_fee_per_gas field is calculated incorrect.
    """
    INVALID_GAS_USED = auto()
    """
    Block header's actual gas used does not match the provided header's value
    """
    INVALID_WITHDRAWALS_ROOT = auto()
    """
    Block header's withdrawals root does not match calculated withdrawals root.
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
    Block's rlp encoding is valid but ethereum structures in it are invalid.
    """
    RLP_WITHDRAWALS_NOT_READ = auto()
    """
    Block's rlp encoding is missing withdrawals.
    """
    RLP_INVALID_FIELD_OVERFLOW_64 = auto()
    """
    One of block's fields rlp is overflow 2**64 value.
    """
    RLP_INVALID_ADDRESS = auto()
    """
    Block withdrawals address is rlp of invalid address != 20 bytes.
    """
    INVALID_REQUESTS = auto()
    """
    Block's requests are invalid.
    """
    IMPORT_IMPOSSIBLE_LEGACY = auto()
    """
    Legacy block import is impossible in this chain configuration.
    """
    IMPORT_IMPOSSIBLE_LEGACY_WRONG_PARENT = auto()
    """
    Legacy block import is impossible, trying to import on top of a block that is not legacy.
    """
    IMPORT_IMPOSSIBLE_LONDON_WRONG_PARENT = auto()
    """
    Trying to import london (basefee) block on top of block that is not 1559.
    """
    IMPORT_IMPOSSIBLE_PARIS_WRONG_POW = auto()
    """
    Trying to import paris(merge) block with PoW enabled.
    """
    IMPORT_IMPOSSIBLE_PARIS_WRONG_POS = auto()
    """
    Trying to import paris(merge) block with PoS enabled before TTD is reached.
    """
    IMPORT_IMPOSSIBLE_LONDON_OVER_PARIS = auto()
    """
    Trying to import london looking block over paris network (POS).
    """
    IMPORT_IMPOSSIBLE_PARIS_OVER_SHANGHAI = auto()
    """
    Trying to import paris block on top of shanghai block.
    """
    IMPORT_IMPOSSIBLE_SHANGHAI = auto()
    """
    Shanghai block import is impossible in this chain configuration.
    """
    IMPORT_IMPOSSIBLE_UNCLES_OVER_PARIS = auto()
    """
    Trying to import a block after paris fork that has not empty uncles hash.
    """
    IMPORT_IMPOSSIBLE_DIFFICULTY_OVER_PARIS = auto()
    """
    Trying to import a block after paris fork that has difficulty != 0.
    """


@unique
class EOFException(ExceptionBase):
    """
    Exception raised when an EOF container is invalid.
    """

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
    MAX_STACK_HEIGHT_ABOVE_LIMIT = auto()
    """
    EOF container's specified max stack height is above the limit.
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
    INVALID_MAX_STACK_HEIGHT = auto()
    """
    EOF container section's specified max stack height does not match the actual stack height.
    """
    INVALID_DATALOADN_INDEX = auto()
    """
    A DATALOADN instruction has out-of-bounds index for the data section.
    """
    TRUNCATED_INSTRUCTION = auto()
    """
    EOF container's code section has truncated instruction.
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
