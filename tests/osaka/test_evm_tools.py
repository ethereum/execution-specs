from functools import partial
from typing import Dict

import pytest

from tests.helpers import ETHEREUM_TESTS_PATH, OSAKA_TEST_PATH
from tests.helpers.load_evm_tools_tests import (
    fetch_evm_tools_tests,
    idfn,
    load_evm_tools_test,
)

ETHEREUM_STATE_TESTS_DIR = f"{ETHEREUM_TESTS_PATH}/GeneralStateTests/"
EEST_STATE_TESTS_DIR = f"{OSAKA_TEST_PATH}/fixtures/state_tests/"
FORK_NAME = "Osaka"


SLOW_TESTS = (
    "GeneralStateTests/stTimeConsuming/CALLBlake2f_MaxRounds.json::CALLBlake2f_MaxRounds-fork_[Cancun-Osaka]-d0g0v0",
    "GeneralStateTests/VMTests/vmPerformance/loopExp.json::loopExp-fork_[Cancun-Osaka]-d[0-14]g0v0",
    "GeneralStateTests/VMTests/vmPerformance/loopMul.json::loopMul-fork_[Cancun-Osaka]-d[0-2]g0v0",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Osaka-state_test-bls_pairing_non-degeneracy-]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Osaka-state_test-bls_pairing_bilinearity-]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Osaka-state_test-bls_pairing_e(G1,-G2)=e(-G1,G2)-]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Osaka-state_test-bls_pairing_e(aG1,bG2)=e(abG1,G2)-]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Osaka-state_test-bls_pairing_e(aG1,bG2)=e(G1,abG2)-]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Osaka-state_test-inf_pair-]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Osaka-state_test-multi_inf_pair-]",
)

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


def is_angry_mutant(test_case):
    return any(case in str(test_case) for case in ANGRY_MUTANT_CASES)


ethereum_state_test_cases = [
    pytest.param(tc, marks=pytest.mark.angry_mutant)
    if is_angry_mutant(tc)
    else tc
    for tc in fetch_tests(ETHEREUM_STATE_TESTS_DIR)
]


# Run tests from ethereum/tests
@pytest.mark.evm_tools
@pytest.mark.parametrize(
    "test_case",
    ethereum_state_test_cases,
    ids=idfn,
)
def test_ethereum_tests_evm_tools(test_case: Dict) -> None:
    run_tests(test_case)


eest_state_test_cases = list(fetch_tests(EEST_STATE_TESTS_DIR))


# Run EEST test fixtures
@pytest.mark.evm_tools
@pytest.mark.parametrize(
    "test_case",
    eest_state_test_cases,
    ids=idfn,
)
def test_eest_evm_tools(test_case: Dict) -> None:
    run_tests(test_case)
