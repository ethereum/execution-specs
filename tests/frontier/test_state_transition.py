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
NETWORK = "Frontier"
PACKAGE = "frontier"

LEGACY_IGNORE_LIST = (
    # Valid block tests to be ignored
    "bcForkStressTest/ForkStressTest.json",
    "bcGasPricerTest/RPC_API_Test.json",
    "bcMultiChainTest/",
    "bcTotalDifficultyTest/",
    "stTimeConsuming/",
    # Invalid block tests to be ignored
    "bcForgedTest",
    "bcMultiChainTest",
    # TODO: See https://github.com/ethereum/tests/issues/1218
    "GasLimitHigherThan2p63m1_Frontier",
)

LEGACY_BIG_MEMORY_TESTS = (
    "/stQuadraticComplexityTest/",
    "/stRandom2/",
    "/stRandom/",
    "/stSpecialTest/",
)

SLOW_LIST = (
    # InvalidBlockTest
    "bcUncleHeaderValidity/nonceWrong.json",
    "bcUncleHeaderValidity/wrongMixHash.json",
)

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
    slow_list=SLOW_LIST,
    big_memory_list=LEGACY_BIG_MEMORY_TESTS,
)

FIXTURES_LOADER = Load(NETWORK, PACKAGE)

run_tests = partial(run_blockchain_st_test, load=FIXTURES_LOADER)


def is_angry_mutant(test_case):
    return any(case in str(test_case) for case in ANGRY_MUTANT_CASES)


# Run tests from ethereum/tests
ethereum_state_test_cases = [
    pytest.param(tc, marks=pytest.mark.angry_mutant)
    if is_angry_mutant(tc)
    else tc
    for tc in fetch_tests(ETHEREUM_BLOCKCHAIN_TESTS_DIR)
]


@pytest.mark.parametrize(
    "test_case",
    ethereum_state_test_cases,
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
