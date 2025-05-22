"""Shared pytest fixtures and hooks for EEST generation modes (fill and execute)."""

import warnings
from typing import List

import pytest

from ethereum_test_execution import BaseExecute, LabeledExecuteFormat
from ethereum_test_fixtures import BaseFixture, LabeledFixtureFormat
from ethereum_test_forks import (
    Fork,
    get_closest_fork_with_solc_support,
    get_forks_with_solc_support,
)
from ethereum_test_specs import BaseTest
from ethereum_test_tools import Yul
from pytest_plugins.spec_version_checker.spec_version_checker import EIPSpecTestItem


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config):
    """
    Pytest hook called after command line options have been parsed and before
    test collection begins.

    Couple of notes:
    1. Register the plugin's custom markers and process command-line options.

        Custom marker registration:
        https://docs.pytest.org/en/7.1.x/how-to/writing_plugins.html#registering-custom-markers

    2. `@pytest.hookimpl(tryfirst=True)` is applied to ensure that this hook is
        called before the pytest-html plugin's pytest_configure to ensure that
        it uses the modified `htmlpath` option.
    """
    if config.pluginmanager.has_plugin("pytest_plugins.filler.filler"):
        for fixture_format in BaseFixture.formats.values():
            config.addinivalue_line(
                "markers",
                (f"{fixture_format.format_name.lower()}: {fixture_format.description}"),
            )
        for label, labeled_fixture_format in LabeledFixtureFormat.registered_labels.items():
            config.addinivalue_line(
                "markers",
                (f"{label}: {labeled_fixture_format.description}"),
            )
    elif config.pluginmanager.has_plugin("pytest_plugins.execute.execute"):
        for execute_format in BaseExecute.formats.values():
            config.addinivalue_line(
                "markers",
                (f"{execute_format.format_name.lower()}: {execute_format.description}"),
            )
        for label, labeled_execute_format in LabeledExecuteFormat.registered_labels.items():
            config.addinivalue_line(
                "markers",
                (f"{label}: {labeled_execute_format.description}"),
            )
    else:
        raise Exception("Neither the filler nor the execute plugin is loaded.")

    for spec_type in BaseTest.spec_types.values():
        for marker, description in spec_type.supported_markers.items():
            config.addinivalue_line(
                "markers",
                (f"{marker}: {description}"),
            )

    config.addinivalue_line(
        "markers",
        "yul_test: a test case that compiles Yul code.",
    )
    config.addinivalue_line(
        "markers",
        "compile_yul_with(fork): Always compile Yul source using the corresponding evm version.",
    )
    config.addinivalue_line(
        "markers",
        "fill: Markers to be added in fill mode only.",
    )
    config.addinivalue_line(
        "markers",
        "execute: Markers to be added in execute mode only.",
    )
    config.addinivalue_line(
        "markers",
        "zkevm: Tests that are relevant to zkEVM.",
    )
    config.addinivalue_line(
        "markers",
        "exception_test: Negative tests that include an invalid block or transaction.",
    )


@pytest.fixture(autouse=True)
def eips():
    """
    Fixture for specifying that, by default, no EIPs should be activated for
    tests.

    This fixture (function) may be redefined in test filler modules in order
    to overwrite this default and return a list of integers specifying which
    EIPs should be activated for the tests in scope.
    """
    return []


@pytest.fixture
def yul(fork: Fork, request: pytest.FixtureRequest):
    """
    Fixture that allows contract code to be defined with Yul code.

    This fixture defines a class that wraps the ::ethereum_test_tools.Yul
    class so that upon instantiation within the test case, it provides the
    test case's current fork parameter. The forks is then available for use
    in solc's arguments for the Yul code compilation.

    Test cases can override the default value by specifying a fixed version
    with the @pytest.mark.compile_yul_with(FORK) marker.
    """
    solc_target_fork: Fork | None
    marker = request.node.get_closest_marker("compile_yul_with")
    assert hasattr(request.config, "solc_version"), "solc_version not set in pytest config."
    if marker:
        if not marker.args[0]:
            pytest.fail(
                f"{request.node.name}: Expected one argument in 'compile_yul_with' marker."
            )
        for fork in request.config.all_forks:  # type: ignore
            if fork.name() == marker.args[0]:
                solc_target_fork = fork
                break
        else:
            pytest.fail(f"{request.node.name}: Fork {marker.args[0]} not found in forks list.")
        assert solc_target_fork in get_forks_with_solc_support(request.config.solc_version)
    else:
        solc_target_fork = get_closest_fork_with_solc_support(fork, request.config.solc_version)
        assert solc_target_fork is not None, "No fork supports provided solc version."
        if solc_target_fork != fork and request.config.getoption("verbose") >= 1:
            warnings.warn(
                f"Compiling Yul for {solc_target_fork.name()}, not {fork.name()}.", stacklevel=2
            )

    class YulWrapper(Yul):
        def __new__(cls, *args, **kwargs):
            return super(YulWrapper, cls).__new__(cls, *args, **kwargs, fork=solc_target_fork)

    return YulWrapper


@pytest.fixture(scope="function")
def test_case_description(request: pytest.FixtureRequest) -> str:
    """Fixture to extract and combine docstrings from the test class and the test function."""
    description_unavailable = (
        "No description available - add a docstring to the python test class or function."
    )
    test_class_doc = ""
    test_function_doc = ""
    if hasattr(request.node, "cls"):
        test_class_doc = f"Test class documentation:\n{request.cls.__doc__}" if request.cls else ""
    if hasattr(request.node, "function"):
        test_function_doc = f"{request.function.__doc__}" if request.function.__doc__ else ""
    if not test_class_doc and not test_function_doc:
        return description_unavailable
    combined_docstring = f"{test_class_doc}\n\n{test_function_doc}".strip()
    return combined_docstring


def pytest_make_parametrize_id(config: pytest.Config, val: str, argname: str):
    """
    Pytest hook called when generating test ids. We use this to generate
    more readable test ids for the generated tests.
    """
    return f"{argname}_{val}"


SPEC_TYPES_PARAMETERS: List[str] = list(BaseTest.spec_types.keys())


def pytest_runtest_call(item: pytest.Item):
    """Pytest hook called in the context of test execution."""
    if isinstance(item, EIPSpecTestItem):
        return

    class InvalidFillerError(Exception):
        def __init__(self, message):
            super().__init__(message)

    if not isinstance(item, pytest.Function):
        return

    if "state_test" in item.fixturenames and "blockchain_test" in item.fixturenames:
        raise InvalidFillerError(
            "A filler should only implement either a state test or a blockchain test; not both."
        )

    # Check that the test defines either test type as parameter.
    if not any(i for i in item.funcargs if i in SPEC_TYPES_PARAMETERS):
        pytest.fail(
            "Test must define either one of the following parameters to "
            + "properly generate a test: "
            + ", ".join(SPEC_TYPES_PARAMETERS)
        )
