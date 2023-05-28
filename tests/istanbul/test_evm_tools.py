import importlib
from functools import partial
from typing import Dict

import pytest

from tests.helpers.load_evm_tools_tests import idfn, load_evm_tools_test

FORK_NAME = "Istanbul"
FORK_PACKAGE = "istanbul"

block_reward = importlib.import_module(
    f"ethereum.{FORK_PACKAGE}.fork"
).BLOCK_REWARD  # type: ignore
fetch_state_tests = importlib.import_module(
    f"tests.{FORK_PACKAGE}.test_state_transition"
).fetch_state_tests  # type: ignore

run_evm_tools_test = partial(
    load_evm_tools_test, fork_name=FORK_NAME, block_reward=block_reward
)


@pytest.mark.evm_tools
@pytest.mark.parametrize(
    "test_case",
    fetch_state_tests(),
    ids=idfn,
)
def test_evm_tools(test_case: Dict) -> None:
    run_evm_tools_test(test_case)
