"""
leanSPHINCS, a stateless hash-based signature scheme over Keccak-256.

The scheme is specified by the Cryptography/Sphincs module of [EthLib] at
commit `03b7e4ddba3c6f09cbfe290930116d9dae75e708`, which also fixes the
encodings of its public keys and signatures. FORS with 24 trees of height
10 signs the message, and three layers of WOTS+C keys, of heights 10, 8
and 8, sign the FORS key up to the public key. It allows up to 2^30
signatures per key.

Verification calls [py-lean-pq], the Python bindings of leanVM's
implementation of that specification.

[EthLib]: https://github.com/ethereum/EthLib
[py-lean-pq]: https://github.com/ethereum/lean-pq-bindings
"""

from typing import Final

import py_lean_pq
from ethereum_types.bytes import Bytes, Bytes32

LEANSPHINCS_PUBLIC_KEY_LENGTH: Final[int] = 32
"""
Length, in bytes, of a leanSPHINCS public key: the 16-byte root of its
top tree followed by its 16-byte public parameter.
"""

LEANSPHINCS_SIGNATURE_LENGTH: Final[int] = 7740
"""
Length, in bytes, of a leanSPHINCS signature.
"""

LEANSPHINCS_MESSAGE_LENGTH: Final[int] = 32
"""
Length, in bytes, of a message signed by leanSPHINCS.
"""


def leansphincs_verify(
    public_key: Bytes, message: Bytes32, signature: Bytes
) -> bool:
    """
    Return whether `signature` signs `message` under `public_key`.

    Every input must have its exact length: a public key of
    [`LEANSPHINCS_PUBLIC_KEY_LENGTH`][pk] bytes and a signature of
    [`LEANSPHINCS_SIGNATURE_LENGTH`][sig] bytes.

    [pk]: ref:ethereum.crypto.leansphincs.LEANSPHINCS_PUBLIC_KEY_LENGTH
    [sig]: ref:ethereum.crypto.leansphincs.LEANSPHINCS_SIGNATURE_LENGTH
    """
    assert len(public_key) == LEANSPHINCS_PUBLIC_KEY_LENGTH
    assert len(message) == LEANSPHINCS_MESSAGE_LENGTH
    assert len(signature) == LEANSPHINCS_SIGNATURE_LENGTH
    try:
        py_lean_pq.sphincs_verify(
            bytes(public_key), bytes(message), bytes(signature)
        )
    except py_lean_pq.LeanPqError:
        return False
    return True
