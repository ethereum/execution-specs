"""
Tests for the Keccak backend dispatch in `ethereum.crypto.hash`.

The module decides at import time whether to use hashlib (linked OpenSSL)
or pycryptodome, depending on whether `hashlib.new("keccak-256", ...)`
succeeds. These tests verify:

* both backends produce byte-identical output (cross-backend equivalence);
* the fallback engages cleanly when hashlib raises, simulated via
  monkeypatch so we can exercise the path on a Python whose OpenSSL does
  expose Keccak;
* on a Python where hashlib supports Keccak, the fast path is selected
  (guards against a regression where `algorithms_available` lies and the
  module silently forces every user onto pycryptodome).
"""

import hashlib
import importlib
from collections.abc import Iterator
from typing import Any
from unittest.mock import patch

import pytest

# Pre-NIST Keccak vectors. Empty-input digests are widely published; the
# `hashme` vector was confirmed against a working hashlib build during
# PR #2370 review.
KECCAK256_VECTORS: list[tuple[bytes, str]] = [
    (
        b"",
        "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470",
    ),
    (
        b"abc",
        "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45",
    ),
    (
        b"hashme",
        "7f98885dc9cf152c0bb08eaf056668f99c47cabd8fe01b1276f9a305b1389646",
    ),
]

KECCAK512_VECTORS: list[tuple[bytes, str]] = [
    (
        b"",
        "0eab42de4c3ceb9235fc91acffe746b29c29a8c366b7c60e4e67c466f36a4304"
        "c00fa9caf9d87976ba469bcbe06713b435f091ef2769fb160cdab33d3670680e",
    ),
]


def _hashlib_has_keccak() -> bool:
    """Return True if `hashlib.new("keccak-256", ...)` succeeds here."""
    try:
        hashlib.new("keccak-256")
    except ValueError:
        return False
    return True


def _clean_reimport_hash() -> Any:
    """Drop and reimport `ethereum.crypto.hash` for a fresh dispatch run."""
    mod = importlib.import_module("ethereum.crypto.hash")
    return importlib.reload(mod)


@pytest.fixture
def restore_hash_module() -> Iterator[None]:
    """Restore the natural-state `ethereum.crypto.hash` after each test."""
    yield
    _clean_reimport_hash()


@pytest.mark.parametrize("buffer, expected_hex", KECCAK256_VECTORS)
def test_keccak256_known_vectors(buffer: bytes, expected_hex: str) -> None:
    """Active backend produces published Keccak-256 digests."""
    from ethereum.crypto.hash import keccak256

    assert keccak256(buffer).hex() == expected_hex


@pytest.mark.parametrize("buffer, expected_hex", KECCAK512_VECTORS)
def test_keccak512_known_vectors(buffer: bytes, expected_hex: str) -> None:
    """Active backend produces published Keccak-512 digests."""
    from ethereum.crypto.hash import keccak512

    assert keccak512(buffer).hex() == expected_hex


def test_both_backends_agree() -> None:
    """Hashlib and pycryptodome produce byte-identical Keccak-256 output."""
    if not _hashlib_has_keccak():
        pytest.skip("hashlib lacks keccak-256 on this OpenSSL build")

    from Crypto.Hash import keccak as pyc_keccak

    inputs = [
        b"",
        b"x",
        b"\x00" * 64,
        bytes(range(256)),
        b"a" * 4096,
        b"\xff" * 65536,
    ]
    for buf in inputs:
        hl = hashlib.new("keccak-256", buf).digest()
        pc = pyc_keccak.new(digest_bits=256).update(buf).digest()
        assert hl == pc, f"backends disagree on input of length {len(buf)}"


def test_fallback_engages_when_hashlib_lacks_keccak(
    restore_hash_module: None,
) -> None:
    """If hashlib raises for Keccak, the module uses pycryptodome instead."""
    del restore_hash_module
    real_new = hashlib.new

    def mocked_new(name: str, *args: Any, **kwargs: Any) -> Any:
        if name in ("keccak-256", "keccak-512"):
            raise ValueError(f"unsupported hash type {name}")
        return real_new(name, *args, **kwargs)

    with patch.object(hashlib, "new", side_effect=mocked_new):
        h = _clean_reimport_hash()

        assert h._USE_HASHLIB is False, (
            "module did not engage pycryptodome fallback"
        )
        for buffer, expected_hex in KECCAK256_VECTORS:
            assert h.keccak256(buffer).hex() == expected_hex
        for buffer, expected_hex in KECCAK512_VECTORS:
            assert h.keccak512(buffer).hex() == expected_hex


def test_native_path_used_when_hashlib_has_keccak(
    restore_hash_module: None,
) -> None:
    """
    Verify hashlib path is selected when keccak-256 is supported.

    Guards against a regression where a bogus availability check (e.g.
    one that relied on `hashlib.algorithms_available`) would silently
    force every user onto the slower pycryptodome path.
    """
    del restore_hash_module
    if not _hashlib_has_keccak():
        pytest.skip("hashlib lacks keccak-256 on this OpenSSL build")

    h = _clean_reimport_hash()
    assert h._USE_HASHLIB is True, (
        "module engaged pycryptodome fallback despite hashlib having keccak"
    )


def test_eest_bytes_keccak256_matches_eels() -> None:
    """`Bytes.keccak256()` returns the same digest as EELS `keccak256`."""
    from ethereum.crypto.hash import keccak256

    from ..base_types import Bytes

    for buffer in (b"", b"hashme", bytes(range(256))):
        from_eest = bytes(Bytes(buffer).keccak256())
        from_eels = bytes(keccak256(buffer))
        assert from_eest == from_eels


def test_eest_trie_keccak256_matches_eels() -> None:
    """`trie.keccak256` and EELS `keccak256` return identical digests."""
    from ethereum.crypto.hash import keccak256 as eels

    from ...test_types.trie import keccak256 as trie

    for buffer in (b"", b"hashme", bytes(range(256))):
        assert bytes(trie(buffer)) == bytes(eels(buffer))
