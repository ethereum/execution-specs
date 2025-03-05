from functools import partial
from typing import Dict

import pytest

from tests.helpers import EEST_TESTS_PATH, ETHEREUM_TESTS_PATH
from tests.helpers.load_evm_tools_tests import (
    fetch_evm_tools_tests,
    idfn,
    load_evm_tools_test,
)

ETHEREUM_STATE_TESTS_DIR = (
    f"{ETHEREUM_TESTS_PATH}/LegacyTests/Cancun/GeneralStateTests/"
)
EEST_STATE_TESTS_DIR = f"{EEST_TESTS_PATH}/state_tests/"
FORK_NAME = "Berlin"

SLOW_TESTS = (
    "CALLBlake2f_MaxRounds",
    "CALLCODEBlake2f",
    "CALLBlake2f",
    "loopExp",
    "loopMul",
)


# Define tests
fetch_tests = partial(
    fetch_evm_tools_tests,
    fork_name=FORK_NAME,
    slow_tests=SLOW_TESTS,
)

run_tests = partial(
    load_evm_tools_test,
    fork_name=FORK_NAME,
)


# Run tests from ethereum/tests
@pytest.mark.evm_tools
@pytest.mark.parametrize(
    "test_case",
    fetch_tests(ETHEREUM_STATE_TESTS_DIR),
    ids=idfn,
)
def test_ethereum_tests_evm_tools(test_case: Dict) -> None:
    run_tests(test_case)


# Run EEST test fixtures
@pytest.mark.evm_tools
@pytest.mark.parametrize(
    "test_case",
    fetch_tests(EEST_STATE_TESTS_DIR),
    ids=idfn,
)
def test_eest_evm_tools(test_case: Dict) -> None:
    run_tests(test_case)
