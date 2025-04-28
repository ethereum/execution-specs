"""
A pytest plugin providing common functionality for Hive simulators.

Simulators using this plugin must define two pytest fixtures:

1. `test_suite_name`: The name of the test suite.
2. `test_suite_description`: The description of the test suite.

These fixtures are used when creating the hive test suite.

Log Capture Architecture:
-------------------------
This module implements a log capture approach that ensures all logs, including those
generated during fixture teardown, are properly captured and included in the test results.

The key insight is that we need to ensure that test finalization happens *before* the
test suite is finalized, but *after* all fixtures have been torn down so we can capture
their logs. This is accomplished through the fixture teardown mechanism in pytest:

1. Since the `hive_test` fixture depends on the `test_suite` fixture, pytest guarantees
   that the teardown of `hive_test` runs before the teardown of `test_suite`
2. All logs are processed and the test is finalized in the teardown phase of the
   `hive_test` fixture using the pytest test report data
3. This sequencing ensures that all logs are captured and the test is properly finalized
   before its parent test suite is finalized

This approach relies on the pytest fixture dependency graph and teardown ordering to
ensure proper sequencing, which is more reliable than using hooks which might run in
an unpredictable order relative to fixture teardown.
"""

import json
import os
import warnings
from dataclasses import asdict
from pathlib import Path

import pytest
from filelock import FileLock
from hive.client import ClientRole
from hive.simulation import Simulation
from hive.testing import HiveTest, HiveTestResult, HiveTestSuite

from ..logging import get_logger
from .hive_info import ClientFile, HiveInfo

logger = get_logger(__name__)


def pytest_configure(config):  # noqa: D103
    hive_simulator_url = config.getoption("hive_simulator")
    if hive_simulator_url is None:
        pytest.exit(
            "The HIVE_SIMULATOR environment variable is not set.\n\n"
            "If running locally, start hive in --dev mode, for example:\n"
            "./hive --dev --client go-ethereum\n\n"
            "and set the HIVE_SIMULATOR to the reported URL. For example, in bash:\n"
            "export HIVE_SIMULATOR=http://127.0.0.1:3000\n"
            "or in fish:\n"
            "set -x HIVE_SIMULATOR http://127.0.0.1:3000"
        )
    # TODO: Try and get these into fixtures; this is only here due to the "dynamic" parametrization
    # of client_type with hive_execution_clients.
    config.hive_simulator_url = hive_simulator_url
    config.hive_simulator = Simulation(url=hive_simulator_url)
    try:
        config.hive_execution_clients = config.hive_simulator.client_types(
            role=ClientRole.ExecutionClient
        )
    except Exception as e:
        message = (
            f"Error connecting to hive simulator at {hive_simulator_url}.\n\n"
            "Did you forget to start hive in --dev mode?\n"
            "./hive --dev --client go-ethereum\n\n"
        )
        if config.option.verbose > 0:
            message += f"Error details:\n{str(e)}"
        else:
            message += "Re-run with -v for more details."
        pytest.exit(message)


def pytest_addoption(parser: pytest.Parser):  # noqa: D103
    pytest_hive_group = parser.getgroup("pytest_hive", "Arguments related to pytest hive")
    pytest_hive_group.addoption(
        "--hive-simulator",
        action="store",
        dest="hive_simulator",
        default=os.environ.get("HIVE_SIMULATOR"),
        help=(
            "The Hive simulator endpoint, e.g. http://127.0.0.1:3000. By default, the value is "
            "taken from the HIVE_SIMULATOR environment variable."
        ),
    )


def get_hive_info(simulator: Simulation) -> HiveInfo | None:
    """Fetch and return the Hive instance information."""
    try:
        hive_info = simulator.hive_instance()
        return HiveInfo(**hive_info)
    except Exception as e:
        warnings.warn(
            f"Error fetching hive information: {str(e)}\n\n"
            "Hive might need to be updated to a newer version.",
            stacklevel=2,
        )
    return None


