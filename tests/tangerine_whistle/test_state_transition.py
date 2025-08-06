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

ETHEREUM_BLOCKCHAIN_TESTS_DIR = (
    f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/BlockchainTests/"
)
EEST_BLOCKCHAIN_TESTS_DIR = f"{EEST_TESTS_PATH}/blockchain_tests/"
NETWORK = "EIP150"
PACKAGE = "tangerine_whistle"

LEGACY_SLOW_TESTS = (
    "stRandom/randomStatetest177.json",
    "stCreateTest/CreateOOGafterMaxCodesize.json",
    # ValidBlockTest
    "bcExploitTest/DelegateCallSpam.json",
    # InvalidBlockTest
    "bcUncleHeaderValidity/nonceWrong.json",
    "bcUncleHeaderValidity/wrongMixHash.json",
)

LEGACY_BIG_MEMORY_TESTS = (
    # GeneralStateTests
    "/stQuadraticComplexityTest/",
    "/stRandom2/",
    "/stRandom/",
    "/stSpecialTest/",
    "stTimeConsuming/",
)

LEGACY_IGNORE_LIST = (
    # ValidBlockTests
    "bcForkStressTest/ForkStressTest.json",
    "bcGasPricerTest/RPC_API_Test.json",
    "bcMultiChainTest",
    "bcTotalDifficultyTest",
    # InvalidBlockTests
    "bcForgedTest",
    "bcMultiChainTest",
    "GasLimitHigherThan2p63m1_EIP150",
)

# angry mutant cases are tests that cannot be run for mutation testing
ANGRY_MUTANT_CASES = (
    "Callcode1024OOG",
    "Call1024OOG",
    "CallRecursiveBombPreCall",
    "CallRecursiveBomb1",
    "ABAcalls2",
    "CallRecursiveBombLog2",
    "CallRecursiveBomb0",
    "ABAcalls1",
    "CallRecursiveBomb2",
    "CallRecursiveBombLog"
)

# Define Tests
fetch_tests = partial(
    fetch_state_test_files,
    network=NETWORK,
    ignore_list=LEGACY_IGNORE_LIST,
    slow_list=LEGACY_SLOW_TESTS,
    big_memory_list=LEGACY_BIG_MEMORY_TESTS,
)

FIXTURES_LOADER = Load(NETWORK, PACKAGE)

run_tests = partial(run_blockchain_st_test, load=FIXTURES_LOADER)


def is_angry_mutant(test_case):
    return any(case in str(test_case) for case in ANGRY_MUTANT_CASES)


# Run tests from ethereum/tests
ethereum_blockchain_test_cases = [
    pytest.param(tc, marks=pytest.mark.angry_mutant)
    if is_angry_mutant(tc)
    else tc
    for tc in fetch_tests(ETHEREUM_BLOCKCHAIN_TESTS_DIR)
]


# Run tests from ethereum/tests
@pytest.mark.parametrize(
    "test_case",
    ethereum_blockchain_test_cases,
    ids=idfn,
)
def test_ethereum_tests(test_case: Dict) -> None:
    run_tests(test_case)


eest_test_cases = list(fetch_tests(EEST_BLOCKCHAIN_TESTS_DIR))


# Run EEST test fixtures
@pytest.mark.parametrize(
    "test_case",
    eest_test_cases,
    ids=idfn,
)
def test_eest_tests(test_case: Dict) -> None:
    run_tests(test_case)
