import importlib
import json
from typing import Any

import pytest
from ethereum_types.bytes import Bytes

from ethereum.utils.hexadecimal import (
    has_hex_prefix,
    hex_to_bytes,
    remove_hex_prefix,
)

from . import FORKS, TEST_FIXTURES

FIXTURE_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]

forks = FORKS.keys()


def to_bytes(data: str) -> Bytes:
    if data is None:
        return b""
    if has_hex_prefix(data):
        return hex_to_bytes(data)

    return data.encode()


@pytest.mark.parametrize("fork", forks)
def test_trie_secure_hex(fork: str) -> None:
    tests = load_tests("hex_encoded_securetrie_test.json")

    package = FORKS[fork]["package"]
    trie_module = importlib.import_module(f"ethereum.{package}.trie")

    for name, test in tests.items():
        st = trie_module.Trie(secured=True, default=b"")
        for k, v in test.get("in").items():
            trie_module.trie_set(st, to_bytes(k), to_bytes(v))
        result = trie_module.root(st)
        expected = remove_hex_prefix(test.get("root"))
        assert result.hex() == expected, f"test {name} failed"


@pytest.mark.parametrize("fork", forks)
def test_trie_secure(fork: str) -> None:
    tests = load_tests("trietest_secureTrie.json")

    package = FORKS[fork]["package"]
    trie_module = importlib.import_module(f"ethereum.{package}.trie")

    for name, test in tests.items():
        st = trie_module.Trie(secured=True, default=b"")
        for t in test.get("in"):
            trie_module.trie_set(st, to_bytes(t[0]), to_bytes(t[1]))
        result = trie_module.root(st)
        expected = remove_hex_prefix(test.get("root"))
        assert result.hex() == expected, f"test {name} failed"


@pytest.mark.parametrize("fork", forks)
def test_trie_secure_any_order(fork: str) -> None:
    tests = load_tests("trieanyorder_secureTrie.json")

    package = FORKS[fork]["package"]
    trie_module = importlib.import_module(f"ethereum.{package}.trie")

    for name, test in tests.items():
        st = trie_module.Trie(secured=True, default=b"")
        for k, v in test.get("in").items():
            trie_module.trie_set(st, to_bytes(k), to_bytes(v))
        result = trie_module.root(st)
        expected = remove_hex_prefix(test.get("root"))
        assert result.hex() == expected, f"test {name} failed"


@pytest.mark.parametrize("fork", forks)
def test_trie(fork: str) -> None:
    tests = load_tests("trietest.json")

    package = FORKS[fork]["package"]
    trie_module = importlib.import_module(f"ethereum.{package}.trie")

    for name, test in tests.items():
        st = trie_module.Trie(secured=False, default=b"")
        for t in test.get("in"):
            trie_module.trie_set(st, to_bytes(t[0]), to_bytes(t[1]))
        result = trie_module.root(st)
        expected = remove_hex_prefix(test.get("root"))
        assert result.hex() == expected, f"test {name} failed"


@pytest.mark.parametrize("fork", forks)
def test_trie_any_order(fork: str) -> None:
    tests = load_tests("trieanyorder.json")

    package = FORKS[fork]["package"]
    trie_module = importlib.import_module(f"ethereum.{package}.trie")

    for name, test in tests.items():
        st = trie_module.Trie(secured=False, default=b"")
        for k, v in test.get("in").items():
            trie_module.trie_set(st, to_bytes(k), to_bytes(v))
        result = trie_module.root(st)
        expected = remove_hex_prefix(test.get("root"))
        assert result.hex() == expected, f"test {name} failed"


def load_tests(path: str) -> Any:
    with open(f"{FIXTURE_PATH}/TrieTests/" + path) as f:
        tests = json.load(f)

    return tests
