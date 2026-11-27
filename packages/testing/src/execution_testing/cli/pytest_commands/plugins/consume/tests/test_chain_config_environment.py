"""Tests for the chain configuration passed to hive clients."""

from types import SimpleNamespace
from typing import Any

import pytest

from execution_testing.base_types import Address
from execution_testing.fixtures.blockchain import FixtureConfig
from execution_testing.forks import Bogota

from ..simulators import multi_test_client, single_test_client
from ..simulators.helpers.chain_config import chain_config_environment
from .direct_calls import fixture_body

NO_ACCOUNTS = FixtureConfig(fork=Bogota)
TWO_ACCOUNTS = FixtureConfig(
    fork=Bogota,
    zero_nonce_storage_accounts=[Address(0x1000), Address(0x2000)],
)
GROUP = "0xgroup"


def test_no_zero_nonce_storage_accounts() -> None:
    """Pass nothing when the fixture names no accounts."""
    assert chain_config_environment(NO_ACCOUNTS) == {}


def test_zero_nonce_storage_accounts() -> None:
    """Pass the named accounts as a comma-separated address list."""
    assert chain_config_environment(TWO_ACCOUNTS) == {
        "HIVE_ZERO_NONCE_STORAGE_ACCOUNTS": (
            "0x0000000000000000000000000000000000001000,"
            "0x0000000000000000000000000000000000002000"
        ),
    }


@pytest.mark.parametrize(
    "config",
    [
        pytest.param(NO_ACCOUNTS, id="no_accounts"),
        pytest.param(TWO_ACCOUNTS, id="two_accounts"),
    ],
)
def test_single_test_client_environment(config: FixtureConfig) -> None:
    """A single-test client starts with its fixture's chain configuration."""
    environment = fixture_body(single_test_client.environment)(
        fixture=SimpleNamespace(fork=Bogota, config=config),
        check_live_port=8551,
    )
    base = single_test_client.client_environment(
        Bogota, int(config.chain_id), 8551
    )
    assert environment == {**base, **chain_config_environment(config)}


def _multi_test_client_environment(
    config: FixtureConfig, cache: dict[Any, dict]
) -> dict:
    """Return the multi-test client environment for a fixture of `GROUP`."""
    environment: dict = fixture_body(multi_test_client.environment)(
        pre_alloc_group=SimpleNamespace(fork=Bogota),
        fixture=SimpleNamespace(pre_hash=GROUP, config=config),
        check_live_port=8551,
        environment_cache=cache,
    )
    return environment


def test_multi_test_client_environment_without_chain_config() -> None:
    """
    A fixture with no chain configuration gets its group's cached
    environment itself, as every fixture did before.
    """
    cache: dict[Any, dict] = {}
    assert _multi_test_client_environment(NO_ACCOUNTS, cache) is cache[GROUP]


def test_multi_test_client_environment_adds_chain_config() -> None:
    """
    A fixture's chain configuration is added for that fixture only: the
    group's cached environment, shared by its other tests, stays free of
    it.
    """
    cache: dict[Any, dict] = {}
    environment = _multi_test_client_environment(TWO_ACCOUNTS, cache)
    variables = chain_config_environment(TWO_ACCOUNTS)
    assert environment == {**cache[GROUP], **variables}
    assert not variables.keys() & cache[GROUP].keys()
