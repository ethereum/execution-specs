"""
Verification of [EIP-8288] dependency proofs.

A dependency proof is a recursive leanVM STARK. Verifying one in Python
is impractical, so this module calls the native verifier of
Nethermind's `lean-bindings` (`libnethermind_lean`, C ABI version
[`LEAN_ABI_VERSION`][abi]) through `ctypes`. The library is located with
the `ETHEREUM_LEAN_LIBRARY` environment variable.

A verifier that cannot run is not a verdict: [`verify_dependency_proof`]
raises [`LeanVerifierUnavailable`] rather than returning `False`, as the
EIP forbids treating a local verifier failure as an invalid block.

[EIP-8288]: https://eips.ethereum.org/EIPS/eip-8288
[abi]: ref:ethereum.crypto.leanvm.LEAN_ABI_VERSION
[`verify_dependency_proof`]: ref:ethereum.crypto.leanvm.verify_dependency_proof
[`LeanVerifierUnavailable`]: ref:ethereum.crypto.leanvm.LeanVerifierUnavailable
"""  # noqa: E501

import ctypes
import os
from functools import cache
from typing import Final

from ethereum_types.bytes import Bytes, Bytes32

from ethereum.exceptions import EthereumException

LEAN_ABI_VERSION: Final[int] = 24
"""
C ABI version of the pinned native verifier (`Nethermind.Crypto.Lean`
0.24.0, upstream leanVM `f7ba4999`).
"""

LEAN_LIBRARY_ENV: Final[str] = "ETHEREUM_LEAN_LIBRARY"
"""Environment variable holding the path of the native verifier."""


class LeanVerifierUnavailable(EthereumException):  # noqa N818
    """
    The native leanVM verifier could not be loaded or did not reach a
    verdict.
    """


@cache
def _library() -> ctypes.CDLL:
    path = os.environ.get(LEAN_LIBRARY_ENV)
    if not path:
        raise LeanVerifierUnavailable(f"{LEAN_LIBRARY_ENV} is not set")
    try:
        library = ctypes.CDLL(path)
    except OSError as error:
        raise LeanVerifierUnavailable(str(error)) from error
    library.nlean_abi_version.restype = ctypes.c_uint32
    if library.nlean_abi_version() != LEAN_ABI_VERSION:
        raise LeanVerifierUnavailable("unexpected leanVM verifier ABI")
    library.nlean_verify_recursive.restype = ctypes.c_int32
    library.nlean_verify_recursive.argtypes = (
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_size_t,
        ctypes.c_char_p,
        ctypes.c_size_t,
    )
    return library


def verify_dependency_proof(
    deps_hash: Bytes32, aggregated_vk: Bytes32, proof: Bytes
) -> bool:
    """
    Check that `proof` is a recursive STARK of the guest keyed by
    `aggregated_vk` whose public statement is `deps_hash`.
    """
    verdict = _library().nlean_verify_recursive(
        bytes(deps_hash),
        bytes(aggregated_vk),
        len(aggregated_vk),
        bytes(proof),
        len(proof),
    )
    if verdict < 0:
        raise LeanVerifierUnavailable("leanVM verifier failed")
    return verdict == 1
