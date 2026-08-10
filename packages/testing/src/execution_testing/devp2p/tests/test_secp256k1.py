"""
Tests for the secp256k1 agreement behind the RLPx shared secrets.

The agreement is checked against an independent oracle: the x
coordinate of `a * (b * G)` equals that of `(a * b mod n) * G`, which
`spec256k1` computes as an ordinary public key.
"""

import os

import pytest

from ..secp256k1 import agree, public_key_bytes

CURVE_ORDER = (
    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
)
"""The order `n` of the secp256k1 group."""


def _scalar(value: int) -> bytes:
    """Return `value` as a 32 byte private key."""
    return value.to_bytes(32, "big")


def _oracle(private_key: bytes, other_private_key: bytes) -> bytes:
    """Return the shared x coordinate computed from both private keys."""
    product = (
        int.from_bytes(private_key, "big")
        * int.from_bytes(other_private_key, "big")
        % CURVE_ORDER
    )
    return public_key_bytes(_scalar(product))[:32]


class TestAgree:
    """The agreement RLPx derives its secrets from."""

    def test_random_pairs_match_the_oracle(self) -> None:
        """Random key pairs agree on the oracle's shared secret."""
        for _ in range(64):
            ours, theirs = os.urandom(32), os.urandom(32)
            shared = agree(ours, public_key_bytes(theirs))
            assert len(shared) == 32
            assert shared == _oracle(ours, theirs)
            assert shared == agree(theirs, public_key_bytes(ours))

    def test_a_fixed_pair(self) -> None:
        """
        Keys 1 and 2 share the x coordinate of 2G.

        A fixed vector pins the byte order and length of the output.
        """
        assert agree(
            _scalar(1), public_key_bytes(_scalar(2))
        ) == bytes.fromhex(
            "c6047f9441ed7d6d3045406e95c07cd85c778e4b8cef3ca7abac09b95c709ee5"
        )

    def test_a_point_off_the_curve_is_refused(self) -> None:
        """A foreign key that is not a curve point raises."""
        with pytest.raises(ValueError):
            agree(_scalar(1), b"\x00" * 63 + b"\x01")

    def test_a_key_of_the_wrong_length_is_refused(self) -> None:
        """A foreign key that is not 64 bytes raises."""
        with pytest.raises(ValueError, match="expected 64"):
            agree(_scalar(1), public_key_bytes(_scalar(2))[:63])
