"""Local pytest configuration for framework tests."""

import os
from typing import Generator

import pytest

from ethereum_clis import ExecutionSpecsTransitionTool, TransitionTool


def pytest_runtest_setup(item):
    """Skip tests if running with pytest-xdist in parallel."""
    marker = item.get_closest_marker(name="run_in_serial")
    if marker is not None:
        if os.getenv("PYTEST_XDIST_WORKER_COUNT") not in [None, "1"]:
            pytest.skip("Skipping test because pytest-xdist is running with more than one worker.")


DEFAULT_T8N_FOR_UNIT_TESTS = ExecutionSpecsTransitionTool


@pytest.fixture(scope="session")
def default_t8n_instance() -> Generator[TransitionTool, None, None]:
    """Fixture to provide a default t8n instance."""
    instance = ExecutionSpecsTransitionTool()
    instance.start_server()
    yield instance
    instance.shutdown()


@pytest.fixture
def default_t8n(
    default_t8n_instance: TransitionTool,
) -> TransitionTool:
    """Fixture to provide a default t8n instance."""
    return default_t8n_instance
