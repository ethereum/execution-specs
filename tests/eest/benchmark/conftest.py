"""Pytest configuration for benchmark tests."""

from pathlib import Path

import pytest


def pytest_collection_modifyitems(config, items):
    """Add the `benchmark` marker to all tests under `./tests/benchmark`."""
    benchmark_dir = Path(__file__).parent
    benchmark_marker = pytest.mark.benchmark
    gen_docs = config.getoption("--gen-docs", default=False)

    if gen_docs:
        for item in items:
            if benchmark_dir in Path(item.fspath).parents and not item.get_closest_marker(
                "benchmark"
            ):
                item.add_marker(benchmark_marker)
        return

    marker_expr = config.getoption("-m", default="")
    run_benchmarks = (
        marker_expr and "benchmark" in marker_expr and "not benchmark" not in marker_expr
    ) or config.getoption("--gas-benchmark-values", default=None)

    items_for_removal = []
    for i, item in enumerate(items):
        is_in_benchmark_dir = benchmark_dir in Path(item.fspath).parents
        is_benchmark_test = is_in_benchmark_dir or item.get_closest_marker("benchmark")

        if is_benchmark_test:
            if is_in_benchmark_dir and not item.get_closest_marker("benchmark"):
                item.add_marker(benchmark_marker)
            if not run_benchmarks:
                items_for_removal.append(i)
        elif run_benchmarks:
            items_for_removal.append(i)

    for i in reversed(items_for_removal):
        items.pop(i)
