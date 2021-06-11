"""
Recursive Length Prefix (RLP) Encoding
--------------------------------------
"""

from __future__ import annotations

from typing import List, Sequence, Tuple, Union, cast

from .base_types import U256, Uint
from .eth_types import Bytes

verbose = False
debug = False


RLP = Union[Bytes, Uint, U256, Sequence["RLP"]]  # type: ignore


def encode(x: RLP) -> Bytes:
    """
    Encodes `x` into a sequence of bytes using RLP.

    Parameters
    ----------
    x : `RLP`
        A `Bytes`, `Uint`, or sequence of `RLP` encodable objects.

    Returns
    -------
    encoded : `eth1spec.eth_types.Bytes`
        The RLP encoded bytes representing `x`.
    """
    if verbose:
        print("RLP(", x, ")", "type: ", type(x))
    if isinstance(x, (bytearray, bytes)):
        return R_b(x)
    elif isinstance(x, (Uint, U256)):
        return encode(x.to_be_bytes())
    elif isinstance(x, Sequence):
        return R_l(cast(Sequence[RLP], x))
    else:
        raise TypeError()


# binary encoding/decoding
def R_b(x: Bytes) -> Bytes:
    """
    Encodes `x`, a sequence of bytes, using RLP.

    Parameters
    ----------
    x : `eth1spec.eth_types.Bytes`
        Bytes to encode with RLP.

    Returns
    -------
    encoded : `eth1spec.eth_types.Bytes`
        The RLP encoded bytes representing `x`.
    """
    if verbose:
        print("R_b(", x, ")")
    len_x = Uint(len(x))
    if len_x == 1 and x[0] < 128:
        return x  # bytearray([x[0] + 0x80]) # noqa: SC100
    elif len_x < 56:
        return bytearray([128 + len_x]) + x
    else:
        big_endian = len_x.to_be_bytes()
        return bytearray([183 + len(big_endian)]) + big_endian + x


# list encoding/decoding
def R_l(x: Sequence[RLP]) -> Bytes:
    """
    Encodes `x`, a list of RLP encodable objects, using RLP.

    Parameters
    ----------
    x : `List[RLP]`
        List to encode with RLP.

    Returns
    -------
    encoded : `eth1spec.eth_types.Bytes`
        The RLP encoded bytes representing `x`.
    """
    if verbose:
        print("R_l(", x, ")")
    partial_x = s(x)
    len_partial_x = Uint(len(partial_x))
    if len_partial_x < 56:
        return bytearray([192 + len_partial_x]) + partial_x
    else:
        big_endian = len_partial_x.to_be_bytes()
        return bytearray([247 + len(big_endian)]) + big_endian + partial_x


# for a list, recursively call RLP or RLP_inverse
def s(x: Sequence[RLP]) -> Bytes:
    """
    Partially encodes `x`, a list of RLP encodable objects, using RLP,
    excluding the length prefix.

    Parameters
    ----------
    x : `List[RLP]`
        List to encode with RLP.

    Returns
    -------
    partially_encoded : `eth1spec.eth_types.Bytes`
        The partially RLP encoded bytes representing `x`.
    """
    if verbose:
        print("s(", x, ")")
    partially_encoded = bytearray([])
    for xi in x:
        partially_encoded += encode(xi)
    return partially_encoded


# inverses of above


def decode(b: Bytes) -> RLP:
    """
    Decodes an integer, byte sequence, or list of RLP encodable objects from
    the byte sequence `b`, using RLP.

    Parameters
    ----------
    b : `eth1spec.eth_types.Bytes`
        A sequence of bytes, in RLP form.

    Returns
    -------
    decoded : `RLP`
        Object decoded from `b`.
    """
    if verbose:
        print("RLP_inverse(", b.hex(), ")")
    if len(b) == 0:
        return bytearray([0x80])
    if b[0] < 0xC0:  # bytes
        return R_b_inverse(b)
    else:
        return R_l_inverse(b)


