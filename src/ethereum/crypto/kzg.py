"""
The KZG Implementation
^^^^^^^^^^^^^^^^^^^^^^
"""
from hashlib import sha256
from typing import Tuple

from eth_typing.bls import BLSPubkey, BLSSignature
from ethereum_types.bytes import Bytes32, Bytes48, Bytes96
from ethereum_types.numeric import U256
from py_ecc.bls import G2ProofOfPossession
from py_ecc.bls.g2_primitives import pubkey_to_G1, signature_to_G2
from py_ecc.fields import optimized_bls12_381_FQ, optimized_bls12_381_FQ2
from py_ecc.fields import optimized_bls12_381_FQ12 as FQ12
from py_ecc.optimized_bls12_381 import add, multiply, neg
from py_ecc.optimized_bls12_381.optimized_curve import G1, G2
from py_ecc.optimized_bls12_381.optimized_pairing import (
    final_exponentiate,
    pairing,
)

from ethereum.utils.hexadecimal import hex_to_bytes

FQ = Tuple[
    optimized_bls12_381_FQ, optimized_bls12_381_FQ, optimized_bls12_381_FQ
]
FQ2 = Tuple[
    optimized_bls12_381_FQ2, optimized_bls12_381_FQ2, optimized_bls12_381_FQ2
]


class KZGCommitment(Bytes48):
    """KZG commitment to a polynomial."""

    pass


class KZGProof(Bytes48):
    """KZG proof"""

    pass


class BLSFieldElement(U256):
    """A field element in the BLS12-381 field."""

    pass


class VersionedHash(Bytes32):
    """A versioned hash."""

    pass


class G2Point(Bytes96):
    """A point in G2."""

    pass


VERSIONED_HASH_VERSION_KZG = hex_to_bytes("0x01")
BYTES_PER_COMMITMENT = 48
BYTES_PER_PROOF = 48
BYTES_PER_FIELD_ELEMENT = 32
G1_POINT_AT_INFINITY = b"\xc0" + b"\x00" * 47
BLS_MODULUS = BLSFieldElement(
    52435875175126190479447740508185965837690552500527637822603658699938581184513  # noqa: E501
)
KZG_SETUP_G2_LENGTH = 65
KZG_SETUP_G2_MONOMIAL_1 = "0xb5bfd7dd8cdeb128843bc287230af38926187075cbfbefa81009a2ce615ac53d2914e5870cb452d2afaaab24f3499f72185cbfee53492714734429b7b38608e23926c911cceceac9a36851477ba4c60b087041de621000edc98edada20c1def2"  # noqa: E501


def kzg_commitment_to_versioned_hash(
    kzg_commitment: KZGCommitment,
) -> VersionedHash:
    """
    Convert a KZG commitment to a versioned hash.
    """
    return VersionedHash(
        VERSIONED_HASH_VERSION_KZG
        + Bytes32(sha256(kzg_commitment).digest())[1:]
    )


def validate_kzg_g1(b: Bytes48) -> None:
    """
    Perform BLS validation required by the types `KZGProof`
    and `KZGCommitment`.
    """
    if b == G1_POINT_AT_INFINITY:
        return

    assert G2ProofOfPossession.KeyValidate(BLSPubkey(b))


def bytes_to_kzg_commitment(b: Bytes48) -> KZGCommitment:
    """
    Convert untrusted bytes into a trusted and validated KZGCommitment.
    """
    validate_kzg_g1(b)
    return KZGCommitment(b)


def bytes_to_bls_field(b: Bytes32) -> BLSFieldElement:
    """
    Convert untrusted bytes to a trusted and validated BLS scalar
    field element. This function does not accept inputs greater than
    the BLS modulus.
    """
    field_element = int.from_bytes(b, "big")
    assert field_element < int(BLS_MODULUS)
    return BLSFieldElement(field_element)


def bytes_to_kzg_proof(b: Bytes48) -> KZGProof:
    """
    Convert untrusted bytes into a trusted and validated KZGProof.
    """
    validate_kzg_g1(b)
    return KZGProof(b)


def pairing_check(values: Tuple[Tuple[FQ, FQ2], Tuple[FQ, FQ2]]) -> bool:
    """
    Check if the pairings are valid.
    """
    p_q_1, p_q_2 = values
    final_exponentiation = final_exponentiate(
        pairing(p_q_1[1], p_q_1[0], final_exponentiate=False)
        * pairing(p_q_2[1], p_q_2[0], final_exponentiate=False)
    )
    return final_exponentiation == FQ12.one()


def verify_kzg_proof(
    commitment_bytes: Bytes48,
    z_bytes: Bytes32,
    y_bytes: Bytes32,
    proof_bytes: Bytes48,
) -> bool:
    """
    Verify KZG proof that ``p(z) == y`` where ``p(z)``
    is the polynomial represented by ``polynomial_kzg``.
    Receives inputs as bytes.
    Public method.
    """
    assert len(commitment_bytes) == BYTES_PER_COMMITMENT
    assert len(z_bytes) == BYTES_PER_FIELD_ELEMENT
    assert len(y_bytes) == BYTES_PER_FIELD_ELEMENT
    assert len(proof_bytes) == BYTES_PER_PROOF

    return verify_kzg_proof_impl(
        bytes_to_kzg_commitment(commitment_bytes),
        bytes_to_bls_field(z_bytes),
        bytes_to_bls_field(y_bytes),
        bytes_to_kzg_proof(proof_bytes),
    )


def verify_kzg_proof_impl(
    commitment: KZGCommitment,
    z: BLSFieldElement,
    y: BLSFieldElement,
    proof: KZGProof,
) -> bool:
    """
    Verify KZG proof that ``p(z) == y`` where ``p(z)``
    is the polynomial represented by ``polynomial_kzg``.
    """
    # Verify: P - y = Q * (X - z)
    X_minus_z = add(
        signature_to_G2(BLSSignature(hex_to_bytes(KZG_SETUP_G2_MONOMIAL_1))),
        multiply(G2, int((BLS_MODULUS - z) % BLS_MODULUS)),
    )
    P_minus_y = add(
        pubkey_to_G1(BLSPubkey(commitment)),
        multiply(G1, int((BLS_MODULUS - y) % BLS_MODULUS)),
    )
    return pairing_check(
        (
            (P_minus_y, neg(G2)),
            (pubkey_to_G1(BLSPubkey(proof)), X_minus_z),
        )
    )
