"""
Error types common across all Ethereum forks.
"""


class EthereumException(Exception):  # noqa N818
    """
    Base class for all exceptions _expected_ to be thrown during normal
    operation.
    """


class InvalidBlock(EthereumException):
    """
    Thrown when a block being processed is found to be invalid.
    """


class StateWithEmptyAccount(EthereumException):
    """
    Thrown when the state has empty account.
    """


class InvalidTransaction(EthereumException):
    """
    Thrown when a transaction being processed is found to be invalid.
    """


class InvalidSenderError(InvalidTransaction):
    """
    Thrown when a transaction originates from an account that cannot send
    transactions.
    """


class InvalidSignatureError(InvalidTransaction):
    """
    Thrown when a transaction has an invalid signature.
    """


class InsufficientBalanceError(InvalidTransaction):
    """
    Thrown when a transaction cannot be executed due to insufficient sender
    funds.
    """


class NonceMismatchError(InvalidTransaction):
    """
    Thrown when a transaction's nonce does not match the expected nonce for the
    sender.
    """


class GasUsedExceedsLimitError(InvalidTransaction):
    """
    Thrown when a transaction's gas usage exceeds the gas available in the
    block.
    """


class InsufficientTransactionGasError(InvalidTransaction):
    """
    Thrown when a transaction does not provide enough gas to cover its
    intrinsic cost.
    """


class NonceOverflowError(InvalidTransaction):
    """
    Thrown when a transaction's nonce is greater than `2**64 - 2`.
    """
