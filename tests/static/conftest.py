"""
Conftest for static tests.

Temporarily skip static tests that fail for Amsterdam due to EIP-8037's
two-dimensional gas model. The gas limits in these static test files
have not yet been updated to account for state gas.

TODO: Update gas limits in the 703 failing static test files and remove
this skip list.
"""

from pathlib import Path

import pytest

_SKIP_LIST_PATH = Path(__file__).parent / "amsterdam_skip_list.txt"
_AMSTERDAM_SKIP_FILES: frozenset[str] = frozenset(
    line.strip()
    for line in _SKIP_LIST_PATH.read_text().splitlines()
    if line.strip()
)


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Skip static tests listed in amsterdam_skip_list.txt for Amsterdam."""
    skip_marker = pytest.mark.skip(
        reason="Static test gas limits not yet updated for EIP-8037"
    )
    for item in items:
        if "fork_Amsterdam" not in item.nodeid:
            continue
        for skip_path in _AMSTERDAM_SKIP_FILES:
            if skip_path in item.nodeid:
                item.add_marker(skip_marker)
                break
