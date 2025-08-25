"""Pytest plugin that helps measure and log timing data in Hive simulators."""

from typing import Generator

import pytest
import rich
from hive.client import Client

from .helpers.timing import TimingData


def pytest_addoption(parser):
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


@pytest.fixture(scope="function", autouse=True)
def total_timing_data(request) -> Generator[TimingData, None, None]:
    """Record timing data for various stages of executing test case."""
    with TimingData("Total (seconds)") as total_timing_data:
        yield total_timing_data
    if request.config.getoption("timing_data"):
        rich.print(f"\n{total_timing_data.formatted()}")
    if hasattr(request.node, "rep_call"):  # make available for test reports
        request.node.rep_call.timings = total_timing_data


@pytest.fixture(scope="function", autouse=True)
def timing_data(
    total_timing_data: TimingData, client: Client
) -> Generator[TimingData, None, None]:
    """Record timing data for the main execution of the test case."""
    with total_timing_data.time("Test case execution") as timing_data:
        yield timing_data
