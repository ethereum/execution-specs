"""Claim verifiers and the interface of accounts that sign messages."""

from typing import Optional, Protocol, SupportsBytes, runtime_checkable

from .base_types import Address, Bytes, Hash

SECP256K1_VERIFIER = Address(0x81A1)
"""
Placeholder address of the EIP-8141 claim-only secp256k1 protocol
verifier, which the EIP leaves to be assigned.
"""

P256_VERIFIER = Address(0x81A2)
"""
Placeholder address of the EIP-8141 claim-only P-256 protocol verifier.
"""

LEANSPHINCS_VERIFIER = Address(0x81A3)
"""
Placeholder address of the EIP-8141 claim-only leanSPHINCS protocol
verifier.
"""


@runtime_checkable
class Signer(SupportsBytes, Protocol):
    """
    An account able to sign messages.

    `bytes()` of a signer gives the key that identifies it in an
    [EIP-8141](https://eips.ethereum.org/EIPS/eip-8141) claim, i.e. its
    address for the secp256k1 and P-256 protocol verifiers.
    """

    @property
    def claim_verifier(self) -> Optional[Address]:
        """
        Return the protocol verifier that checks this signer's signatures
        natively, or `None` if none does.

        A signature scheme the protocol does not verify natively can still
        back a claim of a custom contract verifier.
        """
        ...

    @property
    def signature_length(self) -> int:
        """Return the length of the bytes returned by `sign_message`."""
        ...

    def sign_message(self, message: Hash) -> Bytes:
        """Sign `message` and return the raw signature bytes."""
        ...
