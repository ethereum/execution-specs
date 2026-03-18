"""Pytest configuration for benchmark tests."""

from pathlib import Path
from typing import Any

import pytest
from execution_testing import Fork

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

    for item in items:
        if benchmark_dir in Path(
            item.fspath
        ).parents and not item.get_closest_marker("benchmark"):
            item.add_marker(benchmark_marker)

    # If user explicitly requested benchmarks via -m, keep them
    marker_expr = config.getoption("-m", default="")
    benchmark_requested = (
        "benchmark" in marker_expr and "not benchmark" not in marker_expr
    )
    repricing_requested = (
        "repricing" in marker_expr and "not repricing" not in marker_expr
    )
    if benchmark_requested or repricing_requested:
        return

    # If user targeted benchmark dir directly (all items are
    # benchmarks), keep them
    if items and all(item.get_closest_marker("benchmark") for item in items):
        return

    # Mixed collection (e.g. fill tests/) — exclude benchmarks
    items[:] = [
        item for item in items if not item.get_closest_marker("benchmark")
    ]


@pytest.fixture
def tx_gas_limit(fork: Fork, gas_benchmark_value: int) -> int:
    """Return the transaction gas limit cap."""
    return fork.transaction_gas_limit_cap() or gas_benchmark_value
