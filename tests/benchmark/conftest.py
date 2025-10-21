"""Pytest configuration for benchmark tests."""

from pathlib import Path
from typing import Any

import pytest
from ethereum_test_forks import Fork

DEFAULT_BENCHMARK_FORK = "Prague"


def pytest_generate_tests(metafunc: Any) -> None:
    """
    Modify test generation to enforce default benchmark fork for benchmark
    tests.
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


def pytest_collection_modifyitems(config: Any, items: Any) -> None:
    """Add the `benchmark` marker to all tests under `./tests/benchmark`."""
    benchmark_dir = Path(__file__).parent
    benchmark_marker = pytest.mark.benchmark
    gen_docs = config.getoption("--gen-docs", default=False)

    if gen_docs:
        for item in items:
            if (
                benchmark_dir in Path(item.fspath).parents
                and not item.get_closest_marker("benchmark")
                and not item.get_closest_marker("stateful")
            ):
                item.add_marker(benchmark_marker)
        return

    marker_expr = config.getoption("-m", default="")
    run_benchmarks = (
        marker_expr
        and "benchmark" in marker_expr
        and "not benchmark" not in marker_expr
    )
    run_stateful_tests = (
        marker_expr
        and "stateful" in marker_expr
        and "not stateful" not in marker_expr
    )

    items_for_removal = []
    for i, item in enumerate(items):
        is_in_benchmark_dir = benchmark_dir in Path(item.fspath).parents
        has_stateful_marker = item.get_closest_marker("stateful")
        is_benchmark_test = (
            is_in_benchmark_dir and not has_stateful_marker
        ) or item.get_closest_marker("benchmark")

        if is_benchmark_test:
            if is_in_benchmark_dir and not item.get_closest_marker(
                "benchmark"
            ):
                item.add_marker(benchmark_marker)
            if not run_benchmarks:
                items_for_removal.append(i)
        elif run_benchmarks:
            items_for_removal.append(i)
        elif (
            is_in_benchmark_dir
            and has_stateful_marker
            and not run_stateful_tests
        ):
            items_for_removal.append(i)

    for i in reversed(items_for_removal):
        items.pop(i)


@pytest.fixture
def tx_gas_limit_cap(fork: Fork, gas_benchmark_value: int) -> int:
    """Return the transaction gas limit cap."""
    return fork.transaction_gas_limit_cap() or gas_benchmark_value
