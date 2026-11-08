"""Tests for deselecting tests of forks that a client doesn't support."""

import pytest

from execution_testing.cli.pytest_commands.plugins.consume.consume import (
    is_fork_supported_by_client,
)
from execution_testing.forks import (
    Berlin,
    BerlinToLondonAt5,
    Fork,
    Frontier,
    London,
    Paris,
    ParisToShanghaiAtTime15k,
    Prague,
    TransitionFork,
)


@pytest.mark.parametrize(
    "client_name",
    ["ethrex", "ethrex_default"],
)
@pytest.mark.parametrize(
    "fork,supported",
    [
        (Frontier, False),
        (Berlin, False),
        (London, False),
        (BerlinToLondonAt5, False),
        (Paris, True),
        (ParisToShanghaiAtTime15k, True),
        (Prague, True),
        (None, True),
    ],
)
def test_ethrex_supports_paris_and_later(
    client_name: str, fork: Fork | TransitionFork | None, supported: bool
) -> None:
    """Ethrex doesn't support pre-merge forks, with or without a nametag."""
    assert is_fork_supported_by_client(client_name, fork) is supported


@pytest.mark.parametrize(
    "client_name", ["go-ethereum", "besu_default", "collect-only"]
)
def test_other_clients_support_every_fork(client_name: str) -> None:
    """Clients without an oldest supported fork run every fork."""
    assert is_fork_supported_by_client(client_name, Frontier)
