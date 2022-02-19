from functools import partial

import pytest

from ethereum.utils.ensure import EnsureError
from tests.frontier.blockchain_st_test_helpers import (
    FIXTURES_LOADER,
    run_frontier_blockchain_st_tests,
)
from tests.helpers.load_state_tests import fetch_state_test_files

test_dir = (
    "tests/fixtures/LegacyTests/Constantinople/BlockchainTests/"
    "GeneralStateTests/"
)

run_general_state_tests = partial(run_frontier_blockchain_st_tests, test_dir)


SLOW_TESTS = ()


@pytest.mark.parametrize(
    "test_file", fetch_state_test_files(test_dir, SLOW_TESTS, FIXTURES_LOADER)
)
def test_general_state_tests(test_file: str) -> None:
    try:
        run_general_state_tests(test_file)
    except KeyError:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(f"{test_file} doesn't have post state")


# Test Invalid Block Headers
run_invalid_header_test = partial(
    run_frontier_blockchain_st_tests,
    "tests/fixtures/LegacyTests/Constantinople/BlockchainTests/InvalidBlocks/bcInvalidHeaderTest",
)


@pytest.mark.parametrize(
    "test_file_parent_hash",
    [
        "wrongParentHash.json",
        "wrongParentHash2.json",
    ],
)
def test_invalid_parent_hash(test_file_parent_hash: str) -> None:
    with pytest.raises(EnsureError):
        run_invalid_header_test(test_file_parent_hash)


# Run Non-Legacy GeneralStateTests
run_general_state_tests_new = partial(
    run_frontier_blockchain_st_tests,
    "tests/fixtures/BlockchainTests/GeneralStateTests/",
)


@pytest.mark.parametrize(
    "test_file_new",
    [
        "stCreateTest/CREATE_HighNonce.json",
        "stCreateTest/CREATE_HighNonceMinus1.json",
    ],
)
def test_general_state_tests_new(test_file_new: str) -> None:
    try:
        run_general_state_tests_new(test_file_new)
    except KeyError:
        # KeyError is raised when a test_file has no tests for frontier
        raise pytest.skip(f"{test_file_new} has no tests for frontier")
