"""
Incremental Keccak-256 used by the RLPx frame MACs.

The RLPx transport keeps a running Keccak-256 state per direction, and
reads a digest from it after every frame *without* finalizing it.
``hashlib`` cannot, since it implements SHA3, a different padding rule.
``pycryptodome`` can when built with ``update_after_digest``, and its
compiled sponge MACs a multi-megabyte frame in time; a pure-Python
sponge is too slow for a syncing client to wait for.
"""

from Crypto.Hash import keccak as _pycryptodome_keccak


class Keccak256:
    """
    A Keccak-256 sponge that can be digested and then updated again.

    `digest` leaves the absorbing state untouched, which is what allows a
    single instance to act as the running egress or ingress MAC of an
    RLPx connection.
    """

    def __init__(self, data: bytes = b"") -> None:
        """Initialize the sponge, optionally absorbing `data`."""
        self._hash = _pycryptodome_keccak.new(
            digest_bits=256, update_after_digest=True
        )
        self.update(data)

    def update(self, data: bytes) -> None:
        """Absorb `data` into the sponge."""
        self._hash.update(data)

    def digest(self) -> bytes:
        """
        Return the 32 byte digest of everything absorbed so far.

        The sponge remains usable: further `update` calls continue from
        the pre-padding state.
        """
        return bytes(self._hash.digest())


def keccak256(data: bytes) -> bytes:
    """Return the Keccak-256 digest of `data`."""
    return Keccak256(data).digest()
