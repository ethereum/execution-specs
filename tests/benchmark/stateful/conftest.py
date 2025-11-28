"""Pytest configuration for state tests."""

from pathlib import Path
from typing import Any

import pytest

DEFAULT_BENCHMARK_FORK = "Prague"


def pytest_generate_tests(metafunc: Any) -> None:
    """
    Add default valid_from marker to state tests without explicit fork
    specification.
    """
    state_dir = Path(__file__).parent
    test_file_path = Path(metafunc.definition.fspath)

    if state_dir in test_file_path.parents:
        has_valid_from = any(
            marker.name == "valid_from"
            for marker in metafunc.definition.iter_markers()
        )
        if not has_valid_from:
            metafunc.definition.add_marker(
                pytest.mark.valid_from(DEFAULT_BENCHMARK_FORK)
            )
