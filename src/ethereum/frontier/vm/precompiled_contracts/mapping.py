"""
Precompiled Contract Addresses
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Mapping of precompiled contracts their implementations.
"""
from typing import Callable, Dict

from ...eth_types import Address
from ...utils.hexadecimal import hex_to_address
from .ecrecover import ecrecover
from .identity import identity
from .ripemd160 import ripemd160
from .sha256 import sha256

PRE_COMPILED_CONTRACTS: Dict[Address, Callable] = {
    hex_to_address("0x01"): ecrecover,
    hex_to_address("0x02"): sha256,
    hex_to_address("0x03"): ripemd160,
    hex_to_address("0x04"): identity,
}
