"""Helper types, functions and classes for testing EIP-7702 Set Code Transaction."""

from enum import Enum, auto


class AddressType(Enum):
    """
    Different types of addresses used to specify the type of authority that signs an authorization,
    and the type of address to which the authority authorizes to set the code to.
    """

    EMPTY_ACCOUNT = auto()
    EOA = auto()
    EOA_WITH_SET_CODE = auto()
    CONTRACT = auto()


class ChainIDType(Enum):
    """Different types of chain IDs used in the authorization list."""

    GENERIC = auto()
    CHAIN_SPECIFIC = auto()
