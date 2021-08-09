"""
Utility Functions For RLP
^^^^^^^^^^^^^^^^^^^^^^^^^

..contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

RLP specific utility functions used in this application.
"""

from ethereum import crypto
from ethereum.crypto import Hash32
from ethereum.frontier import rlp


def rlp_hash(data: rlp.RLP) -> Hash32:
    """
    Obtain the keccak-256 hash of the rlp encoding of the passed in data.

    Parameters
    ----------
    data :
        The data for which we need the rlp hash.

    Returns
    -------
    hash : `Hash32`
        The rlp hash of the passed in data.
    """
    return crypto.keccak256(rlp.encode(data))
