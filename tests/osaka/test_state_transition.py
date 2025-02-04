from functools import partial
from typing import Dict, Generator, Tuple

import pytest

from tests.helpers import TEST_FIXTURES
from tests.helpers.load_state_tests import (
    Load,
    fetch_state_test_files,
    idfn,
    run_blockchain_st_test,
)

fetch_osaka_tests = partial(fetch_state_test_files, network="Osaka")

FIXTURES_LOADER = Load("Osaka", "osaka")

run_osaka_blockchain_st_tests = partial(
    run_blockchain_st_test, load=FIXTURES_LOADER
)

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]
ETHEREUM_SPEC_TESTS_PATH = TEST_FIXTURES["execution_spec_tests"][
    "fixture_path"
]


# Run state tests
test_dir = f"{ETHEREUM_TESTS_PATH}/BlockchainTests/"

SLOW_TESTS = (
    # GeneralStateTests
    "stTimeConsuming/CALLBlake2f_MaxRounds.json",
    "stTimeConsuming/static_Call50000_sha256.json",
    "vmPerformance/loopExp.json",
    "vmPerformance/loopMul.json",
    "QuadraticComplexitySolidity_CallDataCopy_d0g1v0_Osaka",
    "CALLBlake2f_d9g0v0_Osaka",
    "CALLCODEBlake2f_d9g0v0",
    # GeneralStateTests
    "stRandom/randomStatetest177.json",
    "stCreateTest/CreateOOGafterMaxCodesize.json",
    # ValidBlockTest
    "bcExploitTest/DelegateCallSpam.json",
    # InvalidBlockTest
    "bcUncleHeaderValidity/nonceWrong.json",
    "bcUncleHeaderValidity/wrongMixHash.json",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py\\:\\:test_valid\\[fork_Osaka-blockchain_test-bls_pairing_non-degeneracy-\\]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py\\:\\:test_valid\\[fork_Osaka-blockchain_test-bls_pairing_bilinearity-\\]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py\\:\\:test_valid\\[fork_Osaka-blockchain_test-bls_pairing_e\\(G1,-G2\\)=e\\(-G1,G2\\)-\\]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py\\:\\:test_valid\\[fork_Osaka-blockchain_test-bls_pairing_e\\(aG1,bG2\\)=e\\(abG1,G2\\)-\\]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py\\:\\:test_valid\\[fork_Osaka-blockchain_test-bls_pairing_e\\(aG1,bG2\\)=e\\(G1,abG2\\)-\\]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py\\:\\:test_valid\\[fork_Osaka-blockchain_test-inf_pair-\\]",
    "tests/osaka/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py\\:\\:test_valid\\[fork_Osaka-blockchain_test-multi_inf_pair-\\]",
    "tests/osaka/eip2935_historical_block_hashes_from_state/test_block_hashes\\.py\\:\\:test_block_hashes_history\\[fork_Osaka-blockchain_test-full_history_plus_one_check_blockhash_first\\]",
)

# These are tests that are considered to be incorrect,
# Please provide an explanation when adding entries
IGNORE_TESTS = (
    # ValidBlockTest
    "bcForkStressTest/ForkStressTest.json",
    "bcGasPricerTest/RPC_API_Test.json",
    "bcMultiChainTest",
    "bcTotalDifficultyTest",
    # InvalidBlockTest
    "bcForgedTest",
    "bcMultiChainTest",
    "GasLimitHigherThan2p63m1_Osaka",
)

# All tests that recursively create a large number of frames (50000)
BIG_MEMORY_TESTS = (
    # GeneralStateTests
    "50000_",
    "/stQuadraticComplexityTest/",
    "/stRandom2/",
    "/stRandom/",
    "/stSpecialTest/",
    "stTimeConsuming/",
    "stBadOpcode/",
    "stStaticCall/",
)

fetch_state_tests = partial(
    fetch_osaka_tests,
    ignore_list=IGNORE_TESTS,
    slow_list=SLOW_TESTS,
    big_memory_list=BIG_MEMORY_TESTS,
)


# Run temporary test fixtures for Osaka
test_dirs = (
    "tests/fixtures/latest_fork_tests/osaka/eof/blockchain_tests/eip7692_eof_v1",
)


def fetch_temporary_tests(test_dirs: Tuple[str, ...]) -> Generator:
    """
    Fetch the relevant tests for a particular EIP-Implementation
    from among the temporary fixtures from ethereum-spec-tests.
    """
    for test_dir in test_dirs:
        yield from fetch_state_tests(test_dir)


@pytest.mark.parametrize(
    "test_case",
    fetch_temporary_tests(test_dirs),
    ids=idfn,
)
def test_execution_specs_generated_tests(test_case: Dict) -> None:
    run_osaka_blockchain_st_tests(test_case)
