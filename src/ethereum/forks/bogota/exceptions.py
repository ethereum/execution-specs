"""
Exceptions specific to this fork.
"""

from typing import TYPE_CHECKING, Final

from ethereum_types.numeric import U64, Uint

from ethereum.exceptions import InvalidBlock, InvalidTransaction

if TYPE_CHECKING:
    from .transactions import Transaction


class WrongChainIdError(InvalidTransaction):
    """
    Chain identifier from a transaction does not match the executing chain. See
    [EIP-155].

    [EIP-155]: https://eips.ethereum.org/EIPS/eip-155
    """

    def __init__(self, expected: U64, actual: U64):
        super().__init__(f"expected chain_id `{expected}` but got `{actual}`")
        self.expected = expected
        self.actual = actual


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


class InvalidBlobVersionedHashError(InvalidTransaction):
    """
    The versioned hash of the blob is invalid.
    """


class NoBlobDataError(InvalidTransaction):
    """
    The transaction does not contain any blob data.
    """


class BlobCountExceededError(InvalidTransaction):
    """
    The transaction has more blobs than the limit.
    """


class PriorityFeeGreaterThanMaxFeeError(InvalidTransaction):
    """
    The priority fee is greater than the maximum fee per gas.
    """


class EmptyAuthorizationListError(InvalidTransaction):
    """
    The authorization list in the transaction is empty.
    """


class InitCodeTooLargeError(InvalidTransaction):
    """
    The init code of the transaction is too large.
    """


class TransactionGasLimitExceededError(InvalidTransaction):
    """
    The transaction has specified a gas limit that is greater than the allowed
    maximum.

    Note that this is _not_ the exception thrown when bytecode execution runs
    out of gas.
    """


class BlockAccessListGasLimitExceededError(InvalidBlock):
    """
    The block access list exceeds the gas limit constraint.

    Introduced in [EIP-7928].

    [EIP-7928]: https://eips.ethereum.org/EIPS/eip-7928
    """


class InsufficientMaxFeeError(InvalidTransaction):
    """
    The transaction's fee budget cannot cover the base fees of every
    resource it reserves ([EIP-7999]).

    [EIP-7999]: https://eips.ethereum.org/EIPS/eip-7999
    """

    max_fee: Final[Uint]
    """
    The fee budget of the transaction.
    """

    required_max_fee: Final[Uint]
    """
    The base fees of every resource the transaction reserves.
    """

    def __init__(self, max_fee: Uint, required_max_fee: Uint):
        super().__init__(
            f"Insufficient max fee ({max_fee} < {required_max_fee})"
        )
        self.max_fee = max_fee
        self.required_max_fee = required_max_fee


class CalldataGasLimitExceededError(InvalidTransaction):
    """
    The transaction's calldata gas does not fit the block's remaining
    calldata gas ([EIP-7999]).

    [EIP-7999]: https://eips.ethereum.org/EIPS/eip-7999
    """


class InvalidGasLimitsVectorError(InvalidTransaction):
    """
    A multidimensional transaction lists a number of gas limits other than
    the single EVM gas limit ([EIP-7999]).

    [EIP-7999]: https://eips.ethereum.org/EIPS/eip-7999
    """


class InvalidPriorityFeesVectorError(InvalidTransaction):
    """
    A multidimensional transaction lists priority fee caps for neither one
    nor every resource, or a cap above `2**64 - 1` ([EIP-7999]).

    [EIP-7999]: https://eips.ethereum.org/EIPS/eip-7999
    """


class MaxFeeTooLargeError(InvalidTransaction):
    """
    A multidimensional transaction's fee budget exceeds `2**128 - 1`
    ([EIP-7999]).

    [EIP-7999]: https://eips.ethereum.org/EIPS/eip-7999
    """
