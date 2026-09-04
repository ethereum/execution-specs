"""
Tests for the incremental Keccak-256 behind the RLPx frame MACs.

Two properties matter here and nothing else does. The hash has to be
Keccak-256 rather than SHA3-256, which differ only in a padding byte and
so agree on nothing - a session built on the wrong one fails its first
frame MAC. And `digest` has to leave the sponge absorbing, because the
MAC reads a tag out of it after every frame and then keeps going.
"""

import pytest

from ..keccak import Keccak256, keccak256

VECTORS = [
    (
        b"",
        "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470",
    ),
    (
        b"abc",
        "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45",
    ),
]
"""Keccak-256 of the empty string and of `abc`. SHA3-256 of the same
inputs differs in every byte, so these pin the padding rule."""

RATE_BYTES = 136
"""The Keccak-256 bitrate, where the sponge absorbs a block."""


class TestDigest:
    """The hash is Keccak-256, not SHA3-256."""

    @pytest.mark.parametrize("data, expected", VECTORS)
    def test_known_vector(self, data: bytes, expected: str) -> None:
        """A published digest is reproduced."""
        assert keccak256(data).hex() == expected

    def test_constructor_absorbs(self) -> None:
        """Data passed at construction is absorbed."""
        assert Keccak256(b"abc").digest() == keccak256(b"abc")


class TestIncrementalUse:
    """A digest is a peek: it must not finalize the sponge."""

    @pytest.mark.parametrize(
        "chunks",
        [
            [b"a", b"b", b"c"],
            [b"x" * RATE_BYTES, b"y" * RATE_BYTES],
            [b"x" * (RATE_BYTES - 1), b"y", b"z" * (RATE_BYTES + 1)],
            [b"", b"abc", b""],
        ],
        ids=["tiny", "whole_blocks", "block_boundary", "empty_updates"],
    )
    def test_digest_after_every_chunk(self, chunks: list[bytes]) -> None:
        """Peeking after each chunk agrees with hashing the whole."""
        sponge = Keccak256()
        absorbed = b""
        for chunk in chunks:
            sponge.update(chunk)
            absorbed += chunk
            assert sponge.digest() == keccak256(absorbed)

    def test_repeated_digest_is_stable(self) -> None:
        """Digesting twice without absorbing returns the same tag."""
        sponge = Keccak256(b"abc")
        assert sponge.digest() == sponge.digest()

    def test_chunking_does_not_change_the_digest(self) -> None:
        """A split update matches the same bytes absorbed at once."""
        data = bytes(range(256)) * 5
        split = Keccak256()
        for start in range(0, len(data), 7):
            split.update(data[start : start + 7])
        assert split.digest() == keccak256(data)
