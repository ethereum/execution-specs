import importlib
from functools import partial
from typing import Dict

import pytest

from tests.helpers import TEST_FIXTURES
from tests.helpers.load_evm_tools_tests import (
    fetch_evm_tools_tests,
    idfn,
    load_evm_tools_test,
)

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]
TEST_DIR = f"{ETHEREUM_TESTS_PATH}/GeneralStateTests/"
FORK_NAME = "Cancun"

run_evm_tools_test = partial(
    load_evm_tools_test,
    fork_name=FORK_NAME,
)

SLOW_TESTS = (
    "CALLBlake2f_MaxRounds",
    "CALLCODEBlake2f",
    "CALLBlake2f",
    "loopExp",
    "loopMul",
)


@pytest.mark.evm_tools
@pytest.mark.parametrize(
    "test_case",
    fetch_evm_tools_tests(
        TEST_DIR,
        FORK_NAME,
        SLOW_TESTS,
    ),
    ids=idfn,
)
def test_evm_tools(test_case: Dict) -> None:
    run_evm_tools_test(test_case)
