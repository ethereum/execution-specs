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


class InvalidMaxFeePerBlobGas(InvalidTransaction):
    """
    The transaction carries no blobs but has a nonzero
    `max_fee_per_blob_gas`.
    """


class BlobCountExceededError(InvalidTransaction):
    """
    The transaction has more blobs than the limit.
    """


class PriorityFeeGreaterThanMaxFeeError(InvalidTransaction):
    """
    The priority fee is greater than the maximum fee per gas.
    """


class FeeOverflowError(InvalidTransaction):
    """
    A fee field of the transaction exceeds the largest representable
    256-bit value.
    """


class MaxCostOverflowError(InvalidTransaction):
    """
    The maximum wei cost the transaction can incur exceeds the largest
    representable 256-bit value.
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


class FrameCountError(InvalidTransaction):
    """
    The transaction has either too many or two few [`Frame`]s to be valid.

    [`Frame`]: ref:ethereum.forks.amsterdam.transactions.frame_transaction.Frame
    """  # noqa: E501

    maximum: Final[Uint]
    """
    Any more than this number of [`Frame`]s invalidates a transaction.

    [`Frame`]: ref:ethereum.forks.amsterdam.transactions.frame_transaction.Frame
    """  # noqa: E501

    actual: Final[Uint]
    """
    Number of [`Frame`]s actually included in the transaction.

    [`Frame`]: ref:ethereum.forks.amsterdam.transactions.frame_transaction.Frame
    """  # noqa: E501

    def __init__(self, actual: Uint, maximum: Uint) -> None:
        message = (
            f"transaction must contain between 1 and {maximum} frames, "
            f"inclusive (got {actual})"
        )

        super().__init__(message)
        self.maximum = maximum
        self.actual = actual


class InvalidFrameError(InvalidTransaction):
    """
    A [`Frame`] did not pass validation.

    [`Frame`]: ref:ethereum.forks.amsterdam.transactions.frame_transaction.Frame
    """  # noqa: E501


class FrameTransactionExecutionError(InvalidTransaction):
    """
    A frame transaction violated a validity rule that is only checkable
    during execution: a `VERIFY` frame reverted, a `SENDER` frame ran
    before execution approval, or no frame approved gas payment.
    """


class BlockAccessListGasLimitExceededError(InvalidBlock):
    """
    The block access list exceeds the gas limit constraint.

    Introduced in [EIP-7928].

    [EIP-7928]: https://eips.ethereum.org/EIPS/eip-7928
    """
