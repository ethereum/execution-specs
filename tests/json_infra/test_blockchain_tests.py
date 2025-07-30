from typing import Callable, Dict

import pytest

from . import FORKS
from .conftest import pytest_config
from .helpers.load_blockchain_tests import (
    Load,
    fetch_blockchain_tests,
    idfn,
    run_blockchain_st_test,
)


def _generate_test_function(fork_name: str) -> Callable:
    @pytest.mark.json_blockchain_tests
    @pytest.mark.parametrize(
        "blockchain_test_case",
        fetch_blockchain_tests(fork_name),
        ids=idfn,
    )
    def test_func(blockchain_test_case: Dict) -> None:
        load = Load(
            blockchain_test_case["network"], blockchain_test_case["package"]
        )
        run_blockchain_st_test(blockchain_test_case, load=load)

    test_func.__name__ = f"test_blockchain_tests_{fork_name.lower()}"
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
        f"test_blockchain_tests_{fork_name.lower()}"
    ] = _generate_test_function(fork_name)
