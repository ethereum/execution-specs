"""Helpers for EIP-8288 proof aggregation tests."""

import hashlib
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from execution_testing import (
    Bytes,
    Fork,
    Frame,
    FrameReceipt,
    Hash,
    RecursiveStark,
    keccak256,
)
from execution_testing.forks.forks.eips.bogota.eip_8288 import (
    leansphincs_test_keys,
    recursive_stark_proof,
)

from tests.bogota.eip8141_frame_transactions.spec import Spec as Spec8141

from .spec import Spec

Dependency = Tuple[int, bytes, bytes]
"""A `(scheme, data_hash, verification_key_hash)` triple."""


def claim(
    message: int, *, key: int = 0, scheme: int = Spec.LEANSPHINCS_SCHEME
) -> Dependency:
    """
    Return a claim that a signature by test key `key` exists over
    message `message`.
    """
    return (
        scheme,
        bytes(keccak256(b"message" + message.to_bytes(32, "big"))),
        leansphincs_test_keys()[key],
    )


def encode_dependencies(dependencies: Sequence[Dependency]) -> Bytes:
    """Return the `96 * k` byte frame data declaring `dependencies`."""
    return Bytes(
        b"".join(
            scheme.to_bytes(32, "big") + data_hash + verification_key_hash
            for scheme, data_hash, verification_key_hash in dependencies
        )
    )


def verification_gas(fork: Fork, count: int) -> int:
    """Return the execution budget a frame declaring `count` claims sets."""
    return count * fork.gas_costs().LEANSPHINCS_VERIFICATION


def dependency_frame(
    fork: Fork, dependencies: Sequence[Dependency], **overrides: Any
) -> Frame:
    """
    Return a valid dependency verification frame declaring
    `dependencies`.

    Keyword arguments override the corresponding frame fields, for
    variants that differ from the canonical frame in a single field.
    """
    kwargs: Dict[str, Any] = dict(
        mode=Spec.MODE_DEP_VERIFY,
        data=encode_dependencies(dependencies),
        gas_limit=verification_gas(fork, len(dependencies)),
        state_gas_limit=0,
    )
    kwargs.update(overrides)
    return Frame(**kwargs)


def dependency_receipt(fork: Fork, count: int) -> FrameReceipt:
    """
    Return the receipt of a dependency frame declaring `count` claims:
    success, its whole execution budget used, no state gas, no logs.
    """
    return FrameReceipt(
        status=Spec8141.STATUS_SUCCESS,
        gas_used=verification_gas(fork, count),
        state_gas_used=0,
        logs=[],
    )


def ordered_dependencies_hash(dependencies: Sequence[Dependency]) -> Hash:
    """
    Return `get_deps_hash` of `dependencies` in the given order: BLAKE2s
    over each claim's data hash and verification key hash.
    """
    return Hash(
        hashlib.blake2s(
            b"".join(
                data_hash + verification_key_hash
                for _, data_hash, verification_key_hash in dependencies
            ),
            digest_size=32,
        ).digest()
    )


def dependencies_hash(dependencies: Iterable[Dependency]) -> Hash:
    """Return `get_deps_hash` of the deduplicated, sorted claims."""
    return ordered_dependencies_hash(sorted(set(dependencies)))


def stored_proof(dependencies: Iterable[Dependency]) -> Bytes:
    """Return the stored recursive STARK of a non-empty set of claims."""
    claims = sorted(set(dependencies))
    return Bytes(
        recursive_stark_proof(
            encode_dependencies(claims), dependencies_hash(claims)
        )
    )


def expected_recursive_stark(
    dependencies: Iterable[Dependency],
) -> RecursiveStark:
    """
    Return the header entry of a block whose transactions declare
    `dependencies`: an empty proof when there are none.
    """
    claims: List[Dependency] = list(dependencies)
    return RecursiveStark(
        stark_proof=stored_proof(claims) if claims else b"",
        block_deps_hash=dependencies_hash(claims),
    )
