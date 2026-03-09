"""Pytest configuration to mark all tests as slow."""

from pathlib import Path
from typing import Any

import pytest


def pytest_collection_modifyitems(config: Any, items: Any) -> None:
    """Add the `slow` marker to time-consuming tests."""
    del config
    st_time_consuming_dir = Path(__file__).parent
    for item in items:
        if st_time_consuming_dir in Path(item.fspath).parents:
            item.add_marker(pytest.mark.slow)
