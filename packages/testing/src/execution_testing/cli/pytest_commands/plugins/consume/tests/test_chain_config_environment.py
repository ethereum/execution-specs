"""Tests for the chain configuration passed to hive clients."""

from execution_testing.base_types import Address
from execution_testing.fixtures.blockchain import FixtureConfig
from execution_testing.forks import Bogota

from ..simulators.helpers.chain_config import chain_config_environment


def test_no_zero_nonce_storage_accounts() -> None:
    """Pass nothing when the fixture names no accounts."""
    assert chain_config_environment(FixtureConfig(fork=Bogota)) == {}


def test_zero_nonce_storage_accounts() -> None:
    """Pass the named accounts as a comma-separated address list."""
    config = FixtureConfig(
        fork=Bogota,
        zero_nonce_storage_accounts=[Address(0x1000), Address(0x2000)],
    )
    assert chain_config_environment(config) == {
        "HIVE_ZERO_NONCE_STORAGE_ACCOUNTS": (
            "0x0000000000000000000000000000000000001000,"
            "0x0000000000000000000000000000000000002000"
        ),
    }
