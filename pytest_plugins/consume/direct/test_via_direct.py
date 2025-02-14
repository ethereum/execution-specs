"""
Executes a JSON test fixture directly against a client using a dedicated
client interface similar to geth's EVM 'blocktest' command.
"""

import re
from pathlib import Path
from typing import Any, List, Optional

import pytest

from ethereum_clis import TransitionTool
from ethereum_test_fixtures import BlockchainFixture, FixtureFormat, StateFixture
from ethereum_test_fixtures.consume import TestCaseIndexFile, TestCaseStream

from ..decorator import fixture_format

statetest_results: dict[Path, List[dict[str, Any]]] = {}


@fixture_format(BlockchainFixture)
def test_blocktest(  # noqa: D103
    test_case: TestCaseIndexFile | TestCaseStream,
    evm: TransitionTool,
    evm_run_single_test: bool,
    fixture_path: Path,
    fixture_format: FixtureFormat,
    test_dump_dir: Optional[Path],
):
    assert fixture_format == BlockchainFixture
    fixture_name = None
    if evm_run_single_test:
        fixture_name = re.escape(test_case.id)
    evm.verify_fixture(
        test_case.format,
        fixture_path,
        fixture_name=fixture_name,
        debug_output_path=test_dump_dir,
    )


@pytest.fixture(scope="function")
def run_statetest(
    test_case: TestCaseIndexFile | TestCaseStream,
    evm: TransitionTool,
    fixture_path: Path,
    test_dump_dir: Optional[Path],
):
    """Run statetest on the json fixture file if the test result is not already cached."""
    # TODO: Check if all required results have been tested and delete test result data if so.
    # TODO: Can we group the tests appropriately so that this works more efficiently with xdist?
    if fixture_path not in statetest_results:
        json_result = evm.verify_fixture(
            test_case.format,
            fixture_path,
            fixture_name=None,
            debug_output_path=test_dump_dir,
        )
        statetest_results[fixture_path] = json_result


@pytest.mark.usefixtures("run_statetest")
@fixture_format(StateFixture)
def test_statetest(  # noqa: D103
    test_case: TestCaseIndexFile | TestCaseStream,
    fixture_format: FixtureFormat,
    fixture_path: Path,
):
    assert fixture_format == StateFixture
    test_result = [
        test_result
        for test_result in statetest_results[fixture_path]
        if test_result["name"] == test_case.id
    ]
    assert len(test_result) < 2, f"Multiple test results for {test_case.id}"
    assert len(test_result) == 1, f"Test result for {test_case.id} missing"
    assert test_result[0]["pass"], f"State test failed: {test_result[0]['error']}"
