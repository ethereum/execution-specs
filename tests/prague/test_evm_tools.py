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
    run_evm_tools_test(test_case)
