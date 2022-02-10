import os
from functools import partial
from typing import Generator

import pytest

from ethereum.utils.ensure import EnsureError
from tests.spurious_dragon.blockchain_st_test_helpers import (
    run_spurious_dragon_blockchain_st_tests,
)

test_dir = (
    "tests/fixtures/LegacyTests/Constantinople/BlockchainTests/"
    "GeneralStateTests/"
)

run_general_state_tests = partial(
    run_spurious_dragon_blockchain_st_tests, test_dir
)

# Every test below takes more than  60s to run and
# hence they've been marked as slow
SLOW_TESTS = ()


def get_test_files() -> Generator[str, None, None]:
    for idx, _dir in enumerate(os.listdir(test_dir)):
        test_file_path = os.path.join(test_dir, _dir)
        for _file in os.listdir(test_file_path):
            _test_file = os.path.join(_dir, _file)
            # TODO: provide a way to run slow tests
            if _test_file in SLOW_TESTS:
                continue
            else:
                yield _test_file


@pytest.mark.parametrize("test_file", get_test_files())
def test_general_state_tests(test_file: str) -> None:
    try:
        run_general_state_tests(test_file)
    except KeyError:
        # KeyError is raised when a test_file has no tests for spurious_dragon
        raise pytest.skip(f"{test_file} has no tests for spurious_dragon")


# Test Invalid Block Headers
run_invalid_header_test = partial(
    run_spurious_dragon_blockchain_st_tests,
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
    run_spurious_dragon_blockchain_st_tests,
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
        # KeyError is raised when a test_file has no tests for spurious_dragon
        raise pytest.skip(f"{test_file_new} has no tests for spurious_dragon")
