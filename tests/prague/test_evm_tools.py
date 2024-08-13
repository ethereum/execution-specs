from functools import partial
from typing import Dict, Generator, Tuple

import pytest

from tests.helpers import TEST_FIXTURES
from tests.helpers.load_evm_tools_tests import (
    fetch_evm_tools_tests,
    idfn,
    load_evm_tools_test,
)

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]
TEST_DIR = "tests/fixtures/latest_fork_tests/state_tests/"
FORK_NAME = "Prague"

run_evm_tools_test = partial(
    load_evm_tools_test,
    fork_name=FORK_NAME,
)

SLOW_TESTS = (
    "CALLBlake2f_MaxRounds",
    "CALLCODEBlake2f",
    "CALLBlake2f",
    "loopExp",
    "loopMul",
    "tests/prague/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Prague-state_test-bls_pairing_non-degeneracy-]",
    "tests/prague/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Prague-state_test-bls_pairing_bilinearity-]",
    "tests/prague/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Prague-state_test-bls_pairing_e(G1,-G2)=e(-G1,G2)-]",
    "tests/prague/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Prague-state_test-bls_pairing_e(aG1,bG2)=e(abG1,G2)-]",
    "tests/prague/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Prague-state_test-bls_pairing_e(aG1,bG2)=e(G1,abG2)-]",
    "tests/prague/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Prague-state_test-inf_pair-]",
    "tests/prague/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Prague-state_test-multi_inf_pair-]",
)

test_dirs = (
    "tests/fixtures/latest_fork_tests/state_tests/prague/eip2537_bls_12_381_precompiles",
    "tests/fixtures/latest_fork_tests/state_tests/prague/eip7702_set_code_tx",
)

IGNORE_TESTS = (
    # TODO: In there current verion of the test fixtures, the following tests are incorrectly filled.
    # Hence, they will be ignored for now. This condition will be removed once the test fixtures are updated.
    "tests/prague/eip7702_set_code_tx/test_set_code_txs.py::test_invalid_tx_invalid_auth_signature[fork_Prague-state_test-v_2,r_1,s_1]",
    "tests/prague/eip7702_set_code_tx/test_set_code_txs.py::test_invalid_tx_invalid_auth_signature[fork_Prague-state_test-v_0,r_1,s_SECP256K1N_OVER_2+1]",
    "tests/prague/eip7702_set_code_tx/test_set_code_txs.py::test_invalid_tx_invalid_auth_signature[fork_Prague-state_test-v_2**256-1,r_1,s_1]",
    "tests/prague/eip7702_set_code_tx/test_set_code_txs.py::test_invalid_tx_invalid_auth_signature[fork_Prague-state_test-v_0,r_1,s_2**256-1]",
)


def fetch_temporary_tests(test_dirs: Tuple[str, ...]) -> Generator:
    for test_dir in test_dirs:
        yield from fetch_evm_tools_tests(
            test_dir,
            FORK_NAME,
            SLOW_TESTS,
        )


@pytest.mark.evm_tools
@pytest.mark.parametrize(
    "test_case",
    fetch_temporary_tests(test_dirs),
    ids=idfn,
)
def test_evm_tools(test_case: Dict) -> None:
    if test_case["test_key"] in IGNORE_TESTS:
        pytest.skip("Test is ignored")
    run_evm_tools_test(test_case)
