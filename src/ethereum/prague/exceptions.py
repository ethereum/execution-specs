"""
Exceptions specific to this fork.
"""

from typing import Final

from ethereum.exceptions import InvalidTransaction


class TransactionTypeError(InvalidTransaction):
    """
    Unknown [EIP-2718] transaction type byte.

    [EIP-2718]: https://eips.ethereum.org/EIPS/eip-2718
    """

    transaction_type: Final[int]
    """
    The type byte of the transaction that caused the error.
    """

    def __init__(self, transaction_type: int):
        super().__init__(f"unknown transaction type `{transaction_type}`")
        self.transaction_type = transaction_type


class TransactionTypeContractCreationError(InvalidTransaction):
    """
    Transaction type is not allowed for contract creation.
    """

    transaction_type: Final[int]
    """
    The type byte of the transaction that caused the error.
    """

    def __init__(self, transaction_type: int):
        super().__init__(
            f"transaction type `{transaction_type}` not allowed for "
            "contract creation"
        )
        self.transaction_type = transaction_type


class BlobGasLimitExceededError(InvalidTransaction):
    """
    The blob gas limit for the transaction exceeds the maximum allowed.
    """


class InsufficientMaxFeePerBlobGasError(InvalidTransaction):
    """
    The maximum fee per blob gas is insufficient for the transaction.
    """


class InsufficientMaxFeePerGasError(InvalidTransaction):
    """
    The maximum fee per gas is insufficient for the transaction.
    """


class InvalidBlobVersionedHashError(InvalidTransaction):
    """
    The versioned hash of the blob is invalid.
    """


class NoBlobDataError(InvalidTransaction):
    """
    The transaction does not contain any blob data.
    """


class PriorityFeeGreaterThanMaxFeeError(InvalidTransaction):
    """
    The priority fee is greater than the maximum fee per gas.
    """


class EmptyAuthorizationListError(InvalidTransaction):
    """
    The authorization list in the transaction is empty.
    """
