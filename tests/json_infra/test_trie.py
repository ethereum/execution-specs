import importlib
import json
from typing import Any, Optional

import pytest
from ethereum_types.bytes import Bytes

from ethereum.utils.hexadecimal import has_hex_prefix, hex_to_bytes

from . import FORKS, TEST_FIXTURES

FIXTURE_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]

forks = FORKS.keys()


def to_bytes(data: Optional[str]) -> Bytes:
    if data is None:
        return b""
    if has_hex_prefix(data):
        return hex_to_bytes(data)

    return data.encode()


@pytest.mark.parametrize("fork", forks)
def test_trie_secure_hex(fork: str) -> None:
    tests = load_tests("hex_encoded_securetrie_test.json")

    eels_fork = FORKS[fork]["eels_fork"]
    trie_module = importlib.import_module(f"ethereum.{eels_fork}.trie")

    for name, test in tests.items():
        st = trie_module.Trie(secured=True, default=b"")
        for k, v in test.get("in").items():
            trie_module.trie_set(st, to_bytes(k), to_bytes(v))
        result = trie_module.root(st)
        expected = hex_to_bytes(test.get("root"))
        assert result == expected, f"test {name} failed"


@pytest.mark.parametrize("fork", forks)
def test_trie_secure(fork: str) -> None:
    tests = load_tests("trietest_secureTrie.json")

    eels_fork = FORKS[fork]["eels_fork"]
    trie_module = importlib.import_module(f"ethereum.{eels_fork}.trie")

    for name, test in tests.items():
        st = trie_module.Trie(secured=True, default=b"")
        for t in test.get("in"):
            trie_module.trie_set(st, to_bytes(t[0]), to_bytes(t[1]))
        result = trie_module.root(st)
        expected = hex_to_bytes(test.get("root"))
        assert result == expected, f"test {name} failed"


@pytest.mark.parametrize("fork", forks)
def test_trie_secure_any_order(fork: str) -> None:
    tests = load_tests("trieanyorder_secureTrie.json")

    eels_fork = FORKS[fork]["eels_fork"]
    trie_module = importlib.import_module(f"ethereum.{eels_fork}.trie")

    for name, test in tests.items():
        st = trie_module.Trie(secured=True, default=b"")
        for k, v in test.get("in").items():
            trie_module.trie_set(st, to_bytes(k), to_bytes(v))
        result = trie_module.root(st)
        expected = hex_to_bytes(test.get("root"))
        assert result == expected, f"test {name} failed"


@pytest.mark.parametrize("fork", forks)
def test_trie(fork: str) -> None:
    tests = load_tests("trietest.json")

    eels_fork = FORKS[fork]["eels_fork"]
    trie_module = importlib.import_module(f"ethereum.{eels_fork}.trie")

    for name, test in tests.items():
        st = trie_module.Trie(secured=False, default=b"")
        for t in test.get("in"):
            trie_module.trie_set(st, to_bytes(t[0]), to_bytes(t[1]))
        result = trie_module.root(st)
        expected = hex_to_bytes(test.get("root"))
        assert result == expected, f"test {name} failed"


@pytest.mark.parametrize("fork", forks)
def test_trie_any_order(fork: str) -> None:
    tests = load_tests("trieanyorder.json")

    eels_fork = FORKS[fork]["eels_fork"]
    trie_module = importlib.import_module(f"ethereum.{eels_fork}.trie")

    for name, test in tests.items():
        st = trie_module.Trie(secured=False, default=b"")
        for k, v in test.get("in").items():
            trie_module.trie_set(st, to_bytes(k), to_bytes(v))
        result = trie_module.root(st)
        expected = hex_to_bytes(test.get("root"))
        assert result == expected, f"test {name} failed"


def load_tests(path: str) -> Any:
    with open(f"{FIXTURE_PATH}/TrieTests/" + path) as f:
        tests = json.load(f)

    return tests
