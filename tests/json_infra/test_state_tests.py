from typing import Callable, Dict

import pytest

from . import FORKS
from .helpers.load_state_tests import fetch_state_tests, idfn, run_state_test


def _generate_test_function(fork_name: str) -> Callable:
    @pytest.mark.fork(fork_name)
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


for fork_name in FORKS.keys():
    locals()[
        f"test_state_tests_{fork_name.lower()}"
    ] = _generate_test_function(fork_name)
