"""
Local pytest configuration for framework tests.
"""

import os

import pytest


def pytest_runtest_setup(item):
    """Hook to skip tests if running with pytest-xdist in parallel."""
    marker = item.get_closest_marker(name="run_in_serial")
    if marker is not None:
        if os.getenv("PYTEST_XDIST_WORKER_COUNT") not in [None, "1"]:
            pytest.skip("Skipping test because pytest-xdist is running with more than one worker.")
