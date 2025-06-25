"""Exceptions for invalid execution."""

from .base import ExceptionBase, UndefinedException, from_pipe_str, to_pipe_str
from .block import BlockException
from .eof import EOFException
from .transaction import TransactionException
from .types import (
    BlockExceptionInstanceOrList,
    EOFExceptionInstanceOrList,
    ExceptionBoundTypeVar,
    ExceptionInstanceOrList,
    TransactionExceptionInstanceOrList,
)

__all__ = [
    "ExceptionBase",
    "UndefinedException",
    "from_pipe_str",
    "to_pipe_str",
    "TransactionException",
    "BlockException",
    "EOFException",
    "ExceptionInstanceOrList",
    "TransactionExceptionInstanceOrList",
    "BlockExceptionInstanceOrList",
    "EOFExceptionInstanceOrList",
    "ExceptionBoundTypeVar",
]
