"""
Exceptions for invalid execution.
"""

from enum import Enum, auto, unique
from typing import List, Union


class ExceptionList(list):
    """
    A list of exceptions.
    """

    def __init__(self, *exceptions: "ExceptionBase") -> None:
        """
        Create a new ExceptionList.
        """
        exceptions_set: List[ExceptionBase] = []
        for exception in exceptions:
            if not isinstance(exception, ExceptionBase):
                raise TypeError(f"Expected ExceptionBase, got {type(exception)}")
            if exception not in exceptions_set:
                exceptions_set.append(exception)
        super().__init__(exceptions_set)

    def __or__(self, other: Union["ExceptionBase", "ExceptionList"]) -> "ExceptionList":
        """
        Combine two ExceptionLists.
        """
        if isinstance(other, list):
            return ExceptionList(*(self + other))
        return ExceptionList(*(self + [other]))

    def __str__(self) -> str:
        """
        String representation of the ExceptionList.
        """
        return "|".join(str(exception) for exception in self)


class ExceptionBase(Enum):
    """
    Base class for exceptions.
    """

    def __contains__(self, exception) -> bool:
        """
        Checks if provided exception is equal to this
        """
        return self == exception

    def __or__(
        self,
        other: Union["TransactionException", "BlockException", ExceptionList],
    ) -> "ExceptionList":
        """
        Combine two exceptions into an ExceptionList.
        """
        if isinstance(other, ExceptionList):
            return ExceptionList(self, *other)
        return ExceptionList(self, other)


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


ExceptionType = Union[TransactionException, BlockException, ExceptionList]
