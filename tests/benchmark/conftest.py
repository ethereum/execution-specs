"""Pytest configuration for benchmark tests."""

from pathlib import Path
from typing import Any

import pytest
from execution_testing import Fork, StubConfig

DEFAULT_BENCHMARK_FORK = "Prague"

_stub_config_key = pytest.StashKey[StubConfig]()


def pytest_configure(config: pytest.Config) -> None:
    """Build StubConfig from ``--address-stubs``."""
    address_stubs = config.getoption("address_stubs", default=None)
    stubs = address_stubs.root if address_stubs else {}
    config.stash[_stub_config_key] = StubConfig(stubs=stubs)


def pytest_generate_tests(metafunc: Any) -> None:
    """
    Modify test generation for benchmark tests.

    Enforce default benchmark fork and inject stub parametrization
    for tests marked with ``@pytest.mark.stub_parametrize``.
    """
    benchmark_dir = Path(__file__).parent
    test_file_path = Path(metafunc.definition.fspath)

    # Check if this test is in the benchmark directory
    is_in_benchmark_dir = benchmark_dir in test_file_path.parents

    if is_in_benchmark_dir:
        # Add benchmark marker if no valid_from marker exists
        existing_markers = list(metafunc.definition.iter_markers())
        has_valid_from = any(
            marker.name == "valid_from" for marker in existing_markers
        )

        if not has_valid_from:
            benchmark_marker = pytest.mark.valid_from(DEFAULT_BENCHMARK_FORK)
            metafunc.definition.add_marker(benchmark_marker)

    # Inject parametrization from StubConfig for stub_parametrize markers
    stub_config = metafunc.config.stash.get(_stub_config_key, None)
    if stub_config is not None:
        for marker in metafunc.definition.iter_markers("stub_parametrize"):
            param_name, prefix = marker.args
            kwargs = dict(marker.kwargs)
            values, ids = stub_config.parametrize_args(
                prefix, caller=metafunc.function.__name__
            )
            kwargs.setdefault("ids", ids)
            metafunc.parametrize(param_name, values, **kwargs)


def pytest_ignore_collect(collection_path: Path, config: Any) -> bool | None:
    """Skip benchmark directory unless explicitly targeted."""
    benchmark_dir = Path(__file__).parent

    args = config.invocation_params.args or ()
    if any(
        benchmark_dir in Path(a).resolve().parents
        or Path(a).resolve() == benchmark_dir
        for a in args
    ):
        return False

    return True


@pytest.fixture
def tx_gas_limit(fork: Fork, gas_benchmark_value: int) -> int:
    """Return the transaction gas limit cap."""
    return fork.transaction_gas_limit_cap() or gas_benchmark_value
