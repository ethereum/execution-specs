"""Signature schemes and the interface of accounts that sign messages."""

from enum import IntEnum
from typing import Optional, Protocol, SupportsBytes, runtime_checkable

from .base_types import Bytes, Hash


class FrameSignatureScheme(IntEnum):
    """
    Scheme of a signature entry of an
    [EIP-8141](https://eips.ethereum.org/EIPS/eip-8141) frame transaction.
    """

    ARBITRARY = 0
    SECP256K1 = 1
    P256 = 2


@runtime_checkable
class Signer(SupportsBytes, Protocol):
    """
    An account able to sign messages.

    `bytes()` of a signer gives the bytes that identify it in a frame
    transaction signature entry, i.e. its address for the `SECP256K1` and
    `P256` schemes.
    """

    @property
    def signature_scheme(self) -> Optional[FrameSignatureScheme]:
        """
        Return the frame transaction signature scheme that verifies this
        signer's signatures natively, or `None` if no scheme does.

        A signature scheme the protocol does not verify natively, either
        in any fork or only before the fork that introduces it, can still
        sign `ARBITRARY` entries, which the account's code verifies.
        """
        ...

    @property
    def signature_length(self) -> int:
        """Return the length of the bytes returned by `sign_message`."""
        ...

    def sign_message(self, message: Hash) -> Bytes:
        """Sign `message` and return the raw signature bytes."""
        ...
