from typing import Any, Callable, Dict

import pytest

from . import FORKS
from .helpers.load_state_tests import fetch_state_tests, idfn, run_state_test

# angry mutant cases are tests that cannot be run for mutation testing
ANGRY_MUTANT_CASES = (
    "Callcode1024OOG",
    "Call1024OOG",
    "CallRecursiveBombPreCall",
    "CallRecursiveBombLog2",
    "CallRecursiveBomb2",
    "ABAcalls1",
    "CallRecursiveBomb0_OOG_atMaxCallDepth",
    "ABAcalls2",
    "CallRecursiveBomb0",
    "CallRecursiveBomb1",
    "CallRecursiveBombLog"
)


def is_angry_mutant(test_case: Any) -> bool:
    return any(case in str(test_case) for case in ANGRY_MUTANT_CASES)


def get_marked_state_test_cases(fork_name: str):
    """Get state test cases with angry mutant marking for the given fork."""
    return [
        pytest.param(tc, marks=pytest.mark.angry_mutant)
        if is_angry_mutant(tc)
        else tc
        for tc in fetch_state_tests(fork_name)
    ]


def _generate_test_function(fork_name: str) -> Callable:
    @pytest.mark.fork(fork_name)
    @pytest.mark.evm_tools
    @pytest.mark.json_state_tests
    @pytest.mark.parametrize(
        "state_test_case",
        get_marked_state_test_cases(fork_name),
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
