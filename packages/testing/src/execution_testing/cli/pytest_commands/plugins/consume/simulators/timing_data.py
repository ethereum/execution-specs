"""Pytest plugin that helps measure and log timing data in Hive simulators."""

from typing import Generator

import pytest
from hive.client import Client

from .helpers.timing import TimingData

TIMING_DATA_PROPERTY = "timing_data"
"""Name of the user property a test's formatted timing data travels in."""


def pytest_addoption(parser: pytest.Parser) -> None:
    """Hive simulator specific consume command line options."""
    consume_group = parser.getgroup(
        "consume", "Arguments related to consuming fixtures via a client"
    )
    consume_group.addoption(
        "--timing-data",
        action="store_true",
        dest="timing_data",
        default=False,
        help="Log the timing data for each test case execution.",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Report timing data from the process that reports results."""
    if config.getoption("timing_data", False) and not hasattr(
        config, "workerinput"
    ):
        config.pluginmanager.register(
            TimingDataReporter(config), "timing-data-reporter"
        )


class TimingDataReporter:
    """
    Print each test's timing data where test results are reported.

    The timing data is measured wherever the test runs, which under
    xdist is a worker whose output goes nowhere, so it travels to the
    controller as a user property of the test's teardown report (and
    lands in a junit report as a test case property on the way).
    """

    def __init__(self, config: pytest.Config) -> None:
        """Print through `config`'s terminal reporter."""
        self.config = config

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        """Print the timing data a teardown report carries."""
        if report.when != "teardown":
            return
        terminal = self.config.pluginmanager.get_plugin("terminalreporter")
        if terminal is None:
            return
        for name, value in report.user_properties:
            if name == TIMING_DATA_PROPERTY:
                terminal.write_line(f"\n{report.nodeid}\n{value}")


@pytest.fixture(scope="function", autouse=True)
def total_timing_data(
    request: pytest.FixtureRequest,
) -> Generator[TimingData, None, None]:
    """Record timing data for various stages of executing test case."""
    with TimingData("Total (seconds)") as total_timing_data:
        yield total_timing_data
    if request.config.getoption("timing_data"):
        request.node.user_properties.append(
            (TIMING_DATA_PROPERTY, total_timing_data.formatted())
        )


@pytest.fixture(scope="function", autouse=True)
def timing_data(
    total_timing_data: TimingData, client: Client
) -> Generator[TimingData, None, None]:
    """Record timing data for the main execution of the test case."""
    del client

    with total_timing_data.time("Test case execution") as timing_data:
        yield timing_data
