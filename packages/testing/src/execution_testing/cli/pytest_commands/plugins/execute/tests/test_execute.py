"""Regression tests for execute plugin configuration."""

from types import SimpleNamespace
from typing import Any

from execution_testing.test_types.block_types import EnvironmentDefaults

from ..execute import pytest_configure


class FakeConfig:
    """Minimal config object for exercising execute plugin setup."""

    engine_rpc_supported: bool

    def __init__(self, *args: str) -> None:
        self.invocation_params = SimpleNamespace(args=args)
        self.option = SimpleNamespace(help=True)
        self.pluginmanager = SimpleNamespace(has_plugin=lambda _name: False)

    def getoption(self, name: str, default: Any = None) -> Any:
        """Return configured option values used by pytest_configure."""
        options = {
            "transaction_gas_limit": 7,
            "disable_html": False,
            "htmlpath": None,
            "markers": False,
            "collectonly": False,
            "show_ported_from": False,
            "links_as_filled": False,
            "help": True,
        }
        return options.get(name, default)


def test_pytest_configure_ignores_default_transaction_gas_limit() -> None:
    """Default execute options must not rewrite the global block gas limit."""
    original_gas_limit = EnvironmentDefaults.gas_limit

    config = FakeConfig()
    pytest_configure(config)  # type: ignore[arg-type]

    assert EnvironmentDefaults.gas_limit == original_gas_limit
    assert config.engine_rpc_supported is False


def test_pytest_configure_applies_explicit_transaction_gas_limit() -> None:
    """An explicit execute gas-limit override still updates the default."""
    original_gas_limit = EnvironmentDefaults.gas_limit

    config = FakeConfig("--transaction-gas-limit=7")
    pytest_configure(config)  # type: ignore[arg-type]

    assert EnvironmentDefaults.gas_limit == 7
    assert config.engine_rpc_supported is False

    EnvironmentDefaults.gas_limit = original_gas_limit
