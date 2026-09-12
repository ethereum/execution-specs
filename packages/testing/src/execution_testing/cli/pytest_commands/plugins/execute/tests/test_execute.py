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


@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize("estimate_gas", [False, True])
def test_estimation_after_setup(dry_run: bool, estimate_gas: bool) -> None:
    """Fund before estimation and keep dry runs free of test RPC calls."""
    from unittest.mock import Mock

    from execution_testing.execution import TransactionPost
    from execution_testing.forks import Amsterdam
    from execution_testing.rpc import EthRPC
    from execution_testing.test_types import EOA, Alloc, Transaction

    from ..execute import base_test_parametrizer

    events: list[str] = []
    tx = Transaction(sender=EOA(key=123))
    plan = TransactionPost(blocks=[[tx]], post={})
    rpc = Mock(spec=EthRPC)

    def estimate(*_args: Any, **_kwargs: Any) -> int:
        events.append("estimate")
        return 100_000

    rpc.estimate_gas.side_effect = estimate
    rpc.send_wait_transactions.side_effect = lambda *_args: events.append(
        "send"
    )
    rpc.get_transaction_receipt.return_value = {"status": "0x1"}
    rpc.get_alloc.return_value = Alloc()
    pre = Mock()
    pre._deployed_contracts = []
    pre._funded_eoa = []
    pre.minimum_balance_for_pending_transactions.return_value = (
        600_000_000,
        60_000_000,
    )
    pre.send_pending_transactions.side_effect = lambda: events.append("setup")

    class TestSpec:
        """Provide the spec interface used by the execute wrapper."""

        model_fields: dict = {}

        def __init__(self, **kwargs: Any) -> None:
            pass

        @classmethod
        def pytest_parameter_name(cls) -> str:
            return "state_test"

        def execute(self, **_kwargs: Any) -> TransactionPost:
            return plan

        def validate_benchmark_gas(self, **kwargs: Any) -> None:
            pass

    config = SimpleNamespace(
        getoption=lambda *_args: estimate_gas,
        op_mode=None,
    )
    request = SimpleNamespace(
        param=TransactionPost,
        config=config,
        node=SimpleNamespace(
            config=config, nodeid="test_estimation_after_setup"
        ),
    )
    spec: Any = TestSpec
    fixture = base_test_parametrizer(spec)
    wrapper = fixture.__wrapped__(
        request=request,
        fork=Amsterdam,
        pre=pre,
        eth_rpc=rpc,
        engine_rpc=None,
        dry_run=dry_run,
        collector=Mock(),
        gas_benchmark_value=0,
        fixed_opcode_count=None,
        gas_price=10,
        max_fee_per_gas=10,
        max_priority_fee_per_gas=1,
        max_fee_per_blob_gas=10,
        max_gas_limit_per_test=None,
        gas_limit_accumulator=Mock(),
        env_gas_limit=60_000_000,
        is_tx_gas_heavy_test=False,
        is_exception_test=False,
        is_inclusion_test=False,
    )
    wrapper()
    assert plan.estimate_gas == estimate_gas
    assert events == (
        []
        if dry_run
        else ["setup"] + (["estimate"] if estimate_gas else []) + ["send"]
    )
