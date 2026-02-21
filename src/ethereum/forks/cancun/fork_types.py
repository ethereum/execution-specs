"""
Ethereum Types.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Types reused throughout the specification, which are specific to Ethereum.
"""

from ethereum_types.bytes import Bytes20, Bytes256

from ethereum.crypto.hash import Hash32
from ethereum.state import (
    EMPTY_ACCOUNT as EMPTY_ACCOUNT,
)
from ethereum.state import (
    Account as Account,
)

Address = Bytes20
Root = Hash32
VersionedHash = Hash32

Bloom = Bytes256
