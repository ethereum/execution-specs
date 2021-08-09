import json
from typing import Any

from ethereum.frontier.eth_types import Bytes
from ethereum.frontier.trie import map_keys, root
from ethereum.utils.hexadecimal import (
    has_hex_prefix,
    hex_to_bytes,
    remove_hex_prefix,
)


def to_bytes(data: str) -> Bytes:
    if data is None:
        return b""
    if has_hex_prefix(data):
        return hex_to_bytes(data)

    return data.encode()


def test_trie_secure_hex() -> None:
    tests = load_tests("hex_encoded_securetrie_test.json")

    for (name, test) in tests.items():
        normalized = {}
        for (k, v) in test.get("in").items():
            normalized[to_bytes(k)] = to_bytes(v)

        result = root(map_keys(normalized))
        expected = remove_hex_prefix(test.get("root"))
        assert result.hex() == expected, f"test {name} failed"


def test_trie_secure() -> None:
    tests = load_tests("trietest_secureTrie.json")

    for (name, test) in tests.items():
        normalized = {}
        for t in test.get("in"):
            normalized[to_bytes(t[0])] = to_bytes(t[1])

        result = root(map_keys(normalized))
        expected = remove_hex_prefix(test.get("root"))
        assert result.hex() == expected, f"test {name} failed"


def test_trie_secure_any_order() -> None:
    tests = load_tests("trieanyorder_secureTrie.json")

    for (name, test) in tests.items():
        normalized = {}
        for (k, v) in test.get("in").items():
            normalized[to_bytes(k)] = to_bytes(v)

        result = root(map_keys(normalized))
        expected = remove_hex_prefix(test.get("root"))
        assert result.hex() == expected, f"test {name} failed"


def test_trie() -> None:
    tests = load_tests("trietest.json")

    for (name, test) in tests.items():
        normalized = {}
        for t in test.get("in"):
            normalized[to_bytes(t[0])] = to_bytes(t[1])

        result = root(map_keys(normalized, secured=False))
        expected = remove_hex_prefix(test.get("root"))
        assert result.hex() == expected, f"test {name} failed"


def test_trie_any_order() -> None:
    tests = load_tests("trieanyorder.json")

    for (name, test) in tests.items():
        normalized = {}
        for (k, v) in test.get("in").items():
            normalized[to_bytes(k)] = to_bytes(v)

        result = root(map_keys(normalized, secured=False))
        expected = remove_hex_prefix(test.get("root"))
        assert result.hex() == expected, f"test {name} failed"


def load_tests(path: str) -> Any:
    with open("tests/fixtures/TrieTests/" + path) as f:
        tests = json.load(f)

    return tests
