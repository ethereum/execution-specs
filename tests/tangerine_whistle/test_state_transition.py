import os
from functools import partial
from typing import Generator

import pytest

from tests.tangerine_whistle.blockchain_st_test_helpers import (
    run_tangerine_whistle_blockchain_st_tests,
)

test_dir = (
    "tests/fixtures/LegacyTests/Constantinople/BlockchainTests/"
    "GeneralStateTests/"
)

run_general_state_tests = partial(
    run_tangerine_whistle_blockchain_st_tests, test_dir
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
        # KeyError is raised when a test_file has no tests for tangerine_whistle
        raise pytest.skip(f"{test_file} has no tests for tangerine_whistle")
