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
TEST_DIR = f"{ETHEREUM_TESTS_PATH}/GeneralStateTests/"
FORK_NAME = "Osaka"

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
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Osaka-state_test-bls_pairing_non-degeneracy-]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Osaka-state_test-bls_pairing_bilinearity-]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Osaka-state_test-bls_pairing_e(G1,-G2)=e(-G1,G2)-]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Osaka-state_test-bls_pairing_e(aG1,bG2)=e(abG1,G2)-]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Osaka-state_test-bls_pairing_e(aG1,bG2)=e(G1,abG2)-]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Osaka-state_test-inf_pair-]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_Osaka-state_test-multi_inf_pair-]",
)


# TODO: All the tests test fixtures have not changed the network name from
# prague to osaka. Hence, we need to run the tests with Prague in some dirs and
# as Osaka in others. This will have to be merged eventually and all the tests
# will be run as Osaka.
test_dirs_prague = (
    "tests/fixtures/latest_fork_tests/osaka/eof/evmone_tests/state_tests/state_transition",
    "tests/fixtures/ethereum_tests/EIPTests/StateTests/stEOF",
)


def fetch_temporary_tests_prague(test_dirs: Tuple[str, ...]) -> Generator:
    for test_dir in test_dirs_prague:
        yield from fetch_evm_tools_tests(
            test_dir,
            "Prague",
            SLOW_TESTS,
        )


test_dirs_osaka = (
    "tests/fixtures/latest_fork_tests/osaka/eof/state_tests/eip7692_eof_v1",
)


def fetch_temporary_tests_osaka(test_dirs: Tuple[str, ...]) -> Generator:
    for test_dir in test_dirs_osaka:
        yield from fetch_evm_tools_tests(
            test_dir,
            "Osaka",
            SLOW_TESTS,
        )


IGNORE_TESTS = (
    # TODO: In there current verion of the test fixtures, the following tests are incorrectly filled.
    # Hence, they will be ignored for now. This condition will be removed once the test fixtures are updated.
    "tests/osaka/eip7702_set_code_tx/test_set_code_txs.py::test_invalid_tx_invalid_auth_signature[fork_Osaka-state_test-v_2,r_1,s_1]",
    "tests/osaka/eip7702_set_code_tx/test_set_code_txs.py::test_invalid_tx_invalid_auth_signature[fork_Osaka-state_test-v_0,r_1,s_SECP256K1N_OVER_2+1]",
    "tests/osaka/eip7702_set_code_tx/test_set_code_txs.py::test_invalid_tx_invalid_auth_signature[fork_Osaka-state_test-v_2**256-1,r_1,s_1]",
    "tests/osaka/eip7702_set_code_tx/test_set_code_txs.py::test_invalid_tx_invalid_auth_signature[fork_Osaka-state_test-v_0,r_1,s_2**256-1]",
    "tests/fixtures/latest_fork_tests/state_tests/osaka/eip7692_eof_v1",
    "tests/fixtures/ethereum_tests/EIPTests/StateTests/stEOF",
)


@pytest.mark.evm_tools
@pytest.mark.parametrize(
    "test_case",
    fetch_temporary_tests_prague(test_dirs_prague),
    ids=idfn,
)
def test_evm_tools_1(test_case: Dict) -> None:
    if test_case["test_key"] in IGNORE_TESTS:
        pytest.skip("Test is ignored")
    run_evm_tools_test(test_case)


@pytest.mark.evm_tools
@pytest.mark.parametrize(
    "test_case",
    fetch_temporary_tests_osaka(test_dirs_osaka),
    ids=idfn,
)
def test_evm_tools_2(test_case: Dict) -> None:
    if test_case["test_key"] in IGNORE_TESTS:
        pytest.skip("Test is ignored")
    run_evm_tools_test(test_case)
