import os
from functools import partial
from typing import Generator

import pytest

from ethereum.utils.ensure import EnsureError
from tests.frontier.blockchain_st_test_helpers import (
    FIXTURE_NETWORK_KEY,
    load_json_fixture,
    run_frontier_blockchain_st_tests,
)

test_dir = (
    "tests/fixtures/LegacyTests/Constantinople/BlockchainTests/"
    "GeneralStateTests/"
)

run_general_state_tests = partial(run_frontier_blockchain_st_tests, test_dir)


def get_state_test_files() -> Generator[str, None, None]:
    for _dir in os.listdir(test_dir):
        test_file_path = os.path.join(test_dir, _dir)
        for _file in os.listdir(test_file_path):
            _test_file = os.path.join(_dir, _file)
            try:
                load_json_fixture(test_dir, _test_file, FIXTURE_NETWORK_KEY)
                yield _test_file
            except KeyError:
                pass


@pytest.mark.parametrize("test_file", get_state_test_files())
def test_general_state_tests(test_file: str) -> None:
    try:
        run_general_state_tests(test_file)
    except KeyError:
        # FIXME: get rid of this block
        # KeyError occurs when the test doesn't have post state
        pass


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
    run_general_state_tests_new(test_file_new)
