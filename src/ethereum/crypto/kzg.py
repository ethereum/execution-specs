"""The KZG Implementation."""

from hashlib import sha256

from ethereum_types.bytes import Bytes32, Bytes48
from py_arkworks_bls12381 import GT, G1Point, G2Point, Scalar

from ethereum.utils.hexadecimal import hex_to_bytes

G1 = G1Point()  # Generator of G1
G2 = G2Point()  # Generator of G2


class KZGCommitment(Bytes48):
    """KZG commitment to a polynomial."""

    pass


class VersionedHash(Bytes32):
    """A versioned hash."""

    pass


VERSIONED_HASH_VERSION_KZG = hex_to_bytes("0x01")
BYTES_PER_COMMITMENT = 48
BYTES_PER_PROOF = 48
BYTES_PER_FIELD_ELEMENT = 32
KZG_SETUP_G2_MONOMIAL_1 = "0xb5bfd7dd8cdeb128843bc287230af38926187075cbfbefa81009a2ce615ac53d2914e5870cb452d2afaaab24f3499f72185cbfee53492714734429b7b38608e23926c911cceceac9a36851477ba4c60b087041de621000edc98edada20c1def2"  # noqa: E501
KZG_SETUP_G2_1 = G2Point.from_compressed_bytes(
    hex_to_bytes(KZG_SETUP_G2_MONOMIAL_1)
)


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

    # Validate and deserialize G1 points
    # Note: Points must be in the prime-ordered subgroup
    commitment = G1Point.from_compressed_bytes(commitment_bytes)
    proof = G1Point.from_compressed_bytes(proof_bytes)

    # Validate and convert scalars
    # Note: Scalars must be canonical
    z = Scalar.from_be_bytes(z_bytes)
    y = Scalar.from_be_bytes(y_bytes)

    # Verify: P - y = Q * (X - z)
    X_minus_z = KZG_SETUP_G2_1 - G2 * z
    P_minus_y = commitment - G1 * y
    return GT.pairing_check(
        [P_minus_y, proof],
        [-G2, X_minus_z],
    )
