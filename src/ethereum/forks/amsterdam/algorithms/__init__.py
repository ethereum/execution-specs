"""
The algorithm registry was introduced via EIP-7932.

TODO: The docs
"""

from ethereum_types.bytes import Bytes, Bytes20
from ethereum_types.numeric import U8, Uint

from ethereum.crypto.hash import keccak256

from .secp256k1 import Secp256k1

__all__ = (
    "calculate_penalty",
    "validate_signature",
    "verify_signature",
    "algorithm_registry",
    "pubkey_to_address",
)


algorithm_registry = {
    algorithm.algorithm_type: algorithm for algorithm in [Secp256k1()]
}


def calculate_penalty(algorithm: U8, signing_data: Bytes) -> Uint:
    """
    Calculate the gas cost of the signature signing over `signing_data`
    with an algorithm of id `algorithm`.
    """
    assert algorithm in algorithm_registry

    algorithm_impl = algorithm_registry[algorithm]

    return Uint(algorithm_impl.gas_cost(signing_data))


def validate_signature(signature: Bytes) -> None:
    """
    Ensure that the `signature` is valid by itself,
    this should be called before `verify_signature`.
    """
    assert len(signature) > 0
    assert U8(signature[0]) in algorithm_registry

    algorithm = algorithm_registry[U8(signature[0])]

    return algorithm.validate(signature)


def verify_signature(signing_data: Bytes, signature: Bytes) -> Bytes:
    """
    Do the expensive signature validation, validate_signature(signature)
    should be called before this function.
    """
    algorithm = algorithm_registry[U8(signature[0])]

    return algorithm.verify(signature, signing_data)


ExecutionAddress = Bytes20


def pubkey_to_address(public_key: Bytes, algorithm_id: U8) -> ExecutionAddress:
    """
    Take a given public key and algorithm id and return the
    address of the signer.
    """
    # Compatibility shim to ensure backwards compatibility
    if int(algorithm_id) == 0xFF:
        return ExecutionAddress(keccak256(public_key[1:])[12:])

    return ExecutionAddress(keccak256(bytes(algorithm_id) + public_key)[12:])
