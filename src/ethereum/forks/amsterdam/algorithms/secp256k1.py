"""
The secp256k1 algorithm defined from
EIP-7932 is defined here.
"""

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U8, U32, U64, U256

from ethereum.crypto import elliptic_curve
from ethereum.crypto.hash import keccak256
from ethereum.exceptions import InvalidSignatureError

from .algorithm import Algorithm
from .exceptions import AlgorithmValidationError

__all__ = ("Secp256k1",)

SECP256K1N = U256(
    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
)

SECP256K1_SIGNATURE_SIZE = 65


def secp256k1_unpack(  # noqa: D103
    signature: Bytes,
) -> tuple[U256, U256, U256]:
    r = U256.from_be_bytes(signature[0:32])
    s = U256.from_be_bytes(signature[32:64])
    y_parity = signature[64]
    return (r, s, U256(y_parity))


def secp256k1_validate(signature: Bytes) -> None:  # noqa: D103
    r, s, y_parity = secp256k1_unpack(signature)
    assert U256(0) < r < SECP256K1N
    assert U256(0) < s <= SECP256K1N // U256(2)
    assert y_parity in (0, 1)


class Secp256k1(Algorithm):  # noqa: D101
    @property
    def algorithm_type(self) -> U8:
        """
        The algorithm type / id that is prefixed to the
        start of signature data.
        """
        return U8(0xFF)

    @property
    def size(self) -> U32:
        """
        The size of all signatures produced by this
        algorithm.
        """
        return U32(SECP256K1_SIGNATURE_SIZE + 1)

    def gas_cost(self, signing_data: bytes) -> U64:
        """
        Get the gas cost of signing the data `signing_data`
        for this particular algorithm.
        """
        if len(signing_data) == 32:
            return U64(0)
        else:
            minimum_word_size = (len(signing_data) + 31) // 32
            return U64(30 + (6 * minimum_word_size))

    def validate(self, signature: bytes) -> None:
        """
        Check whether the signature is valid. For some
        algorithms, this may be a no-op. This function
        must always be called before `verify`.

        Throws:
          - AlgorithmValidationError
        """
        try:
            secp256k1_validate(signature[1:])
        except InvalidSignatureError as e:
            raise AlgorithmValidationError from e
        except AssertionError as e:
            raise AlgorithmValidationError from e

    def verify(self, signature: bytes, signing_data: bytes) -> bytes:
        """
        Take the signature and signing_data and return the
        public key of the signer.

        Throws:
          - AlgorithmVerificationError
        """
        if len(signing_data) != 32:
            signing_data = keccak256(signing_data)

        try:
            # For some reason the `elliptic_curve` library does **not**
            # return the 04 prefix.
            return b"\x04" + elliptic_curve.secp256k1_recover(
                *secp256k1_unpack(signature[1:]), Bytes32(signing_data)
            )
        except InvalidSignatureError as e:
            raise AlgorithmValidationError from e