@pytest.hookimpl(trylast=True)
def pytest_report_header(config, start_path):
    """Add lines to pytest's console output header."""
    if config.option.collectonly:
        return
    header_lines = [f"hive simulator: {config.hive_simulator_url}"]
    if hive_info := get_hive_info(config.hive_simulator):
        hive_command = " ".join(hive_info.command)
        header_lines += [
            f"hive command: {hive_command}",
            f"hive commit: {hive_info.commit}",
            f"hive date: {hive_info.date}",
        ]
        for client in hive_info.client_file.root:
            header_lines += [
                f"hive client ({client.client}): {client.model_dump_json(exclude_none=True)}",
            ]
    return header_lines


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Make the setup, call, and teardown results available in the teardown phase of
    a test fixture (i.e., after yield has been called).

    This is used to get the test result and pass it to the hive test suite.

    Available as:
    - result_setup - setup result
    - result_call - test result
    - result_teardown - teardown result
    """
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"result_{report.when}", report)


@pytest.fixture(scope="session")
def simulator(request) -> Simulation:
    """Return the Hive simulator instance."""
    return request.config.hive_simulator


@pytest.fixture(scope="session")
def hive_info(simulator: Simulation):
    """Fetch and return the Hive instance information."""
    return get_hive_info(simulator)


@pytest.fixture(scope="session")
def client_file(hive_info: HiveInfo | None) -> ClientFile:
    """Return the client file used when launching hive."""
    if hive_info is None:
        return ClientFile(root=[])
    return hive_info.client_file


def get_test_suite_scope(fixture_name, config: pytest.Config):
    """
    Return the appropriate scope of the test suite.

    See: https://docs.pytest.org/en/stable/how-to/fixtures.html#dynamic-scope
    """
    if hasattr(config, "test_suite_scope"):
        return config.test_suite_scope
    return "module"


@pytest.fixture(scope=get_test_suite_scope)
def test_suite(
    simulator: Simulation,
    session_temp_folder: Path,
    test_suite_name: str,
    test_suite_description: str,
):
    """Defines a Hive test suite and cleans up after all tests have run."""
    suite_file_name = f"test_suite_{test_suite_name}"
    suite_file = session_temp_folder / suite_file_name
    suite_lock_file = session_temp_folder / f"{suite_file_name}.lock"
    with FileLock(suite_lock_file):
        if suite_file.exists():
            with open(suite_file, "r") as f:
                suite = HiveTestSuite(**json.load(f))
        else:
            suite = simulator.start_suite(
                name=test_suite_name,
                description=test_suite_description,
            )
            with open(suite_file, "w") as f:
                json.dump(asdict(suite), f)

    users_file_name = f"test_suite_{test_suite_name}_users"
    users_file = session_temp_folder / users_file_name
    users_lock_file = session_temp_folder / f"{users_file_name}.lock"
    with FileLock(users_lock_file):
        if users_file.exists():
            with open(users_file, "r") as f:
                users = json.load(f)
        else:
            users = 0
        users += 1
        with open(users_file, "w") as f:
            json.dump(users, f)

    yield suite

    with FileLock(users_lock_file):
        with open(users_file, "r") as f:
            users = json.load(f)
        users -= 1
        with open(users_file, "w") as f:
            json.dump(users, f)
        if users == 0:
            suite.end()
            suite_file.unlink()
            users_file.unlink()


@pytest.fixture(scope="function")
def hive_test(request, test_suite: HiveTestSuite):
    """
    Propagate the pytest test case and its result to the hive server.

    This fixture handles both starting the test and ending it with all logs, including
    those generated during teardown of other fixtures. The approach of processing teardown
    logs directly in the teardown phase of this fixture ensures that the test gets properly
    finalized before the test suite is torn down.
    """
    try:
        test_case_description = request.getfixturevalue("test_case_description")
    except pytest.FixtureLookupError:
        pytest.exit(
            "Error: The 'test_case_description' fixture has not been defined by the simulator "
            "or pytest plugin using this plugin!"
        )

    test_parameter_string = request.node.name
    test: HiveTest = test_suite.start_test(
        name=test_parameter_string,
        description=test_case_description,
    )
    yield test

    try:
        # Collect all logs from all phases
        captured = []
        setup_out = ""
        call_out = ""
        for phase in ("setup", "call", "teardown"):
            report = getattr(request.node, f"result_{phase}", None)
            if report:
                stdout = report.capstdout or "None"
                stderr = report.capstderr or "None"

                # Remove setup output from call phase output
                if phase == "setup":
                    setup_out = stdout
                if phase == "call":
                    call_out = stdout
                    # If call output starts with setup output, strip it
                    if call_out.startswith(setup_out):
                        stdout = call_out[len(setup_out) :]

                captured.append(
                    f"# Captured Output from Test {phase.capitalize()}\n\n"
                    f"## stdout:\n{stdout}\n"
                    f"## stderr:\n{stderr}\n"
                )

        captured_output = "\n".join(captured)

        if hasattr(request.node, "result_call") and request.node.result_call.passed:
            test_passed = True
            test_result_details = "Test passed.\n\n" + captured_output
        elif hasattr(request.node, "result_call") and not request.node.result_call.passed:
            test_passed = False
            test_result_details = "Test failed.\n\n" + captured_output
            test_result_details = request.node.result_call.longreprtext + "\n" + captured_output
        elif hasattr(request.node, "result_setup") and not request.node.result_setup.passed:
            test_passed = False
            test_result_details = (
                "Test setup failed.\n\n"
                + request.node.result_setup.longreprtext
                + "\n"
                + captured_output
            )
        elif hasattr(request.node, "result_teardown") and not request.node.result_teardown.passed:
            test_passed = False
            test_result_details = (
                "Test teardown failed.\n\n"
                + request.node.result_teardown.longreprtext
                + "\n"
                + captured_output
            )
        else:
            test_passed = False
            test_result_details = (
                "Test failed for unknown reason (setup or call status unknown).\n\n"
                + captured_output
            )

        test.end(result=HiveTestResult(test_pass=test_passed, details=test_result_details))
        logger.verbose(f"Finished processing logs for test: {request.node.nodeid}")

    except Exception as e:
        logger.verbose(f"Error processing logs for test {request.node.nodeid}: {str(e)}")
        test_passed = False
        test_result_details = f"Exception whilst processing test result: {str(e)}"
        test.end(result=HiveTestResult(test_pass=test_passed, details=test_result_details))
