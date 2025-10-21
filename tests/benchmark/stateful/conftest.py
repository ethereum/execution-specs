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


def pytest_collection_modifyitems(config: Any, items: Any) -> None:
    """Manage stateful test markers and filtering."""
    state_dir = Path(__file__).parent
    gen_docs = config.getoption("--gen-docs", default=False)

    if gen_docs:
        _add_stateful_markers_for_docs(items, state_dir)
        return

    marker_expr = config.getoption("-m", default="")

    items_to_remove = []

    for i, item in enumerate(items):
        item_path = Path(item.fspath)
        is_in_state_dir = state_dir in item_path.parents

        # Add stateful marker to tests in state directory that don't have it
        if is_in_state_dir and not item.get_closest_marker("stateful"):
            item.add_marker(pytest.mark.stateful)

        has_stateful_marker = item.get_closest_marker("stateful")

        run_stateful = (
            marker_expr
            and ("stateful" in marker_expr)
            and ("not stateful" not in marker_expr)
        )

        # When not running stateful tests, remove all stateful tests
        if not run_stateful and has_stateful_marker:
            items_to_remove.append(i)

    for i in reversed(items_to_remove):
        items.pop(i)


def _add_stateful_markers_for_docs(items: Any, state_dir: Any) -> None:
    """Add stateful markers for documentation generation."""
    for item in items:
        item_path = Path(item.fspath)
        if state_dir in item_path.parents and not item.get_closest_marker(
            "stateful"
        ):
            item.add_marker(pytest.mark.stateful)
