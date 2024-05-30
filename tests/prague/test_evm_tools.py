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
)

test_dirs = (
    "tests/fixtures/latest_fork_tests/fixtures/state_tests/prague/eip2537_bls_12_381_precompiles/bls12_g1add",
    "tests/fixtures/latest_fork_tests/fixtures/state_tests/prague/eip2537_bls_12_381_precompiles/bls12_g1mul",
    "tests/fixtures/latest_fork_tests/fixtures/state_tests/prague/eip2537_bls_12_381_precompiles/bls12_g1msm",
    "tests/fixtures/latest_fork_tests/fixtures/state_tests/prague/eip2537_bls_12_381_precompiles/bls12_g2add",
    "tests/fixtures/latest_fork_tests/fixtures/state_tests/prague/eip2537_bls_12_381_precompiles/bls12_g2mul",
    "tests/fixtures/latest_fork_tests/fixtures/state_tests/prague/eip2537_bls_12_381_precompiles/bls12_g2msm",
    "tests/fixtures/latest_fork_tests/fixtures/state_tests/prague/eip2537_bls_12_381_precompiles/bls12_pairing",
    "tests/fixtures/latest_fork_tests/fixtures/state_tests/prague/eip2537_bls_12_381_precompiles/bls12_map_fp2_to_g2",
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
