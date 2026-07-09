"""Recipient type enumeration for transaction gas calculations."""

from enum import Enum, auto


class RecipientType(Enum):
    """The type of recipient for a transaction."""

    SELF = auto()
    EOA = auto()
    CONTRACT = auto()
    DELEGATION_7702 = auto()
    PRECOMPILE = auto()
    EMPTY_ACCOUNT = auto()
