"""
Top-level pytest configuration file providing:
- Command-line options,
- Test-fixtures that can be used by all test cases,
and that modifies pytest hooks in order to fill test specs for all tests and
writes the generated fixtures to file.
"""
import json
import os

import pytest

from ethereum_test_forks import (
    ArrowGlacier,
    InvalidForkError,
    set_latest_fork_by_name,
)
from ethereum_test_tools import JSONEncoder, fill_test
from evm_block_builder import EvmBlockBuilder
from evm_transition_tool import EvmTransitionTool


def pytest_addoption(parser):
    group = parser.getgroup(
        "evm", "Arguments defining evm executable behavior"
    )
    group.addoption(
        "--evm-bin",
        action="store",
        dest="evm_bin",
        default=None,
        help="Path to evm executable that provides `t8n` and `b11r` ",
    )
    group.addoption(
        "--traces",
        action="store_true",
        dest="evm_collect_traces",
        default=None,
        help="Collect traces of the execution information from the "
        + "transition tool",
    )

    group = parser.getgroup(
        "fillers", "Arguments defining filler location and output"
    )
    group.addoption(
        "--filler-path",
        action="store",
        dest="filler_path",
        default="./fillers/",
        help="Path to filler directives",
    )
    group.addoption(
        "--output",
        action="store",
        dest="output",
        default="./out/",
        help="Directory to store filled test fixtures",
    )
    group.addoption(
        "--latest-fork",
        action="store",
        dest="latest_fork",
        default=None,
        help="Latest fork used to fill tests",
    )


def pytest_configure(config):
    """
    Check parameters and make session-wide configuration changes, such as
    setting the latest fork.
    """
    latest_fork = config.getoption("latest_fork")
    if latest_fork is not None:
        try:
            set_latest_fork_by_name(latest_fork)
        except InvalidForkError as e:
            pytest.exit(f"Error applying --latest-fork={latest_fork}: {e}.")
        except Exception as e:
            raise e
    return None


@pytest.fixture(autouse=True, scope="session")
def evm_bin(request):
    """
    Returns the configured evm tool binary path.
    """
    return request.config.getoption("evm_bin")


@pytest.fixture(autouse=True, scope="session")
def t8n(request):
    """
    Returns the configured transition tool.
    """
    t8n = EvmTransitionTool(
        binary=request.config.getoption("evm_bin"),
        trace=request.config.getoption("evm_collect_traces"),
    )
    return t8n


@pytest.fixture(autouse=True, scope="session")
def b11r(request):
    """
    Returns the configured block builder tool.
    """
    b11r = EvmBlockBuilder(binary=request.config.getoption("evm_bin"))
    return b11r


@pytest.fixture(autouse=True, scope="session")
def engine():
    """
    Returns the sealEngine used in the generated test fixtures.
    """
    return "NoProof"


@pytest.fixture(autouse=True, scope="session")
def output_dir(request):
    """
    Returns the fixture output directory.
    """
    return request.config.getoption("output")


@pytest.fixture(autouse=True, scope="session")
def filler_path(request):
    """
    Returns the directory containing the fillers to execute.
    """
    return request.config.getoption("filler_path")


@pytest.fixture(autouse=True)
def eips():
    """
    A fixture specifying that, by default, no EIPs should be activated for
    fillers.

    This fixture (function) may be redefined in test filler modules in order
    to overwrite this default and return a list of integers specifying which
    EIPs should be activated for the fillers in scope.
    """
    return []


@pytest.fixture(autouse=True)
def reference_spec():
    return None


@pytest.fixture(scope="function")
def state_test():
    """
    This fixture is used to store a StateTest object from within a test
    function so that it can be filled post test function execution in
    the pytest_runtest_call() hook.

    Every test that defines a StateTest filler must explicitly specify this
    fixture in its function arguments and set the StateTestWrapper's spec
    property.

    Implementation detail: It must be scoped on test function level to avoid
    leakage between tests.
    """

    class StateTestWrapper:
        spec = None

    return StateTestWrapper()


@pytest.fixture(scope="function")
def blockchain_test():
    """
    A fixture used to held define BlockchainTests analogous to the state_test
    fixture for StateTests. See the state_test fixture docstring for details.
    """

    class BlockchainTestWrapper:
        spec = None

    return BlockchainTestWrapper()


def convert_pytest_case_name_to_fixture_name(item):
    fixture_name = item.name
    fixture_name = fixture_name.replace("]", "")
    fixture_name = fixture_name.replace("[", "_")
    return fixture_name


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """
    Pytest hook called in the context of test execution. After pytest
    has executed the test function and created the test spec, we fill
    the test spec and write the generated fixture to file.
    """
    output = yield  # Execute the test function

    # Process test result; this will stop execution if there was an issue in
    # the test function and trigger a pytest error or fail for this spec.
    output.get_result()

    # Get config from session-wide fixtures. Note, we could also access these
    # from the pytest config object via item.config
    # evm_bin = item.funcargs["evm_bin"]
    t8n = item.funcargs["t8n"]
    b11r = item.funcargs["b11r"]
    engine = item.funcargs["engine"]
    reference_spec = item.funcargs["reference_spec"]

    # Get test-specific params from potentially locally defined fixtures
    eips = item.funcargs["eips"]
    fork = item.funcargs["fork"]
    if "state_test" in item.funcargs:
        test_spec = item.funcargs["state_test"].spec
    elif "blockchain_test" in item.funcargs:
        test_spec = item.funcargs["blockchain_test"].spec
    else:
        # TODO: Raise custom exception instead of fail to trigger a
        # pytest error
        pytest.fail(
            "Invalid test function signature: Test did not use either "
            " of the 'state_test' or 'blockchain_test' fixtures."
        )

    if not t8n.is_fork_supported(fork):
        pytest.skip(f"Fork '{fork}' not supported by t8n, skipped")
    if fork == ArrowGlacier:
        pytest.skip(f"Fork '{fork}' not supported by hive, skipped")

    fixture_name = convert_pytest_case_name_to_fixture_name(item)
    fixture_output = fill_test(
        fixture_name,
        t8n,
        b11r,
        test_spec,
        fork,
        engine,
        reference_spec,
        eips=eips,
    )
    write_fixture_file(item, fixture_output)


def write_fixture_file(item, fixture_output):
    """
    Write the generated test fixture output to a:
    - sub-directory in the fixture output directory that corresponds to the
    relative path of the test case module within the filler sub-directory.
    - json file using the test case id (without special characters).
    """

    def get_fixture_output_dir():
        dirname = os.path.dirname(item.path)
        basename, _ = os.path.splitext(item.path)
        module_path_no_ext = os.path.join(dirname, basename)
        module_dir = os.path.relpath(
            module_path_no_ext,
            item.funcargs["filler_path"],
        )
        output_dir = os.path.join(
            item.funcargs["output_dir"],
            module_dir,
        )
        return output_dir

    output_dir = get_fixture_output_dir()
    os.makedirs(output_dir, exist_ok=True)

    def get_fixture_output_path():
        filename = convert_pytest_case_name_to_fixture_name(item)
        return os.path.join(output_dir, f"{filename}.json")

    path = get_fixture_output_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            fixture_output,
            f,
            ensure_ascii=False,
            indent=4,
            cls=JSONEncoder,
        )
