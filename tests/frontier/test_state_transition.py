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


@pytest.mark.parametrize(
    "test_file",
    [
        f"stTransactionTest/Opcodes_TransactionInit_d{i}g0v0.json"
        for i in range(121)
        if i not in [33, 37, 38]
        # TODO: Tests 121-127 need the CALL Opcode
        #  increase the range to 128 once CALL is implemeneted
        # NOTE:
        # - Test 33 has no tests for Frontier
        # - test 37, 38 have invalid opcodes that needs to be handled gracefully
    ],
)
def test_transaction_init(test_file: str) -> None:
    run_frontier_blockchain_st_tests(test_file)


# TODO: Run the below test cases once CALL opcode has been implemented.
# @pytest.mark.parametrize(
#     "test_file",
#     list(os.listdir(os.path.join(TEST_DIR, "stLogTests")))
# )
# def test_log_operations(test_file: str) -> None:
#     print(test_file)
#     run_frontier_blockchain_st_tests(f"stLogTests/{test_file}")
#     assert 1 == 0
