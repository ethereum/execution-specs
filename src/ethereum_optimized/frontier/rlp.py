"""
Optimized RLP
^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

This module contains functions can be monkey patched into
`ethereum.frontier.rlp` to use alternate optimized implementations.
"""

from platform import python_implementation
from typing import Sequence

import ethereum.frontier.rlp as rlp
from ethereum.base_types import U256, Bytes, Uint
from ethereum.frontier.eth_types import (
    Block,
    Header,
    Log,
    Receipt,
    Transaction,
)

if python_implementation() == "CPython":
    from rusty_rlp import decode_raw, encode_raw
elif python_implementation() == "PyPy":
    from rlp.codec import decode_raw, encode_raw


def encode(raw_data: rlp.RLP) -> Bytes:
    """F"""
    return encode_raw(transcode(raw_data))


def decode(encoded_data: Bytes) -> rlp.RLP:
    """F"""
    return decode_raw(encoded_data, True, False)[0]


def transcode(raw_data: rlp.RLP) -> rlp.RLP:
    """
    Encodes `raw_data` into a sequence of bytes using RLP.

    Parameters
    ----------
    raw_data :
        A `Bytes`, `Uint`, `Uint256` or sequence of `RLP` encodable
        objects.

    Returns
    -------
    encoded : `eth1spec.base_types.Bytes`
        The RLP encoded bytes representing `raw_data`.
    """
    if isinstance(raw_data, bytes):
        return raw_data
    elif isinstance(raw_data, (Uint, U256)):
        return raw_data.to_be_bytes()
    elif isinstance(raw_data, str):
        return raw_data.encode()
    elif isinstance(raw_data, bytearray):
        return bytes(raw_data)
    elif isinstance(raw_data, Sequence):
        return list(map(transcode, raw_data))
    elif isinstance(raw_data, Block):
        return transcode(rlp.transcode_block(raw_data))
    elif isinstance(raw_data, Header):
        return transcode(rlp.transcode_header(raw_data))
    elif isinstance(raw_data, Transaction):
        return transcode(rlp.transcode_transaction(raw_data))
    elif isinstance(raw_data, Receipt):
        return transcode(rlp.transcode_receipt(raw_data))
    elif isinstance(raw_data, Log):
        return transcode(rlp.transcode_log(raw_data))
    else:
        raise TypeError(
            "RLP Encoding of type {} is not supported".format(type(raw_data))
        )
