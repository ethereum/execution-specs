"""Tests for parsing the network name of fork-transition fixtures."""

from typing import Any, Dict

import pytest
from ethereum_rlp import rlp

from ethereum.fork_criteria import ByBlockNumber, ByTimestamp

from .helpers.load_blockchain_tests import (
    HEADER_NUMBER_INDEX,
    HEADER_TIMESTAMP_INDEX,
    ForkTransition,
)


def test_parse_timestamp_transition() -> None:
    """Parse a timestamp transition, expanding the `k` suffix."""
    transition = ForkTransition.parse("BPO2ToAmsterdamAtTime15k")

    assert transition is not None
    assert transition.from_fork == "BPO2"
    assert transition.to_fork == "Amsterdam"
    assert transition.criteria == ByTimestamp(15_000)


def test_parse_block_number_transition() -> None:
    """Parse a block number transition."""
    transition = ForkTransition.parse("BerlinToLondonAt5")

    assert transition is not None
    assert transition.from_fork == "Berlin"
    assert transition.to_fork == "London"
    assert transition.criteria == ByBlockNumber(5)


@pytest.mark.parametrize("network", ["Amsterdam", "Dao Fork", "EIP150"])
def test_parse_plain_fork_name(network: str) -> None:
    """Return `None` for a network that names a single fork."""
    assert ForkTransition.parse(network) is None


def decoded_block(number: int, timestamp: int) -> Dict[str, Any]:
    """Return a fixture block with a decoded header."""
    return {
        "blockHeader": {"number": hex(number), "timestamp": hex(timestamp)}
    }


def encoded_block(number: int, timestamp: int) -> Dict[str, Any]:
    """Return a fixture block that carries only its RLP."""
    header = [b""] * (HEADER_TIMESTAMP_INDEX + 1)
    header[HEADER_NUMBER_INDEX] = number.to_bytes(4, "big").lstrip(b"\0")
    header[HEADER_TIMESTAMP_INDEX] = timestamp.to_bytes(4, "big").lstrip(b"\0")
    return {"rlp": "0x" + rlp.encode([header, [], []]).hex()}


def test_activates_at_the_transition_timestamp() -> None:
    """Activate the second fork from the given timestamp on."""
    transition = ForkTransition.parse("BPO2ToAmsterdamAtTime15k")
    assert transition is not None

    assert not transition.activates(decoded_block(1, 14_999))
    assert transition.activates(decoded_block(2, 15_000))
    assert transition.activates(decoded_block(3, 15_001))


def test_activates_from_encoded_header() -> None:
    """Read the activation point from the RLP of an undecoded block."""
    transition = ForkTransition.parse("BPO2ToAmsterdamAtTime15k")
    assert transition is not None

    assert not transition.activates(encoded_block(1, 14_999))
    assert transition.activates(encoded_block(2, 15_000))


def test_activates_by_block_number() -> None:
    """Activate the second fork from the given block number on."""
    transition = ForkTransition.parse("BerlinToLondonAt5")
    assert transition is not None

    assert not transition.activates(decoded_block(4, 0))
    assert transition.activates(decoded_block(5, 0))
    assert transition.activates(encoded_block(6, 0))


def test_undecodable_block_does_not_activate() -> None:
    """Leave a block whose RLP does not decode to the fork before it."""
    transition = ForkTransition.parse("BPO2ToAmsterdamAtTime15k")
    assert transition is not None

    assert not transition.activates({"rlp": "0xc0"})
    assert not transition.activates({"rlp": "0xff"})
