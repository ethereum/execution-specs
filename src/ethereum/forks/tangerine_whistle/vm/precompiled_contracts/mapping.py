"""
Precompiled Contract Addresses.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Mapping of precompiled contracts to their implementations.
"""

from types import MappingProxyType
from typing import Callable, Mapping

from ethereum.state import Address

from . import (
    ECRECOVER_ADDRESS,
    IDENTITY_ADDRESS,
    RIPEMD160_ADDRESS,
    SHA256_ADDRESS,
)
from .ecrecover import ecrecover
from .identity import identity
from .ripemd160 import ripemd160
from .sha256 import sha256

PRE_COMPILED_CONTRACTS: Mapping[Address, Callable] = MappingProxyType(
    {
        ECRECOVER_ADDRESS: ecrecover,
        SHA256_ADDRESS: sha256,
        RIPEMD160_ADDRESS: ripemd160,
        IDENTITY_ADDRESS: identity,
    }
)
"""
The precompiled contracts of this fork, keyed by the address each one
answers at.

The mapping is read-only. An execution that wants a different
arrangement -- a precompile moved elsewhere, or withheld entirely --
hands its own mapping to the block environment rather than editing this
one, so the rearrangement cannot outlive the execution that asked for
it.
"""