def R_b_inverse(b: Bytes) -> Bytes:
    """
    Decodes a byte sequence from the byte sequence `b`, using RLP.

    Parameters
    ----------
    b : `eth1spec.eth_types.Bytes`
        A sequence of bytes, in RLP form.

    Returns
    -------
    decoded : `eth1spec.eth_types.Bytes`
        Bytes decoded from `b`
    """
    if verbose:
        print("R_b_inverse(", b.hex(), ")")
    if len(b) == 1 and b[0] < 0x80:
        return b  # bytearray([b[0]-0x80]) # noqa: SC100
    elif b[0] <= 0xB7:
        return b[1 : 1 + b[0] - 0x80]
    else:
        length_len = b[0] - 183
        len_x = Uint.from_be_bytes(b[1 : length_len + 1])
        return b[length_len + 1 : length_len + 1 + len_x]


def R_l_inverse(b: Bytes) -> List[RLP]:
    """
    Decodes `b` into a list of RLP encodable objects, using RLP.

    Parameters
    ----------
    b : `eth1spec.eth_types.Bytes`
        An RLP encoded list.

    Returns
    -------
    decoded : `List[RLP]`
        List of objects decoded from `b`.
    """
    if verbose:
        print("R_l_inverse(", b.hex(), ")")
    if b[0] <= 0xF7:
        len_partial_x = b[0] - 0xC0
        partial_x = b[1 : 1 + len_partial_x]
    else:
        len_len_partial_x = b[0] - 247
        len_partial_x = Uint.from_be_bytes(b[1 : 1 + len_len_partial_x])
        partial_x = b[
            1 + len_len_partial_x : 1 + len_len_partial_x + len_partial_x
        ]
    return s_inverse(partial_x)


def s_inverse(b: Bytes) -> List[RLP]:
    """
    Decodes `b`, a partially encoded list of RLP encodable objects, excluding
    the length prefix.

    Parameters
    ----------
    b : `eth1spec.eth_types.Bytes`
        A list of objects, encoded in RLP, without the length prefix.

    Returns
    -------
    decoded : `List[RLP]`
        A list of objects decoded from `b`.
    """
    if verbose:
        print("s_inverse(", b.hex(), ")")
    x = []
    i = 0
    len_ = len(b)
    while i < len_:
        len_cur, len_len_cur = decode_length(b[i:])
        x += [decode(b[i : i + len_len_cur + len_cur])]
        i += len_cur + len_len_cur
        if debug:
            print("  s_inverse() returning", x)
    if debug:
        print("  s_inverse() returning", x)
    return x


# this is a helper function not described in the spec
# but the spec does not discuss the inverse to he RLP function, so never has
# the opportunity to discuss this returns the length of an encoded rlp object
def decode_length(b: Bytes) -> Tuple[Uint, Uint]:
    """
    Decodes the length prefix from the byte sequence `b`.

    Parameters
    ----------
    b : `eth1spec.eth_types.Bytes`
        Sequence of RLP bytes.

    Returns
    -------
    rlp_length : `eth1spec.base_types.Uint`
        TODO
    length_length : `eth1spec.base_types.Uint`
        TODO
    """
    if verbose:
        print("length_inverse(", b.hex(), ")")
    if len(b) == 0:
        return Uint(0), Uint(0)  # TODO: this may be an error
    length_length = Uint(0)
    first_rlp_byte = Uint(b[0])
    if first_rlp_byte < 0x80:
        rlp_length = Uint(1)
        return rlp_length, length_length
    elif first_rlp_byte <= 0xB7:
        rlp_length = first_rlp_byte - 0x80
    elif first_rlp_byte <= 0xBF:
        length_length = first_rlp_byte - 0xB7
        rlp_length = Uint.from_be_bytes(b[1 : 1 + length_length])
    elif first_rlp_byte <= 0xF7:
        rlp_length = first_rlp_byte - 0xC0
    elif first_rlp_byte <= 0xBF:
        length_length = first_rlp_byte - 0xB7
        rlp_length = Uint.from_be_bytes(b[1 : 1 + length_length])
    return rlp_length, Uint(1 + length_length)
