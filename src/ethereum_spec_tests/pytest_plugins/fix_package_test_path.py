"""
Pytest plugin to fix the test IDs for all pytest command that use a command-logic test
file.
"""

from typing import List

import pytest


def pytest_collection_modifyitems(items: List[pytest.Item]):
    """Modify collected item names to remove the test runner function from the name."""
    for item in items:
        original_name = item.originalname  # type: ignore
        remove = f"{original_name}["
        if item.name.startswith(remove):
            item.name = item.name.removeprefix(remove)[:-1]
        if remove in item.nodeid:
            item._nodeid = item.nodeid[item.nodeid.index(remove) + len(remove) : -1]
