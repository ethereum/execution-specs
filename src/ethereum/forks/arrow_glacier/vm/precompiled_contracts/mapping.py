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
    ALT_BN128_ADD_ADDRESS,
    ALT_BN128_MUL_ADDRESS,
    ALT_BN128_PAIRING_CHECK_ADDRESS,
    BLAKE2F_ADDRESS,
    ECRECOVER_ADDRESS,
    IDENTITY_ADDRESS,
    MODEXP_ADDRESS,
    RIPEMD160_ADDRESS,
    SHA256_ADDRESS,
)
from .alt_bn128 import alt_bn128_add, alt_bn128_mul, alt_bn128_pairing_check
from .blake2f import blake2f
from .ecrecover import ecrecover
from .identity import identity
from .modexp import modexp
from .ripemd160 import ripemd160
from .sha256 import sha256

PRE_COMPILED_CONTRACTS: Mapping[Address, Callable] = MappingProxyType(
    {
        ECRECOVER_ADDRESS: ecrecover,
        SHA256_ADDRESS: sha256,
        RIPEMD160_ADDRESS: ripemd160,
        IDENTITY_ADDRESS: identity,
        MODEXP_ADDRESS: modexp,
        ALT_BN128_ADD_ADDRESS: alt_bn128_add,
        ALT_BN128_MUL_ADDRESS: alt_bn128_mul,
        ALT_BN128_PAIRING_CHECK_ADDRESS: alt_bn128_pairing_check,
        BLAKE2F_ADDRESS: blake2f,
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
