"""
The block's recursive STARK, introduced in [EIP-8288].

Frame transactions declare claims ([`Dependency`][d]) in dependency
verification frames instead of carrying the signatures and proofs that
back them. Those travel through the mempool, where they are aggregated
into a single recursive STARK. The block header carries that proof with
a digest of the block's claims ([`RecursiveStark`][rs]), and a block is
valid only if the digest commits to exactly the claims its transactions
declare and the proof verifies against it.

The proof is a leanVM proof of the pinned recursive guest, checked by the
leanVM verifier (see [`verify_recursive_stark`][vrs]).

[EIP-8288]: https://eips.ethereum.org/EIPS/eip-8288
[d]: ref:ethereum.forks.bogota.transactions.frame_transaction.Dependency
[rs]: ref:ethereum.forks.bogota.blocks.RecursiveStark
[vrs]: ref:ethereum.forks.bogota.recursive_stark.verify_recursive_stark
"""

from typing import Final, Sequence, Tuple

from ethereum_types.bytes import Bytes, Bytes32

from ethereum.crypto.hash import Hash32, blake2s256
from ethereum.crypto.leanvm import recursive_guest_key, verify_dependencies
from ethereum.exceptions import InvalidBlock

from .blocks import RecursiveStark
from .transactions.frame_transaction import Dependency

AGGREGATED_VK: Final[Bytes32] = Bytes32(
    bytes.fromhex(
        "6deed6ff48d7e4af71132fb8cdc5224d16574d0358a94d274af5caee648c80ad"
    )
)
"""
Verification key of the recursive STARK circuit: the transcript seed of
the recursive guest, which binds its bytecode. [EIP-8288] leaves it to be
defined; this is the guest Nethermind's prototype pins
(`Eip8288Constants.AggregatedVk`).

[EIP-8288]: https://eips.ethereum.org/EIPS/eip-8288
"""


def block_dependencies(
    dependencies: Sequence[Dependency],
) -> Tuple[Dependency, ...]:
    """
    Return the claims of a block's transactions, deduplicated and
    sorted.
    """
    return tuple(sorted(set(dependencies)))


def compute_dependencies_hash(dependencies: Sequence[Dependency]) -> Hash32:
    """
    Compute the digest the recursive STARK commits to: the [BLAKE2s]
    hash of each claim's data hash followed by its verification key
    hash, in order. [EIP-8288] calls it `get_deps_hash` and defines it
    for leanSPHINCS claims, the only scheme a frame may declare.

    [BLAKE2s]: ref:ethereum.crypto.hash.blake2s256
    [EIP-8288]: https://eips.ethereum.org/EIPS/eip-8288
    """
    return blake2s256(
        b"".join(
            dependency.data_hash + dependency.verification_key_hash
            for dependency in dependencies
        )
    )


def verify_recursive_stark(
    stark_proof: Bytes, block_deps_hash: Hash32
) -> bool:
    """
    Check that `stark_proof` proves, under the guest whose key is
    [`AGGREGATED_VK`][avk], exactly the claims `block_deps_hash` commits
    to.

    [avk]: ref:ethereum.forks.bogota.recursive_stark.AGGREGATED_VK
    """
    if recursive_guest_key() != AGGREGATED_VK:
        return False
    return verify_dependencies(block_deps_hash, stark_proof)


def validate_recursive_stark(
    recursive_stark: RecursiveStark,
    dependencies: Sequence[Dependency],
) -> None:
    """
    Check the header's recursive STARK against the claims the block's
    transactions declare.

    The digest must commit to the deduplicated, sorted claims. A block
    declaring no claims carries an empty proof, and any other block a
    proof that verifies against the digest.
    """
    claims = block_dependencies(dependencies)
    if recursive_stark.block_deps_hash != compute_dependencies_hash(claims):
        raise InvalidBlock("block deps hash mismatch")
    if len(claims) == 0:
        if len(recursive_stark.stark_proof) != 0:
            raise InvalidBlock("recursive STARK proof without dependencies")
    elif not verify_recursive_stark(
        recursive_stark.stark_proof, recursive_stark.block_deps_hash
    ):
        raise InvalidBlock("invalid recursive STARK proof")
