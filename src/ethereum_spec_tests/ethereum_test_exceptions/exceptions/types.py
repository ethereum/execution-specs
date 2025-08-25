"""Pydantic annotated types for exceptions."""

from typing import Annotated, List, TypeVar

from pydantic import BeforeValidator, PlainSerializer

from .base import from_pipe_str, to_pipe_str
from .block import BlockException
from .eof import EOFException
from .transaction import TransactionException

"""
Pydantic Annotated Types
"""

ExceptionInstanceOrList = Annotated[
    List[TransactionException | BlockException] | TransactionException | BlockException,
    BeforeValidator(from_pipe_str),
    PlainSerializer(to_pipe_str),
]

TransactionExceptionInstanceOrList = Annotated[
    List[TransactionException] | TransactionException,
    BeforeValidator(from_pipe_str),
    PlainSerializer(to_pipe_str),
]

BlockExceptionInstanceOrList = Annotated[
    List[BlockException] | BlockException,
    BeforeValidator(from_pipe_str),
    PlainSerializer(to_pipe_str),
]

EOFExceptionInstanceOrList = Annotated[
    List[EOFException] | EOFException,
    BeforeValidator(from_pipe_str),
    PlainSerializer(to_pipe_str),
]

ExceptionBoundTypeVar = TypeVar(
    "ExceptionBoundTypeVar", TransactionException, BlockException, EOFException
)
