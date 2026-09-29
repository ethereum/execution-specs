"""Tests for parsing the network name of fork-transition fixtures."""

from typing import Any, Dict

import pytest

from ethereum.fork_criteria import ByBlockNumber, ByTimestamp

from . import FORKS
from .helpers.load_blockchain_tests import TRANSITION_FORKS, ForkTransition


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


@pytest.mark.parametrize("network", sorted(TRANSITION_FORKS))
def test_every_transition_fork_names_known_forks(network: str) -> None:
    """Map both ends of every transition fork to a fork of the spec."""
    transition = ForkTransition.parse(network)

    assert transition is not None
    assert transition.from_fork in FORKS
    assert transition.to_fork in FORKS


def decoded_block(number: int, timestamp: int) -> Dict[str, Any]:
    """Return a fixture block with a decoded header."""
    return {
        "blockHeader": {
            "coinbase": "0x" + "00" * 20,
            "stateRoot": "0x" + "00" * 32,
            "number": hex(number),
            "gasLimit": "0x00",
            "timestamp": hex(timestamp),
            "extraData": "0x",
        }
    }


def invalid_block(number: int, timestamp: int) -> Dict[str, Any]:
    """Return a fixture block that is expected to be rejected."""
    return {"rlp": "0x", "rlp_decoded": decoded_block(number, timestamp)}


def test_activates_at_the_transition_timestamp() -> None:
    """Activate the second fork from the given timestamp on."""
    transition = ForkTransition.parse("BPO2ToAmsterdamAtTime15k")
    assert transition is not None

    assert not transition.activates(decoded_block(1, 14_999))
    assert transition.activates(decoded_block(2, 15_000))
    assert transition.activates(decoded_block(3, 15_001))


def test_activates_from_decoded_invalid_block() -> None:
    """Read the activation point from an invalid block's decoded header."""
    transition = ForkTransition.parse("BPO2ToAmsterdamAtTime15k")
    assert transition is not None

    assert not transition.activates(invalid_block(1, 14_999))
    assert transition.activates(invalid_block(2, 15_000))


def test_activates_by_block_number() -> None:
    """Activate the second fork from the given block number on."""
    transition = ForkTransition.parse("BerlinToLondonAt5")
    assert transition is not None

    assert not transition.activates(decoded_block(4, 0))
    assert transition.activates(decoded_block(5, 0))
    assert transition.activates(invalid_block(6, 0))


def test_undecodable_block_does_not_activate() -> None:
    """Leave a block without a decoded header to the fork before it."""
    transition = ForkTransition.parse("BPO2ToAmsterdamAtTime15k")
    assert transition is not None

    assert not transition.activates({"rlp": "0xc0"})


@pytest.mark.parametrize("timestamp", [2**256, 2**300])
def test_oversized_timestamp_does_not_activate(timestamp: int) -> None:
    """Leave a header with a timestamp above `U256` to the fork before it."""
    transition = ForkTransition.parse("BPO2ToAmsterdamAtTime15k")
    assert transition is not None

    assert not transition.activates(decoded_block(2, timestamp))
    assert not transition.activates(invalid_block(2, timestamp))


@pytest.mark.parametrize("number, timestamp", [(-1, 15_000), (2, -1)])
def test_negative_header_value_does_not_activate(
    number: int, timestamp: int
) -> None:
    """Leave negative activation values to the fork before the transition."""
    transition = ForkTransition.parse("BPO2ToAmsterdamAtTime15k")
    assert transition is not None

    assert not transition.activates(decoded_block(number, timestamp))
    assert not transition.activates(invalid_block(number, timestamp))
