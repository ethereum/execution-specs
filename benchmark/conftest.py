"""Pytest configuration for benchmark tests."""

from pathlib import Path

import pytest


def pytest_collection_modifyitems(config, items):
    """Add the `benchmark` marker to all tests under `./tests/benchmark`."""
    for item in items:
        if Path(__file__).parent in Path(item.fspath).parents:
            item.add_marker(pytest.mark.benchmark)
