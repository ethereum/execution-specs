"""
Exceptions specific to this fork.
"""

from typing import TYPE_CHECKING, Final

from ethereum_types.numeric import Uint

from ethereum.exceptions import InvalidTransaction

if TYPE_CHECKING:
    from .transactions import Transaction


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
    Contract creation is not allowed for a transaction type.
    """

    transaction: "Transaction"
    """
    The transaction that caused the error.
    """

    def __init__(self, transaction: "Transaction"):
        super().__init__(
            f"transaction type `{type(transaction).__name__}` not allowed to "
            "create contracts"
        )
        self.transaction = transaction


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

    transaction_max_fee_per_gas: Final[Uint]
    """
    The maximum fee per gas specified in the transaction.
    """

    block_base_fee_per_gas: Final[Uint]
    """
    The base fee per gas of the block in which the transaction is included.
    """

    def __init__(
        self, transaction_max_fee_per_gas: Uint, block_base_fee_per_gas: Uint
    ):
        super().__init__(
            f"Insufficient max fee per gas "
            f"({transaction_max_fee_per_gas} < {block_base_fee_per_gas})"
        )
        self.transaction_max_fee_per_gas = transaction_max_fee_per_gas
        self.block_base_fee_per_gas = block_base_fee_per_gas


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


class InitCodeTooLargeError(InvalidTransaction):
    """
    The init code of the transaction is too large.
    """
