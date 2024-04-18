"""
Exceptions for invalid execution.
"""

from .exceptions import (
    BlockException,
    BlockExceptionInstanceOrList,
    EOFException,
    ExceptionInstanceOrList,
    TransactionException,
    TransactionExceptionInstanceOrList,
)

__all__ = [
    "BlockException",
    "BlockExceptionInstanceOrList",
    "EOFException",
    "ExceptionInstanceOrList",
    "TransactionException",
    "TransactionExceptionInstanceOrList",
]
