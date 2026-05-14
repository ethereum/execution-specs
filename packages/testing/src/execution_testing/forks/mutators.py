"""Fork specific test modifiers."""

from enum import Flag


class SpecTestMutator(Flag):
    """
    Collection of modifiers supported by test specs which enable dynamic
    modifications on all tests depending on fork activation.
    """

    NONE = 0
