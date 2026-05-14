"""Fork specific test modifiers."""

from enum import Flag, auto


class SpecTestMutator(Flag):
    """
    Collection of modifiers supported by test specs which enable dynamic
    modifications on all tests depending on fork activation.
    """

    NONE = 0
    EIP_7702_ALL_CONTRACTS_AS_DELEGATIONS = auto()
