from typing import Callable, Dict

import pytest

from . import FORKS
from .conftest import pytest_config
from .helpers.load_state_tests import fetch_state_tests, idfn, run_state_test


def _generate_test_function(fork_name: str) -> Callable:
    @pytest.mark.evm_tools
    @pytest.mark.json_state_tests
    @pytest.mark.parametrize(
        "state_test_case",
        fetch_state_tests(fork_name),
        ids=idfn,
    )
    def test_func(state_test_case: Dict) -> None:
        run_state_test(state_test_case)

    test_func.__name__ = f"test_state_tests_{fork_name.lower()}"
    return test_func


# Get the fork option from pytest config if available

# Determine which forks to generate tests for
if pytest_config and pytest_config.getoption("fork", None):
    # If --fork option is specified, only generate test for that fork
    fork_option = pytest_config.getoption("fork")
    if fork_option in FORKS:
        forks_to_test = [fork_option]
    else:
        # If specified fork is not valid, generate no tests
        forks_to_test = []
else:
    # If no --fork option, generate tests for all forks
    forks_to_test = list(FORKS.keys())

for fork_name in forks_to_test:
    locals()[
        f"test_state_tests_{fork_name.lower()}"
    ] = _generate_test_function(fork_name)
