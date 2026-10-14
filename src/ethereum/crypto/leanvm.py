"""
Verification of [leanVM] execution proofs, the recursive STARKs of
[EIP-8288].

A block's proof attests, under a pinned recursive guest program, that every
dependency the block declares was verified. [`verify_dependencies`] checks
one against the block's dependency digest, and [`recursive_guest_key`] is the
key of the guest it checks against. Both come from the pinned leanVM fork's
dependency-free Python verifier, [`leanvm-verifier`].

[leanVM]: https://github.com/leanEthereum/leanVM
[EIP-8288]: https://eips.ethereum.org/EIPS/eip-8288
[`leanvm-verifier`]: https://github.com/spencer-tb/leanVM/tree/46cb599c0e40b605b21d91dd78d6adb2a93f6bd7/python-verifier
[`verify_dependencies`]: ref:ethereum.crypto.leanvm.verify_dependencies
[`recursive_guest_key`]: ref:ethereum.crypto.leanvm.recursive_guest_key
"""  # noqa: E501

from ethereum_types.bytes import Bytes, Bytes32
from leanvm_verifier import eip8288_mixed


def recursive_guest_key() -> Bytes32:
    """
    Return the verification key of the recursive guest whose proofs
    [`verify_dependencies`] accepts.

    [`verify_dependencies`]: ref:ethereum.crypto.leanvm.verify_dependencies
    """
    return Bytes32(eip8288_mixed.guest_key())


def verify_dependencies(dependencies_hash: Bytes32, proof: Bytes) -> bool:
    """
    Check that `proof` proves, under the recursive guest, exactly the
    dependencies `dependencies_hash` commits to.
    """
    return eip8288_mixed.verify_dependencies(
        bytes(dependencies_hash), bytes(proof)
    )
