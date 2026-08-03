"""Regression tests for execute plugin configuration."""

from types import SimpleNamespace
from typing import Any

import pytest

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


EXECUTE_COLLECTION_PLUGINS = [
    "execution_testing.cli.pytest_commands.plugins.shared.execute_fill",
    "execution_testing.cli.pytest_commands.plugins.shared.live_client_flags",
    "execution_testing.cli.pytest_commands.plugins.execute.execute",
    "execution_testing.cli.pytest_commands.plugins.forks.forks",
]


def test_forkless_items_pruned_before_filter_combinations(
    pytester: pytest.Pytester,
) -> None:
    """
    Collect a test that is not valid for the session's fork in execute mode.

    Such a test is collected without a fork parametrization and hence
    without its covariant params; it must be pruned before the forks
    plugin evaluates filter_combinations predicates, which would
    otherwise fail with a TypeError and abort the whole session.
    """
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.parametrize("a", [1, 2])
        @pytest.mark.with_all_refund_types()
        @pytest.mark.filter_combinations(
            lambda refund_type, a, **_: True,
            reason="requires the covariant refund_type param",
        )
        @pytest.mark.valid_from("Amsterdam")
        def test_case(state_test, refund_type, a):
            pass
        """
    )
    plugin_args = [
        arg for name in EXECUTE_COLLECTION_PLUGINS for arg in ("-p", name)
    ]
    result = pytester.runpytest(
        *plugin_args,
        "--fork=Osaka",
        "--collect-only",
        "-q",
    )
    output = "\n".join(result.outlines + result.errlines)
    assert "INTERNALERROR" not in output
    assert result.ret in (
        pytest.ExitCode.OK,
        pytest.ExitCode.NO_TESTS_COLLECTED,
    )
