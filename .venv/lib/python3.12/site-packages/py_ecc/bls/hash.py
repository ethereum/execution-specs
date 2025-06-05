import hashlib
import hmac
import math
from typing import (
    Union,
)

from _hashlib import (
    HASH,
)


def hkdf_extract(salt: Union[bytes, bytearray], ikm: Union[bytes, bytearray]) -> bytes:
    """
    HKDF-Extract

    https://tools.ietf.org/html/rfc5869
    """
    return hmac.new(salt, ikm, hashlib.sha256).digest()


def hkdf_expand(
    prk: Union[bytes, bytearray], info: Union[bytes, bytearray], length: int
) -> bytes:
    """
    HKDF-Expand

    https://tools.ietf.org/html/rfc5869
    """
    n = math.ceil(length / 32)

    # okm = T(1) || T(2) || T(3) || ... || T(n)
    okm = bytearray(0)
    previous = bytearray(0)

    for i in range(0, n):
        # Concatenate (T(i) || info || i)
        text = previous + info + bytes([i + 1])

        # T(i + 1) = HMAC(T(i) || info || i)
        previous = bytearray(hmac.new(prk, text, hashlib.sha256).digest())
        okm.extend(previous)

    # Return first `length` bytes.
    return okm[:length]


def i2osp(x: int, xlen: int) -> bytes:
    """
    Convert a nonnegative integer `x` to an octet string of a specified length `xlen`.
    https://tools.ietf.org/html/rfc8017#section-4.1
    """
    return x.to_bytes(xlen, byteorder="big", signed=False)


def os2ip(x: bytes) -> int:
    """
    Convert an octet string `x` to a nonnegative integer.
    https://tools.ietf.org/html/rfc8017#section-4.2
    """
    return int.from_bytes(x, byteorder="big", signed=False)


def sha256(x: bytes) -> bytes:
    return hashlib.sha256(x).digest()


def xor(a: bytes, b: bytes) -> bytes:
    return bytes(_a ^ _b for _a, _b in zip(a, b))


def expand_message_xmd(
    msg: bytes, DST: bytes, len_in_bytes: int, hash_function: HASH
) -> bytes:
    b_in_bytes = hash_function().digest_size
    r_in_bytes = hash_function().block_size
    if len(DST) > 255:
        raise ValueError("DST must be <= 255 bytes")
    ell = math.ceil(len_in_bytes / b_in_bytes)
    if ell > 255:
        raise ValueError("invalid len in bytes for hash function")
    DST_prime = DST + i2osp(
        len(DST), 1
    )  # Append the length of the DST as a single byte
    Z_pad = b"\x00" * r_in_bytes
    l_i_b_str = i2osp(len_in_bytes, 2)
    b_0 = hash_function(Z_pad + msg + l_i_b_str + b"\x00" + DST_prime).digest()
    b = [hash_function(b_0 + b"\x01" + DST_prime).digest()]
    for i in range(2, ell + 1):
        b.append(hash_function(xor(b_0, b[i - 2]) + i2osp(i, 1) + DST_prime).digest())
    pseudo_random_bytes = b"".join(b)
    return pseudo_random_bytes[:len_in_bytes]
