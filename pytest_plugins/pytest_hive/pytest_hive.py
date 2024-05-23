"""
A pytest plugin providing common functionality for Hive simulators.

Simulators using this plugin must define two pytest fixtures:

1. `test_suite_name`: The name of the test suite.
2. `test_suite_description`: The description of the test suite.

These fixtures are used when creating the hive test suite.
"""
import os

import pytest
from hive.client import ClientRole
from hive.simulation import Simulation
from hive.testing import HiveTest, HiveTestResult, HiveTestSuite


@pytest.fixture(scope="session")
def simulator(request):  # noqa: D103
    return request.config.hive_simulator


@pytest.fixture(scope="session")
def test_suite(request, simulator: Simulation):
    """
    Defines a Hive test suite and cleans up after all tests have run.
    """
    try:
        test_suite_name = request.getfixturevalue("test_suite_name")
        test_suite_description = request.getfixturevalue("test_suite_description")
    except pytest.FixtureLookupError:
        pytest.exit(
            "Error: The 'test_suite_name' and 'test_suite_description' fixtures are not defined "
            "by the hive simulator pytest plugin using this ('test_suite') fixture!"
        )

    suite = simulator.start_suite(name=test_suite_name, description=test_suite_description)
    # TODO: Can we share this fixture across all nodes using xdist? Hive uses different suites.
    yield suite
    suite.end()


def pytest_configure(config):  # noqa: D103
    hive_simulator_url = os.environ.get("HIVE_SIMULATOR")
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


@pytest.hookimpl(trylast=True)
def pytest_report_header(config, start_path):
    """
    Add lines to pytest's console output header.
    """
    if config.option.collectonly:
        return
    return [f"hive simulator: {config.hive_simulator_url}"]


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
    rep = outcome.get_result()
    setattr(item, f"result_{rep.when}", rep)


@pytest.fixture
def hive_test(request, test_suite: HiveTestSuite):
    """
    Propagate the pytest test case and its result to the hive server.
    """
    test_parameter_string = request.node.nodeid.split("[")[-1].rstrip("]")  # test fixture name
    test: HiveTest = test_suite.start_test(
        # TODO: pass test case documentation when available
        name=test_parameter_string,
        description="TODO: This should come from the '_info' field.",
    )
    yield test
    try:
        # TODO: Handle xfail/skip, does this work with run=False?
        if hasattr(request.node, "result_call") and request.node.result_call.passed:
            test_passed = True
            test_result_details = "Test passed."
        elif hasattr(request.node, "result_call") and not request.node.result_call.passed:
            test_passed = False
            test_result_details = request.node.result_call.longreprtext
        elif hasattr(request.node, "result_setup") and not request.node.result_setup.passed:
            test_passed = False
            test_result_details = "Test setup failed.\n" + request.node.result_setup.longreprtext
        elif hasattr(request.node, "result_teardown") and not request.node.result_teardown.passed:
            test_passed = False
            test_result_details = (
                "Test teardown failed.\n" + request.node.result_teardown.longreprtext
            )
        else:
            test_passed = False
            test_result_details = "Test failed for unknown reason (setup or call status unknown)."
    except Exception as e:
        test_passed = False
        test_result_details = f"Exception whilst processing test result: {str(e)}"
    test.end(result=HiveTestResult(test_pass=test_passed, details=test_result_details))
