"""Local pytest configuration used on multiple framework tests."""

import os
from typing import Dict, Generator

import pytest

from ethereum_clis import BesuTransitionTool, ExecutionSpecsTransitionTool, TransitionTool


def pytest_runtest_setup(item):
    """Skip tests if running with pytest-xdist in parallel."""
    marker = item.get_closest_marker(name="run_in_serial")
    if marker is not None:
        if os.getenv("PYTEST_XDIST_WORKER_COUNT") not in [None, "1"]:
            pytest.skip("Skipping test because pytest-xdist is running with more than one worker.")


DEFAULT_TRANSITION_TOOL_FOR_UNIT_TESTS = ExecutionSpecsTransitionTool

INSTALLED_TRANSITION_TOOLS = [
    transition_tool
    for transition_tool in TransitionTool.registered_tools
    if (
        transition_tool.is_installed()
        # Currently, Besu has the same `default_binary` as Geth, so we can't use `is_installed`.
        and transition_tool != BesuTransitionTool
    )
]


@pytest.fixture(scope="session")
def installed_transition_tool_instances() -> Generator[
    Dict[str, TransitionTool | Exception], None, None
]:
    """Return all instantiated transition tools."""
    instances: Dict[str, TransitionTool | Exception] = {}
    for transition_tool_class in INSTALLED_TRANSITION_TOOLS:
        try:
            instances[transition_tool_class.__name__] = transition_tool_class()
        except Exception as e:
            # Record the exception in order to provide context when failing the appropriate test
            instances[transition_tool_class.__name__] = e
    yield instances
    for instance in instances.values():
        if isinstance(instance, TransitionTool):
            instance.shutdown()


@pytest.fixture(
    params=INSTALLED_TRANSITION_TOOLS,
    ids=[transition_tool_class.__name__ for transition_tool_class in INSTALLED_TRANSITION_TOOLS],
)
def installed_t8n(
    request: pytest.FixtureRequest,
    installed_transition_tool_instances: Dict[str, TransitionTool | Exception],
) -> TransitionTool:
    """
    Return an instantiated transition tool.

    Tests using this fixture will be automatically parameterized with all
    installed transition tools.
    """
    transition_tool_class = request.param
    assert issubclass(transition_tool_class, TransitionTool)
    assert transition_tool_class.__name__ in installed_transition_tool_instances, (
        f"{transition_tool_class.__name__} not instantiated"
    )
    instance_or_error = installed_transition_tool_instances[transition_tool_class.__name__]
    if isinstance(instance_or_error, Exception):
        raise Exception(
            f"Failed to instantiate {transition_tool_class.__name__}"
        ) from instance_or_error
    return instance_or_error


@pytest.fixture
def default_t8n(
    installed_transition_tool_instances: Dict[str, TransitionTool | Exception],
) -> TransitionTool:
    """Fixture to provide a default t8n instance."""
    instance = installed_transition_tool_instances.get(
        DEFAULT_TRANSITION_TOOL_FOR_UNIT_TESTS.__name__
    )
    if instance is None:
        raise Exception(f"Failed to instantiate {DEFAULT_TRANSITION_TOOL_FOR_UNIT_TESTS.__name__}")
    if isinstance(instance, Exception):
        raise Exception(
            f"Failed to instantiate {DEFAULT_TRANSITION_TOOL_FOR_UNIT_TESTS.__name__}"
        ) from instance
    return instance


@pytest.fixture(scope="session")
def running_in_ci() -> bool:
    """Return whether the test is running in a CI environment."""
    return "CI" in os.environ
