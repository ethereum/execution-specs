"""Chain configuration for consume hive simulators beyond the fork rules."""

from typing import Dict

from execution_testing.fixtures.blockchain import FixtureConfig


def chain_config_environment(config: FixtureConfig) -> Dict[str, str]:
    """
    Return the hive environment for the fixture's chain configuration
    that the fork rules do not carry.

    The EIP-8253 zero-nonce storage accounts are passed as a
    comma-separated address list, only when the fixture names any.
    """
    if not config.zero_nonce_storage_accounts:
        return {}
    return {
        "HIVE_ZERO_NONCE_STORAGE_ACCOUNTS": ",".join(
            str(address) for address in config.zero_nonce_storage_accounts
        ),
    }
