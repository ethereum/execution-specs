from functools import partial
from typing import Dict

import pytest

from tests.helpers import EEST_TESTS_PATH, ETHEREUM_TESTS_PATH
from tests.helpers.load_evm_tools_tests import (
    fetch_evm_tools_tests,
    idfn,
    load_evm_tools_test,
)

ETHEREUM_STATE_TESTS_DIR = f"{ETHEREUM_TESTS_PATH}/GeneralStateTests/"
EEST_STATE_TESTS_DIR = f"{EEST_TESTS_PATH}/state_tests/"
FORK_NAME = "Osaka"


SLOW_TESTS = (
    "CALLBlake2f_MaxRounds",
    "CALLCODEBlake2f",
    "CALLBlake2f",
    "loopExp",
    "loopMul",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Prague-state_test-bls_pairing_non-degeneracy-]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Prague-state_test-bls_pairing_bilinearity-]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Prague-state_test-bls_pairing_e(G1,-G2)=e(-G1,G2)-]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Prague-state_test-bls_pairing_e(aG1,bG2)=e(abG1,G2)-]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Prague-state_test-bls_pairing_e(aG1,bG2)=e(G1,abG2)-]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Prague-state_test-inf_pair-]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Prague-state_test-multi_inf_pair-]",
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


# Run tests from ethereum/tests
@pytest.mark.evm_tools
@pytest.mark.parametrize(
    "test_case",
    fetch_tests(ETHEREUM_STATE_TESTS_DIR),
    ids=idfn,
)
def test_ethereum_tests_evm_tools(test_case: Dict) -> None:
    run_tests(test_case)


# Run EEST test fixtures
@pytest.mark.evm_tools
@pytest.mark.parametrize(
    "test_case",
    fetch_tests(EEST_STATE_TESTS_DIR),
    ids=idfn,
)
def test_eest_evm_tools(test_case: Dict) -> None:
    run_tests(test_case)
