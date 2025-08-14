from typing import Callable, Dict

import pytest

from . import FORKS
from .helpers.load_blockchain_tests import (
    Load,
    fetch_blockchain_tests,
    idfn,
    run_blockchain_st_test,
)


def _generate_test_function(fork_name: str) -> Callable:
    @pytest.mark.fork(fork_name)
    @pytest.mark.json_blockchain_tests
    @pytest.mark.parametrize(
        "blockchain_test_case",
        fetch_blockchain_tests(fork_name),
        ids=idfn,
    )
    def test_func(blockchain_test_case: Dict) -> None:
        load = Load(
            blockchain_test_case["json_fork"],
            blockchain_test_case["eels_fork"],
        )
        run_blockchain_st_test(blockchain_test_case, load=load)

    test_func.__name__ = f"test_blockchain_tests_{fork_name.lower()}"
    return test_func


for fork_name in FORKS.keys():
    locals()[
        f"test_blockchain_tests_{fork_name.lower()}"
    ] = _generate_test_function(fork_name)
