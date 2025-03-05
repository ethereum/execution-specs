from functools import partial
from typing import Dict

import pytest

from tests.helpers import EEST_TESTS_PATH, ETHEREUM_TESTS_PATH
from tests.helpers.load_state_tests import (
    Load,
    fetch_state_test_files,
    idfn,
    run_blockchain_st_test,
)

ETHEREUM_BLOCKCHAIN_TESTS_DIR = f"{ETHEREUM_TESTS_PATH}/BlockchainTests/"
EEST_BLOCKCHAIN_TESTS_DIR = f"{EEST_TESTS_PATH}/blockchain_tests/"
NETWORK = "Prague"
PACKAGE = "prague"

SLOW_TESTS = (
    # GeneralStateTests
    "stTimeConsuming/CALLBlake2f_MaxRounds.json",
    "stTimeConsuming/static_Call50000_sha256.json",
    "vmPerformance/loopExp.json",
    "vmPerformance/loopMul.json",
    "QuadraticComplexitySolidity_CallDataCopy_d0g1v0_Prague",
    "CALLBlake2f_d9g0v0_Prague",
    "CALLCODEBlake2f_d9g0v0",
    # GeneralStateTests
    "stRandom/randomStatetest177.json",
    "stCreateTest/CreateOOGafterMaxCodesize.json",
    # ValidBlockTest
    "bcExploitTest/DelegateCallSpam.json",
    # InvalidBlockTest
    "bcUncleHeaderValidity/nonceWrong.json",
    "bcUncleHeaderValidity/wrongMixHash.json",
    "tests/prague/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py\\:\\:test_valid\\[fork_Prague-blockchain_test-bls_pairing_non-degeneracy-\\]",
    "tests/prague/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py\\:\\:test_valid\\[fork_Prague-blockchain_test-bls_pairing_bilinearity-\\]",
    "tests/prague/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py\\:\\:test_valid\\[fork_Prague-blockchain_test-bls_pairing_e\\(G1,-G2\\)=e\\(-G1,G2\\)-\\]",
    "tests/prague/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py\\:\\:test_valid\\[fork_Prague-blockchain_test-bls_pairing_e\\(aG1,bG2\\)=e\\(abG1,G2\\)-\\]",
    "tests/prague/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py\\:\\:test_valid\\[fork_Prague-blockchain_test-bls_pairing_e\\(aG1,bG2\\)=e\\(G1,abG2\\)-\\]",
    "tests/prague/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py\\:\\:test_valid\\[fork_Prague-blockchain_test-inf_pair-\\]",
    "tests/prague/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py\\:\\:test_valid\\[fork_Prague-blockchain_test-multi_inf_pair-\\]",
    "tests/prague/eip2935_historical_block_hashes_from_state/test_block_hashes\\.py\\:\\:test_block_hashes_history\\[fork_Prague-blockchain_test-full_history_plus_one_check_blockhash_first\\]",
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
    "GasLimitHigherThan2p63m1_Prague",
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

# Define Tests
fetch_tests = partial(
    fetch_state_test_files,
    network=NETWORK,
    ignore_list=IGNORE_TESTS,
    slow_list=SLOW_TESTS,
    big_memory_list=BIG_MEMORY_TESTS,
)

FIXTURES_LOADER = Load(NETWORK, PACKAGE)

run_tests = partial(run_blockchain_st_test, load=FIXTURES_LOADER)


# Run tests from ethereum/tests
@pytest.mark.parametrize(
    "test_case",
    fetch_tests(ETHEREUM_BLOCKCHAIN_TESTS_DIR),
    ids=idfn,
)
def test_ethereum_tests(test_case: Dict) -> None:
    run_tests(test_case)


# Run EEST test fixtures
@pytest.mark.parametrize(
    "test_case",
    fetch_tests(EEST_BLOCKCHAIN_TESTS_DIR),
    ids=idfn,
)
def test_eest_tests(test_case: Dict) -> None:
    run_tests(test_case)
