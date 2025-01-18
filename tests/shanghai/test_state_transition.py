from functools import partial
from typing import Dict

import pytest

from tests.helpers import TEST_FIXTURES
from tests.helpers.load_state_tests import (
    Load,
    fetch_state_test_files,
    idfn,
    run_blockchain_st_test,
)

fetch_shanghai_tests = partial(fetch_state_test_files, network="Shanghai")

FIXTURES_LOADER = Load("Shanghai", "shanghai")

run_shanghai_blockchain_st_tests = partial(
    run_blockchain_st_test, load=FIXTURES_LOADER
)

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]
ETHEREUM_SPEC_TESTS_PATH = TEST_FIXTURES["execution_spec_tests"][
    "fixture_path"
]


# Run state tests
test_dir = f"{ETHEREUM_TESTS_PATH}/LegacyTests/Cancun/BlockchainTests/"

SLOW_TESTS = (
    # GeneralStateTests
    "stTimeConsuming/CALLBlake2f_MaxRounds.json",
    "stTimeConsuming/static_Call50000_sha256.json",
    "vmPerformance/loopExp.json",
    "vmPerformance/loopMul.json",
    "QuadraticComplexitySolidity_CallDataCopy_d0g1v0_Shanghai",
    "CALLBlake2f_d9g0v0_Shanghai",
    "CALLCODEBlake2f_d9g0v0",
    # GeneralStateTests
    "stRandom/randomStatetest177.json",
    "stCreateTest/CreateOOGafterMaxCodesize.json",
    # ValidBlockTest
    "bcExploitTest/DelegateCallSpam.json",
    # InvalidBlockTest
    "bcUncleHeaderValidity/nonceWrong.json",
    "bcUncleHeaderValidity/wrongMixHash.json",
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
    "GasLimitHigherThan2p63m1_Shanghai",
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
    fetch_shanghai_tests,
    test_dir,
    ignore_list=IGNORE_TESTS,
    slow_list=SLOW_TESTS,
    big_memory_list=BIG_MEMORY_TESTS,
)


@pytest.mark.parametrize(
    "test_case",
    fetch_state_tests(),
    ids=idfn,
)
def test_general_state_tests(test_case: Dict) -> None:
    run_shanghai_blockchain_st_tests(test_case)


# Run execution-spec-generated-tests
test_dir = f"{ETHEREUM_SPEC_TESTS_PATH}/fixtures/withdrawals"


@pytest.mark.parametrize(
    "test_case",
    fetch_shanghai_tests(test_dir),
    ids=idfn,
)
def test_execution_specs_generated_tests(test_case: Dict) -> None:
    run_shanghai_blockchain_st_tests(test_case)
