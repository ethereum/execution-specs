"""Shared pytest fixtures and hooks for EEST generation modes (fill and execute)."""

from enum import StrEnum, unique
from typing import List

import pytest

from ethereum_test_execution import BaseExecute, LabeledExecuteFormat
from ethereum_test_fixtures import BaseFixture, LabeledFixtureFormat
from ethereum_test_specs import BaseTest
from ethereum_test_tools import Environment
from ethereum_test_types import EOA, Alloc

from ..spec_version_checker.spec_version_checker import EIPSpecTestItem


@unique
class OpMode(StrEnum):
    """Operation mode for the fill and execute."""

    CONSENSUS = "consensus"
    BENCHMARKING = "benchmarking"


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

    if not hasattr(config, "op_mode"):
        config.op_mode = OpMode.CONSENSUS  # type: ignore[attr-defined]

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
        "benchmark: Tests relevant to benchmarking EVMs.",
    )
    config.addinivalue_line(
        "markers",
        "exception_test: Negative tests that include an invalid block or transaction.",
    )
    config.addinivalue_line(
        "markers",
        "eip_checklist(item_id, eip=None): Mark a test as implementing a specific checklist item. "
        "The first positional parameter is the checklist item ID. "
        "The optional 'eip' keyword parameter specifies additional EIPs covered by the test.",
    )
    config.addinivalue_line(
        "markers",
        "derived_test: Mark a test as a derived test (E.g. a BlockchainTest that is derived "
        "from a StateTest).",
    )
    config.addinivalue_line(
        "markers",
        "tagged: Marks a static test as tagged. Tags are used to generate dynamic "
        "addresses for static tests at fill time. All tagged tests are compatible with "
        "dynamic address generation.",
    )
    config.addinivalue_line(
        "markers",
        "untagged: Marks a static test as untagged. Tags are used to generate dynamic "
        "addresses for static tests at fill time. Untagged tests are incompatible with "
        "dynamic address generation.",
    )


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


# Global `sender` fixture that can be overridden by tests.
@pytest.fixture
def sender(pre: Alloc) -> EOA:
    """Fund an EOA from pre-alloc."""
    return pre.fund_eoa()


def pytest_addoption(parser: pytest.Parser):
    """Add command-line options to pytest."""
    static_filler_group = parser.getgroup("static", "Arguments defining static filler behavior")
    static_filler_group.addoption(
        "--fill-static-tests",
        action="store_true",
        dest="fill_static_tests_enabled",
        default=None,
        help=("Enable reading and filling from static test files."),
    )


@pytest.fixture
def env(request: pytest.FixtureRequest) -> Environment:  # noqa: D103
    return Environment()
