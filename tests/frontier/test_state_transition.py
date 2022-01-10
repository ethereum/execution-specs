import os
from functools import partial

import pytest

from ethereum.utils.ensure import EnsureError
from tests.frontier.blockchain_st_test_helpers import (
    run_frontier_blockchain_st_tests,
)

test_dir = (
    "tests/fixtures/LegacyTests/Constantinople/BlockchainTests/"
    "GeneralStateTests/"
)

run_general_state_tests = partial(run_frontier_blockchain_st_tests, test_dir)


@pytest.mark.parametrize(
    "test_file",
    [
        os.path.join(_dir, _file)
        for _dir in os.listdir(test_dir)
        for _file in os.listdir(os.path.join(test_dir, _dir))
    ],
)
def test_general_state_tests(test_file: str) -> None:
    try:
        run_general_state_tests(test_file)
    except KeyError:
        # KeyError is raised when a test_file has no tests for frontier
        raise pytest.skip(f"{test_file} has no tests for frontier")


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
