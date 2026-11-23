"""
The block's dependency proof, introduced in [EIP-8288].

Frame transactions declare claims ([`Dependency`][d]) in dependency
verification frames instead of carrying the signatures and proofs that
back them. Those travel through the mempool, where they are aggregated
into one recursive STARK, the dependency proof. The proof is in neither
the block header nor the block body: it travels in the execution payload,
and the header commits to it through `dependency_proof_hash`, next to the
`block_deps_hash` digest of the block's claims that the proof's public
statement is.

[EIP-8288]: https://eips.ethereum.org/EIPS/eip-8288
[d]: ref:ethereum.forks.bogota.transactions.frame_transaction.Dependency
"""

from typing import Final, Optional, Sequence, Tuple

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import Uint, ulen

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.crypto.leanvm import verify_dependency_proof
from ethereum.exceptions import EthereumException, InvalidBlock

from .blocks import Header
from .transactions.frame_transaction import Dependency

MAX_DEPENDENCY_PROOF_BYTES: Final[Uint] = Uint(1048576)
"""
Maximum length of a dependency proof. The proof is not part of the RLP
block, so the block size limit of [EIP-7934] does not cover it.

[EIP-7934]: https://eips.ethereum.org/EIPS/eip-7934
"""

AGGREGATED_VK: Final[Bytes32] = Bytes32(
    bytes.fromhex(
        "645bc491d3d0728b8a0f556be143f845e2ff80aa59da060d750f32cfb05b800c"
    )
)
"""
Verification key of the recursive guest. [EIP-8288] leaves it to be
defined; this is the guest of `Nethermind.Crypto.Lean` 0.24.0 (upstream
leanVM `f7ba4999`, leanSPHINCS over Keccak-256).

[EIP-8288]: https://eips.ethereum.org/EIPS/eip-8288
"""


class DependencyProofUnavailable(EthereumException):  # noqa N818
    """
    The block commits to a non-empty dependency proof that was not
    received with it. The block is not invalid: it cannot be validated.
    """


def block_dependencies(
    dependencies: Sequence[Dependency],
) -> Tuple[Dependency, ...]:
    """
    Return the claims of a block's transactions, deduplicated and
    sorted.
    """
    return tuple(sorted(set(dependencies)))


def encode_dependencies(dependencies: Sequence[Dependency]) -> Bytes:
    """
    Return the canonical 96-byte encoding of each claim, concatenated:
    its zero-padded scheme word, data hash and verification key hash.
    """
    return b"".join(
        int(dependency.scheme).to_bytes(32, "big")
        + dependency.data_hash
        + dependency.verification_key_hash
        for dependency in dependencies
    )


def compute_dependencies_hash(dependencies: Sequence[Dependency]) -> Hash32:
    """
    Compute `get_deps_hash`, the digest the dependency proof commits to.

    `DEPS_HASH` is the hash the aggregation circuit uses for its
    dependency digest. The pinned guest uses Keccak-256 over the
    canonical 96-byte claims, scheme word included, so an empty list
    hashes to `keccak256(b"")`.
    """
    return keccak256(encode_dependencies(dependencies))


def validate_dependency_proof(
    header: Header,
    dependencies: Sequence[Dependency],
    dependency_proof: Optional[Bytes],
) -> None:
    """
    Check the header's commitments against the block's claims and the
    dependency proof received with the block.

    `dependency_proof` is `None` when no proof was received. A block that
    commits to the empty proof needs none; any other block cannot be
    validated without it.
    """
    claims = block_dependencies(dependencies)
    if header.block_deps_hash != compute_dependencies_hash(claims):
        raise InvalidBlock("block deps hash mismatch")

    if dependency_proof is None:
        if header.dependency_proof_hash != keccak256(b""):
            raise DependencyProofUnavailable
        dependency_proof = Bytes(b"")

    if ulen(dependency_proof) > MAX_DEPENDENCY_PROOF_BYTES:
        raise InvalidBlock("dependency proof too long")
    if header.dependency_proof_hash != keccak256(dependency_proof):
        raise InvalidBlock("dependency proof hash mismatch")

    if len(claims) == 0:
        if len(dependency_proof) != 0:
            raise InvalidBlock("dependency proof without dependencies")
    elif not verify_dependency_proof(
        header.block_deps_hash, AGGREGATED_VK, dependency_proof
    ):
        raise InvalidBlock("invalid dependency proof")
