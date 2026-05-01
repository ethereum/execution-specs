"""Tests for hardfork discovery helpers."""

import pytest

from ethereum_spec_tools.forks import Hardfork


class CustomHardfork(Hardfork):
    """Hardfork subclass used to test generic class methods."""


def test_by_short_name_returns_matching_hardfork() -> None:
    """Return the hardfork matching the requested short name."""
    fork = Hardfork.by_short_name("frontier")

    assert fork.short_name == "frontier"
    assert fork.name == "ethereum.forks.frontier"


def test_by_short_name_preserves_subclass() -> None:
    """Return the same hardfork subclass used for lookup."""
    fork = CustomHardfork.by_short_name("frontier")

    assert isinstance(fork, CustomHardfork)
    assert fork.short_name == "frontier"


def test_by_short_name_rejects_unknown_fork() -> None:
    """Raise an error when the hardfork short name is unknown."""
    with pytest.raises(ValueError, match="unknown hardfork `unknown_fork`"):
        Hardfork.by_short_name("unknown_fork")
