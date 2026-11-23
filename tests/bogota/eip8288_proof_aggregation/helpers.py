"""Helpers for EIP-8288 proof aggregation tests."""

from typing import Any, Dict, Iterable, List, Sequence, Tuple

from execution_testing import (
    Bytes,
    Fork,
    Frame,
    FrameReceipt,
    Hash,
    Header,
    keccak256,
)
from execution_testing.forks.forks.eips.bogota.eip_8288 import (
    dependency_proof,
    leansphincs_test_keys,
    leanstark_test_key,
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


def stark_claim(message: int) -> Dependency:
    """
    Return a claim that the accept-all test leanSTARK program has a proof
    with public inputs hash derived from `message`.
    """
    return (
        Spec.LEANSTARK_SCHEME,
        bytes(keccak256(b"stark" + message.to_bytes(32, "big"))),
        leanstark_test_key(),
    )


def encode_dependencies(dependencies: Sequence[Dependency]) -> Bytes:
    """Return the `96 * k` byte frame data declaring `dependencies`."""
    return Bytes(
        b"".join(
            scheme.to_bytes(32, "big") + data_hash + verification_key_hash
            for scheme, data_hash, verification_key_hash in dependencies
        )
    )


def verification_gas(fork: Fork, count: int, *, stark_count: int = 0) -> int:
    """
    Return the execution budget a frame declaring `count` leanSPHINCS
    and `stark_count` leanSTARK claims sets.
    """
    costs = fork.gas_costs()
    return (
        count * costs.LEANSPHINCS_VERIFICATION
        + stark_count * costs.LEANSTARK_VERIFICATION
    )


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
        gas_limit=verification_gas(
            fork,
            sum(1 for d in dependencies if d[0] == Spec.LEANSPHINCS_SCHEME),
            stark_count=sum(
                1 for d in dependencies if d[0] == Spec.LEANSTARK_SCHEME
            ),
        ),
        state_gas_limit=0,
    )
    kwargs.update(overrides)
    return Frame(**kwargs)


def dependency_receipt(
    fork: Fork, count: int, *, stark_count: int = 0
) -> FrameReceipt:
    """
    Return the receipt of a dependency frame declaring `count` claims:
    success, its whole execution budget used, no state gas, no logs.
    """
    return FrameReceipt(
        status=Spec8141.STATUS_SUCCESS,
        gas_used=verification_gas(fork, count, stark_count=stark_count),
        state_gas_used=0,
        logs=[],
    )


def ordered_dependencies_hash(dependencies: Sequence[Dependency]) -> Hash:
    """
    Return `get_deps_hash` of `dependencies` in the given order:
    Keccak-256 over each claim's canonical 96-byte encoding.
    """
    return keccak256(encode_dependencies(dependencies))


def dependencies_hash(dependencies: Iterable[Dependency]) -> Hash:
    """Return `get_deps_hash` of the deduplicated, sorted claims."""
    return ordered_dependencies_hash(sorted(set(dependencies)))


def stored_proof(dependencies: Iterable[Dependency]) -> Bytes:
    """Return the stored dependency proof of a non-empty set of claims."""
    claims = sorted(set(dependencies))
    return Bytes(
        dependency_proof(
            encode_dependencies(claims), dependencies_hash(claims)
        )
    )


def expected_commitment(dependencies: Iterable[Dependency]) -> Header:
    """
    Return the header commitments of a block whose transactions declare
    `dependencies`: the hash of the empty proof when there are none.
    """
    claims: List[Dependency] = list(dependencies)
    proof = stored_proof(claims) if claims else Bytes(b"")
    return Header(
        dependency_proof_hash=keccak256(proof),
        block_deps_hash=dependencies_hash(claims),
    )
