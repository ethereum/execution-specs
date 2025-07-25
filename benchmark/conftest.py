"""Pytest configuration for benchmark tests."""

from pathlib import Path

import pytest


def pytest_collection_modifyitems(config, items):
    """Add the `benchmark` marker to all tests under `./tests/benchmark`."""
    marker_expr = config.getoption("-m", default="")
    gas_benchmark_values = config.getoption("--gas-benchmark-values", default=None)
    run_benchmarks = marker_expr and (
        "benchmark" in marker_expr and "not benchmark" not in marker_expr
    )
    if gas_benchmark_values:
        run_benchmarks = True
    items_for_removal = []
    for i, item in enumerate(items):
        is_in_benchmark_dir = Path(__file__).parent in Path(item.fspath).parents
        has_benchmark_marker = item.get_closest_marker("benchmark") is not None
        is_benchmark_test = is_in_benchmark_dir or has_benchmark_marker
        if is_benchmark_test:
            if is_in_benchmark_dir and not has_benchmark_marker:
                benchmark_marker = pytest.mark.benchmark

                item.add_marker(benchmark_marker)
            if not run_benchmarks:
                items_for_removal.append(i)

        elif run_benchmarks:
            items_for_removal.append(i)

    for i in reversed(items_for_removal):
        items.pop(i)
