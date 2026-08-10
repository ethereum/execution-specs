"""
Incremental Keccak-256 used by the RLPx frame MACs.

The RLPx transport keeps a running Keccak-256 state per direction, and
reads a digest from it after every frame *without* finalizing it.
``hashlib`` cannot express that at all, since it implements SHA3, a
different padding rule. ``pycryptodome`` can, but only when asked: a
Keccak hash built with ``update_after_digest`` pads and squeezes a copy
of the sponge, leaving the absorbing state free to take the next frame.

That flag is worth the note it takes to explain, because the tempting
alternative - a hand-rolled pure-Python sponge - absorbs at roughly
0.2 MiB/s, some 880 times slower than pycryptodome's compiled Keccak.
At that rate, MAC-ing one frame carrying an eight mebibyte EIP-7934
block takes the best part of a minute, long enough for a syncing
client to give up on the peer and drop it mid-transfer.
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
