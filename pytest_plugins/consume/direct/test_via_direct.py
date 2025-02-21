"""
Executes a JSON test fixture directly against a client using a dedicated
client interface similar to geth's EVM 'blocktest' command.
"""

from pathlib import Path

from ethereum_test_fixtures import BaseFixture, FixtureConsumer, FixtureFormat
from ethereum_test_fixtures.consume import TestCaseIndexFile, TestCaseStream
from pytest_plugins.consume.decorator import fixture_format


@fixture_format(*BaseFixture.formats.values())
def test_fixture(
    test_case: TestCaseIndexFile | TestCaseStream,
    fixture_consumer: FixtureConsumer,
    fixture_path: Path,
    fixture_format: FixtureFormat,
    test_dump_dir: Path | None,
):
    """
    Generic test function used to call the fixture consumer with a given fixture file path and
    a fixture name (for a single test run).
    """
    fixture_consumer.consume_fixture(
        fixture_format,
        fixture_path,
        fixture_name=test_case.id,
        debug_output_path=test_dump_dir,
    )
