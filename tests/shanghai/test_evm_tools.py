import importlib
from functools import partial
from typing import Dict

import pytest

from tests.helpers.load_evm_tools_tests import idfn, load_evm_tools_test

FORK_NAME = "Shanghai"
FORK_PACKAGE = "shanghai"

fetch_general_state_tests = importlib.import_module(
    f"tests.{FORK_PACKAGE}.test_state_transition"
).fetch_general_state_tests  # type: ignore

run_evm_tools_test = partial(load_evm_tools_test, fork_name=FORK_NAME)


@pytest.mark.evm_tools
@pytest.mark.parametrize(
    "test_case",
    fetch_general_state_tests(),
    ids=idfn,
)
def test_evm_tools(test_case: Dict) -> None:
    run_evm_tools_test(test_case)
