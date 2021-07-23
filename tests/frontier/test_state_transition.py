import os

import pytest

from tests.frontier.blockchain_st_test_helpers import (
    run_frontier_blockchain_st_tests,
)

TEST_DIR = (
    "tests/fixtures/LegacyTests/Constantinople/BlockchainTests/"
    "GeneralStateTests/"
)


def test_add() -> None:
    run_frontier_blockchain_st_tests("stExample/add11_d0g0v0.json")


# TODO: Run the below test cases once CALL opcode has been implemented.
# @pytest.mark.parametrize(
#     "test_file",
#     list(os.listdir(os.path.join(TEST_DIR, "stLogTests")))
# )
# def test_log_operations(test_file: str) -> None:
#     print(test_file)
#     run_frontier_blockchain_st_tests(f"stLogTests/{test_file}")
#     assert 1 == 0
