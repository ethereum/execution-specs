"""
A pytest plugin containing common functionality for executing blockchain test
fixtures in Hive simulators (RLP and Engine API).
"""

from pathlib import Path

import pytest

from ethereum_test_fixtures import BlockchainFixture
from ethereum_test_fixtures.consume import TestCaseIndexFile, TestCaseStream
from ethereum_test_fixtures.file import BlockchainFixtures
from pytest_plugins.consume.consume import JsonSource

TestCase = TestCaseIndexFile | TestCaseStream


@pytest.fixture(scope="function")
def fixture(fixture_source: JsonSource, test_case: TestCase) -> BlockchainFixture:
    """
    Return the blockchain fixture's pydantic model for the current test case.

    The fixture is either already available within the test case (if consume
    is taking input on stdin) or loaded from the fixture json file if taking
    input from disk (fixture directory with index file).
    """
    if fixture_source == "stdin":
        assert isinstance(test_case, TestCaseStream), "Expected a stream test case"
        assert isinstance(
            test_case.fixture, BlockchainFixture
        ), "Expected a blockchain test fixture"
        fixture = test_case.fixture
    else:
        assert isinstance(test_case, TestCaseIndexFile), "Expected an index file test case"
        # TODO: Optimize, json files will be loaded multiple times. This pytest fixture
        # is executed per test case, and a fixture json will contain multiple test cases.
        # Use cache fixtures as for statetest in consume direct?
        fixtures = BlockchainFixtures.from_file(Path(fixture_source) / test_case.json_path)
        fixture = fixtures[test_case.id]
    return fixture


@pytest.fixture(scope="function")
def fixture_description(fixture: BlockchainFixture, test_case: TestCase) -> str:
    """
    Return the description of the current test case.
    """
    description = f"Test id: {test_case.id}"
    if "url" in fixture.info:
        description += f"\n\nTest source: {fixture.info['url']}"
    if "description" not in fixture.info:
        description += "\n\nNo description field provided in the fixture's 'info' section."
    else:
        description += f"\n\n{fixture.info['description']}"
    return description
