from typing import Any, Callable, Dict

import pytest

from . import FORKS
from .helpers.load_blockchain_tests import (
    Load,
    fetch_blockchain_tests,
    idfn,
    run_blockchain_st_test,
)

# angry mutant cases are tests that cannot be run for mutation testing
ANGRY_MUTANT_CASES = (
    "Callcode1024OOG",
    "Call1024OOG",
    "CallRecursiveBombPreCall",
    "CallRecursiveBomb1",
    "ABAcalls2",
    "CallRecursiveBombLog2",
    "CallRecursiveBomb0",
    "ABAcalls1",
    "CallRecursiveBomb2",
    "CallRecursiveBombLog",
)


def is_angry_mutant(test_case: Any) -> bool:
    return any(case in str(test_case) for case in ANGRY_MUTANT_CASES)


def get_marked_blockchain_test_cases(fork_name: str) -> list:
    """Get blockchain test cases with angry mutant marking for the given fork."""
    return [
        pytest.param(tc, marks=pytest.mark.angry_mutant)
        if is_angry_mutant(tc)
        else tc
        for tc in fetch_blockchain_tests(fork_name)
    ]


def _generate_test_function(fork_name: str) -> Callable:
    @pytest.mark.fork(fork_name)
    @pytest.mark.json_blockchain_tests
    @pytest.mark.parametrize(
        "blockchain_test_case",
        get_marked_blockchain_test_cases(fork_name),
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
