"""Signature schemes and the interface of accounts that sign messages."""

from enum import IntEnum
from typing import Protocol, Sequence

from .base_types import Bytes, Hash


class FrameSignatureScheme(IntEnum):
    """
    Scheme of a signature entry of an
    [EIP-8141](https://eips.ethereum.org/EIPS/eip-8141) frame transaction.
    """

    ARBITRARY = 0
    SECP256K1 = 1
    P256 = 2


class Signer(Protocol):
    """An account able to sign messages."""

    @property
    def signature_schemes(self) -> Sequence[FrameSignatureScheme]:
        """
        Return the frame transaction signature schemes this signer can sign
        for, in order of preference.
        """
        ...

    def sign_message(self, message: Hash) -> Bytes:
        """Sign `message` and return the raw signature bytes."""
        ...
