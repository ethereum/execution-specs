"""
leanSPHINCS, a stateless hash-based signature scheme over Keccak-256.

The scheme is the configuration that [EthLib] specifies in Lean: FORS with
24 trees of height 10 signs the message, and three layers of WOTS+C keys,
of heights 10, 8 and 8, sign the FORS key up to the public key. It allows
up to 2^30 signatures per key.

Verification calls [py-lean-pq], the Python bindings of leanVM's
implementation of that specification.

[EthLib]: https://github.com/ethereum/EthLib
[py-lean-pq]: https://github.com/ethereum/lean-pq-bindings
"""

from typing import Final

import py_lean_pq
from ethereum_types.bytes import Bytes, Bytes32

SPHINCS_PUBLIC_KEY_LENGTH: Final[int] = 32
"""
Length, in bytes, of a leanSPHINCS public key.
"""

SPHINCS_SIGNATURE_LENGTH: Final[int] = 7740
"""
Length, in bytes, of a leanSPHINCS signature.
"""

SPHINCS_MESSAGE_LENGTH: Final[int] = 32
"""
Length, in bytes, of a message signed by leanSPHINCS.
"""


def sphincs_verify(
    public_key: Bytes, message: Bytes32, signature: Bytes
) -> bool:
    """
    Return whether `signature` signs `message` under `public_key`.

    Every input must have its exact length: a public key of
    [`SPHINCS_PUBLIC_KEY_LENGTH`][pk] bytes and a signature of
    [`SPHINCS_SIGNATURE_LENGTH`][sig] bytes.

    [pk]: ref:ethereum.crypto.sphincs.SPHINCS_PUBLIC_KEY_LENGTH
    [sig]: ref:ethereum.crypto.sphincs.SPHINCS_SIGNATURE_LENGTH
    """
    assert len(public_key) == SPHINCS_PUBLIC_KEY_LENGTH
    assert len(message) == SPHINCS_MESSAGE_LENGTH
    assert len(signature) == SPHINCS_SIGNATURE_LENGTH
    try:
        py_lean_pq.sphincs_verify(
            bytes(public_key), bytes(message), bytes(signature)
        )
    except py_lean_pq.LeanPqError:
        return False
    return True
